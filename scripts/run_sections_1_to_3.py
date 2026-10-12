#!/usr/bin/env python3
"""Reproduce methodology Sections 1-3 with a fixed ASTRA-sim experiment.

Run this script inside the project Docker container. It generates Chakra
execution traces, invokes the congestion-aware analytical backend, validates
all simulated endpoints, and writes per-job and per-scenario summaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable


PINNED_ASTRA_COMMIT = "4ce9ecfe746a3ee5fe47559a11d91644d641fa7f"
FINISH_PATTERN = re.compile(r"sys\[(\d+)\] finished, (\d+) cycles")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the fixed Sections 1-3 ASTRA-sim tutorial experiment."
    )
    parser.add_argument("--astra", type=Path, required=True, help="ASTRA-sim checkout")
    parser.add_argument(
        "--output", type=Path, default=Path("results/sections-1-3"),
        help="result directory (default: results/sections-1-3)",
    )
    parser.add_argument(
        "--sections", default="1,2,3",
        help="comma-separated sections to run; Section 3 always includes the Section 2 baseline",
    )
    parser.add_argument(
        "--config", type=Path, default=Path("configs/sections-1-3"),
        help="directory containing the fixed experiment inputs",
    )
    return parser.parse_args()


def build_groups(maximum_jobs: int, gpus_per_job: int, topology_npus: int) -> dict[str, list[int]]:
    """Return disjoint, strided communicator groups with nonzero group IDs."""
    if maximum_jobs * gpus_per_job != topology_npus:
        raise ValueError("maximum_jobs * gpus_per_job must equal topology_npus")
    groups = {
        str(job + 1): [job + slot * maximum_jobs for slot in range(gpus_per_job)]
        for job in range(maximum_jobs)
    }
    ranks = [rank for members in groups.values() for rank in members]
    if sorted(ranks) != list(range(topology_npus)):
        raise ValueError("communicator groups must cover every rank exactly once")
    return groups


def selected_sections(raw: str) -> set[int]:
    try:
        sections = {int(part.strip()) for part in raw.split(",") if part.strip()}
    except ValueError as exc:
        raise ValueError("--sections must contain only 1, 2, and 3") from exc
    if not sections or not sections.issubset({1, 2, 3}):
        raise ValueError("--sections must contain only 1, 2, and 3")
    return sections


def build_scenarios(config: dict, sections: set[int]) -> list[dict]:
    scenarios: list[dict] = []
    if 1 in sections:
        scenarios.append({
            "section": 1,
            "name": "section1_one_iteration",
            "job_count": 1,
            "iterations": config["section_1_iterations"],
        })
    if 2 in sections or 3 in sections:
        scenarios.append({
            "section": 2,
            "name": "section2_single_job_baseline",
            "job_count": 1,
            "iterations": config["sections_2_and_3_iterations"],
        })
    if 3 in sections:
        for job_count in config["job_counts"]:
            if job_count == 1:
                continue
            scenarios.append({
                "section": 3,
                "name": f"section3_{job_count:02d}_jobs",
                "job_count": job_count,
                "iterations": config["sections_2_and_3_iterations"],
            })
    return scenarios


def validate_fixed_inputs(config: dict, config_dir: Path) -> None:
    network_text = (config_dir / "network_64npu_ring.yml").read_text()
    expected_network_values = {
        "npus_count": config["topology_npus"],
        "bandwidth": config["bandwidth_GBps"],
        "latency": config["latency_ns"],
    }
    for key, expected in expected_network_values.items():
        match = re.search(rf"^{key}:\s*\[\s*([0-9.]+)\s*\]", network_text, re.MULTILINE)
        if not match or float(match.group(1)) != float(expected):
            raise ValueError(f"{key} in network_64npu_ring.yml must equal {expected}")
    if not re.search(r"^topology:\s*\[\s*Ring\s*\]", network_text, re.MULTILINE):
        raise ValueError("network_64npu_ring.yml must use the Ring topology")

    system = json.loads((config_dir / "system_ring.json").read_text())
    if system.get("all-reduce-implementation") != ["ring"]:
        raise ValueError("system_ring.json must select Ring AllReduce")
    if system.get("active-chunks-per-dimension") != 4:
        raise ValueError("system_ring.json must use four active chunks per dimension")


def nearest_rank_percentile(values: Iterable[float], percentile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate a percentile of an empty sequence")
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def jain_fairness(values: Iterable[float]) -> float:
    samples = list(values)
    if not samples or any(value < 0 for value in samples):
        raise ValueError("fairness requires one or more nonnegative values")
    denominator = len(samples) * sum(value * value for value in samples)
    return 1.0 if denominator == 0 else (sum(samples) ** 2) / denominator


def load_chakra(astra: Path):
    sys.path.insert(0, str(astra))
    from extern.graph_frontend.chakra.schema.protobuf.et_def_pb2 import (  # type: ignore
        ALL_REDUCE,
        COMM_COLL_NODE,
        COMP_NODE,
        AttributeProto,
        GlobalMetadata,
        Node,
    )
    from extern.graph_frontend.chakra.src.third_party.utils.protolib import (  # type: ignore
        encodeMessage,
    )
    return {
        "ALL_REDUCE": ALL_REDUCE,
        "COMM_COLL_NODE": COMM_COLL_NODE,
        "COMP_NODE": COMP_NODE,
        "AttributeProto": AttributeProto,
        "GlobalMetadata": GlobalMetadata,
        "Node": Node,
        "encodeMessage": encodeMessage,
    }


def write_traces(
    case_dir: Path,
    topology_npus: int,
    groups: dict[str, list[int]],
    active_group_ids: list[str],
    iterations: int,
    compute_us: int,
    message_bytes: int,
    chakra: dict,
) -> None:
    rank_to_group = {
        rank: group_id for group_id, members in groups.items() for rank in members
    }
    active = set(active_group_ids)
    for rank in range(topology_npus):
        group_id = rank_to_group[rank]
        path = case_dir / f"workload.{rank}.et"
        with path.open("wb") as stream:
            chakra["encodeMessage"](stream, chakra["GlobalMetadata"](version="0.0.4"))
            previous_id: int | None = None
            node_id = 0

            def emit(node_type: int, name: str, duration_us: int = 0, collective: bool = False) -> None:
                nonlocal previous_id, node_id
                node = chakra["Node"](
                    id=node_id,
                    name=name,
                    type=node_type,
                    duration_micros=duration_us,
                )
                if previous_id is not None:
                    node.data_deps.append(previous_id)
                node.attr.append(chakra["AttributeProto"](name="is_cpu_op", bool_val=False))
                if collective:
                    node.attr.extend([
                        chakra["AttributeProto"](
                            name="comm_type", int64_val=chakra["ALL_REDUCE"]
                        ),
                        chakra["AttributeProto"](
                            name="comm_size", int64_val=message_bytes
                        ),
                        chakra["AttributeProto"](
                            name="pg_name", string_val=group_id
                        ),
                    ])
                chakra["encodeMessage"](stream, node)
                previous_id = node_id
                node_id += 1

            if group_id not in active:
                emit(chakra["COMP_NODE"], "inactive_endpoint", duration_us=1)
                continue

            for iteration in range(iterations):
                emit(
                    chakra["COMP_NODE"],
                    f"job_{group_id}_compute_{iteration}",
                    duration_us=compute_us,
                )
                emit(
                    chakra["COMM_COLL_NODE"],
                    f"job_{group_id}_allreduce_{iteration}",
                    collective=True,
                )
            emit(
                chakra["COMP_NODE"],
                f"job_{group_id}_final_compute",
                duration_us=compute_us,
            )


def run_case(
    scenario: dict,
    config: dict,
    groups: dict[str, list[int]],
    astra: Path,
    config_dir: Path,
    output_dir: Path,
    chakra: dict,
) -> list[dict]:
    case_dir = output_dir / scenario["name"]
    case_dir.mkdir(parents=True, exist_ok=True)
    active_group_ids = [str(index) for index in range(1, scenario["job_count"] + 1)]
    write_traces(
        case_dir=case_dir,
        topology_npus=config["topology_npus"],
        groups=groups,
        active_group_ids=active_group_ids,
        iterations=scenario["iterations"],
        compute_us=config["compute_phase_us"],
        message_bytes=config["message_bytes_per_rank"],
        chakra=chakra,
    )

    (case_dir / "groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    description = {
        **scenario,
        "active_group_ids": active_group_ids,
        "topology_npus": config["topology_npus"],
        "gpus_per_job": config["gpus_per_job"],
        "compute_phase_us": config["compute_phase_us"],
        "message_bytes_per_rank": config["message_bytes_per_rank"],
        "job_arrival_ns": config["all_jobs_arrive_at_ns"],
        "placement": config["placement"],
        "trace_pattern": "(compute -> AllReduce) repeated N times -> final compute",
    }
    (case_dir / "description.json").write_text(json.dumps(description, indent=2) + "\n")
    shutil.copy2(config_dir / "network_64npu_ring.yml", case_dir / "network.yml")
    shutil.copy2(config_dir / "system_ring.json", case_dir / "system.json")

    binary = astra / "build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Aware"
    if not binary.is_file():
        raise FileNotFoundError(
            f"missing {binary}; run ./build/astra_analytical/build.sh inside Docker first"
        )
    remote_memory = Path(__file__).resolve().parents[1] / "configs/no_memory_expansion.json"
    command = [
        str(binary),
        f"--workload-configuration={case_dir}/workload",
        f"--comm-group-configuration={case_dir}/groups.json",
        f"--system-configuration={case_dir}/system.json",
        f"--remote-memory-configuration={remote_memory}",
        f"--network-configuration={case_dir}/network.yml",
        f"--logging-folder={case_dir}/logging",
    ]
    (case_dir / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    result = subprocess.run(
        command,
        cwd=astra,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=180,
        env={**os.environ, "CS4251_POLICY": "immediate"},
    )
    (case_dir / "run.log").write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(
            f"{scenario['name']} failed with exit code {result.returncode}; "
            f"inspect {case_dir / 'run.log'}"
        )

    completion_by_rank = {
        int(rank): int(cycles) for rank, cycles in FINISH_PATTERN.findall(result.stdout)
    }
    expected_ranks = set(range(config["topology_npus"]))
    if set(completion_by_rank) != expected_ranks:
        missing = sorted(expected_ranks - set(completion_by_rank))
        raise RuntimeError(
            f"{scenario['name']} completed {len(completion_by_rank)} of "
            f"{config['topology_npus']} ranks; missing {missing}"
        )

    compute_total_us = (scenario["iterations"] + 1) * config["compute_phase_us"]
    rows = []
    for group_id in active_group_ids:
        completion_ns = max(completion_by_rank[rank] for rank in groups[group_id])
        completion_us = completion_ns / 1000.0
        communication_and_wait_us = completion_us - compute_total_us
        rows.append({
            "section": scenario["section"],
            "case": scenario["name"],
            "job_count": scenario["job_count"],
            "job_id": int(group_id),
            "gpus_per_job": config["gpus_per_job"],
            "iterations": scenario["iterations"],
            "message_bytes_per_rank": config["message_bytes_per_rank"],
            "compute_total_us": compute_total_us,
            "completion_ns": completion_ns,
            "jct_us": completion_us,
            "communication_and_wait_us": round(communication_and_wait_us, 6),
            "mean_allreduce_and_wait_us": round(
                communication_and_wait_us / scenario["iterations"], 6
            ),
            "mean_iteration_us": round(
                (completion_us - config["compute_phase_us"])
                / scenario["iterations"],
                6,
            ),
        })
    print(
        f"{scenario['name']}: {scenario['job_count']} active job(s), "
        f"{config['topology_npus']} of {config['topology_npus']} ranks completed",
        flush=True,
    )
    return rows


def add_slowdown_and_summarize(rows: list[dict]) -> list[dict]:
    baseline_rows = [row for row in rows if row["case"] == "section2_single_job_baseline"]
    if not baseline_rows:
        for row in rows:
            row["slowdown_vs_single_job"] = ""
        return []
    baseline_us = baseline_rows[0]["jct_us"]
    for row in rows:
        row["slowdown_vs_single_job"] = (
            round(row["jct_us"] / baseline_us, 6) if row["section"] in (2, 3) else ""
        )

    summaries = []
    for job_count in sorted({row["job_count"] for row in rows if row["section"] in (2, 3)}):
        matching = [
            row for row in rows
            if row["job_count"] == job_count and row["section"] in (2, 3)
        ]
        jcts = [row["jct_us"] for row in matching]
        slowdowns = [row["slowdown_vs_single_job"] for row in matching]
        completion_rates = [1.0 / value for value in jcts]
        summaries.append({
            "job_count": job_count,
            "mean_jct_us": round(sum(jcts) / len(jcts), 6),
            "p95_jct_us": round(nearest_rank_percentile(jcts, 0.95), 6),
            "makespan_us": round(max(jcts), 6),
            "mean_slowdown": round(sum(slowdowns) / len(slowdowns), 6),
            "max_slowdown": round(max(slowdowns), 6),
            "jain_fairness_completion_rate": round(jain_fairness(completion_rates), 6),
        })
    return summaries


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_svg(path: Path, summaries: list[dict]) -> None:
    width, height = 820, 460
    left, top, plot_width, plot_height = 80, 45, 680, 330
    maximum = max(row["mean_slowdown"] for row in summaries)
    y_max = max(1.25, math.ceil(maximum * 4) / 4)
    points = []
    for index, row in enumerate(summaries):
        x = left + (plot_width * index / max(1, len(summaries) - 1))
        y = top + plot_height * (1 - row["mean_slowdown"] / y_max)
        points.append((x, y, row))
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="820" height="460" viewBox="0 0 820 460">',
        '<rect width="820" height="460" fill="white"/>',
        '<text x="410" y="26" text-anchor="middle" font-family="sans-serif" font-size="18" font-weight="bold">Contention slowdown versus concurrent jobs</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#333"/>',
    ]
    for tick in range(5):
        value = y_max * tick / 4
        y = top + plot_height * (1 - value / y_max)
        lines.extend([
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#ddd"/>',
            f'<text x="{left - 10}" y="{y + 5:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{value:.2f}x</text>',
        ])
    if len(points) > 1:
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
        lines.append(f'<polyline points="{point_string}" fill="none" stroke="#0969da" stroke-width="3"/>')
    for x, y, row in points:
        lines.extend([
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#0969da"/>',
            f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" font-family="sans-serif" font-size="12">{row["mean_slowdown"]:.2f}x</text>',
            f'<text x="{x:.1f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="sans-serif" font-size="12">{row["job_count"]}</text>',
        ])
    lines.extend([
        f'<text x="{left + plot_width / 2}" y="{height - 22}" text-anchor="middle" font-family="sans-serif" font-size="14">Concurrent jobs</text>',
        f'<text x="20" y="{top + plot_height / 2}" text-anchor="middle" font-family="sans-serif" font-size="14" transform="rotate(-90 20 {top + plot_height / 2})">Mean JCT slowdown</text>',
        '</svg>',
    ])
    path.write_text("\n".join(lines) + "\n")


def write_results_markdown(
    path: Path, config: dict, summaries: list[dict], rows: list[dict]
) -> None:
    section_one = next(row for row in rows if row["case"] == "section1_one_iteration")
    section_two = next(row for row in rows if row["case"] == "section2_single_job_baseline")
    lines = [
        "# Sections 1-3 recorded results",
        "",
        "These values were generated by `scripts/run_sections_1_to_3.py` with the",
        "checked-in fixed inputs. Times are simulated time; they are not Docker wall time.",
        "",
        "## Sections 1 and 2 timing checks",
        "",
        f"The one-iteration trace completed in {section_one['jct_us']:.3f} us: "
        f"{section_one['compute_total_us']} us of configured compute replay plus "
        f"{section_one['communication_and_wait_us']:.3f} us in AllReduce.",
        f"The three-iteration single-job baseline completed in "
        f"{section_two['jct_us']:.3f} us. Its measured timing equals 400 us of "
        f"configured compute replay plus three {section_one['communication_and_wait_us']:.3f}-us "
        "AllReduce phases in this uncontended scenario.",
        "",
        "## Section 3 contention sweep",
        "",
        "| Concurrent jobs | Mean JCT (us) | P95 JCT (us) | Mean slowdown | Max slowdown | Jain fairness |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['job_count']} | {row['mean_jct_us']:.3f} | "
            f"{row['p95_jct_us']:.3f} | {row['mean_slowdown']:.3f}x | "
            f"{row['max_slowdown']:.3f}x | "
            f"{row['jain_fairness_completion_rate']:.4f} |"
        )
    lines.extend([
        "",
        "The fairness column applies Jain's index to reciprocal JCT (a completion-rate",
        "proxy). The analytical backend's ordinary output does not expose measured",
        "per-link utilization. `communication_and_wait_us` in `per_job_summary.csv` is",
        "JCT minus configured compute replay time; it includes collective transfer time",
        "and contention waiting and must not be described as direct link utilization.",
        "",
        f"Configuration: {config['topology_npus']}-NPU Ring, "
        f"{config['gpus_per_job']} GPUs/job, {config['bandwidth_GBps']} GB/s links, "
        f"{config['message_bytes_per_rank']} bytes/rank/AllReduce.",
        f"Simulator commit: `{PINNED_ASTRA_COMMIT}`. The recorded "
        "`astra-sim-status.txt` is empty, so this run used no simulator source changes.",
        "",
        "![Contention slowdown](contention-slowdown.svg)",
    ])
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    astra = args.astra.resolve()
    output_dir = args.output.resolve()
    config_dir = args.config.resolve()
    sections = selected_sections(args.sections)
    config = json.loads((config_dir / "experiment.json").read_text())
    validate_fixed_inputs(config, config_dir)
    groups = build_groups(
        config["maximum_jobs"], config["gpus_per_job"], config["topology_npus"]
    )
    scenarios = build_scenarios(config, sections)
    output_dir.mkdir(parents=True, exist_ok=True)

    astra_commit = subprocess.check_output(
        ["git", "-C", str(astra), "rev-parse", "HEAD"], text=True
    ).strip()
    if astra_commit != PINNED_ASTRA_COMMIT:
        raise RuntimeError(
            f"expected ASTRA-sim {PINNED_ASTRA_COMMIT}, found {astra_commit}"
        )
    (output_dir / "astra-sim-commit.txt").write_text(astra_commit + "\n")
    astra_status = subprocess.check_output(
        ["git", "-C", str(astra), "status", "--short"], text=True
    )
    (output_dir / "astra-sim-status.txt").write_text(astra_status)
    if astra_status:
        print(
            "WARNING: ASTRA-sim has local changes; provenance is recorded in "
            f"{output_dir / 'astra-sim-status.txt'}",
            file=sys.stderr,
        )
    (output_dir / "submodule-commits.txt").write_text(
        subprocess.check_output(
            ["git", "-C", str(astra), "submodule", "status", "--recursive"],
            text=True,
        )
    )
    (output_dir / "groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    (output_dir / "experiment.json").write_text(json.dumps(config, indent=2) + "\n")

    chakra = load_chakra(astra)
    rows: list[dict] = []
    for scenario in scenarios:
        rows.extend(
            run_case(scenario, config, groups, astra, config_dir, output_dir, chakra)
        )
    summaries = add_slowdown_and_summarize(rows)
    write_csv(output_dir / "per_job_summary.csv", rows)
    write_csv(output_dir / "contention_summary.csv", summaries)
    if summaries:
        write_svg(output_dir / "contention-slowdown.svg", summaries)
        write_results_markdown(output_dir / "README.md", config, summaries, rows)
    print(f"Wrote verified results to {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
