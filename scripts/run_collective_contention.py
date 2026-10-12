#!/usr/bin/env python3
"""Generate, run, and summarize the controlled ASTRA-sim experiments.

Run this script inside the project Docker container. It generates Chakra
execution traces, invokes the congestion-aware analytical backend, validates
all simulated endpoints, and writes per-job and per-scenario summaries.

Contention is created through the inputs rather than a special "contention"
API. Multiple independent communicator groups receive identical
compute/AllReduce traces and start at simulated time zero. Their strided rank
placement makes their Ring AllReduces request shared physical Ring links. The
analytical backend models the resulting chunk waiting; this script measures
the resulting increase in job completion time.

This runner does not implement the proposed scheduler. It establishes the
native ready-to-run behavior and the contention evidence needed before policy
comparisons are added.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable


PINNED_ASTRA_COMMIT = "4ce9ecfe746a3ee5fe47559a11d91644d641fa7f"
FINISH_PATTERN = re.compile(r"sys\[(\d+)\] finished, (\d+) cycles")


def parse_args() -> argparse.Namespace:
    """Read simulator, input, scenario, and output paths from the command line."""
    parser = argparse.ArgumentParser(
        description="Run the fixed ASTRA-sim collective-contention experiment."
    )
    parser.add_argument("--astra", type=Path, required=True, help="ASTRA-sim checkout")
    parser.add_argument(
        "--output", type=Path, default=Path("results/collective-contention"),
        help="result directory (default: results/collective-contention)",
    )
    parser.add_argument(
        "--scenarios", default="iteration,baseline,contention",
        help=(
            "comma-separated scenario groups: iteration, baseline, contention; "
            "contention always includes the matched baseline"
        ),
    )
    parser.add_argument(
        "--config", type=Path, default=Path("configs/collective-contention"),
        help="directory containing the fixed experiment inputs",
    )
    return parser.parse_args()


def build_groups(maximum_jobs: int, gpus_per_job: int, topology_npus: int) -> dict[str, list[int]]:
    """Return disjoint communicator groups whose logical Rings share links.

    With 16 four-GPU jobs, job 1 receives [0, 16, 32, 48], job 2 receives
    [1, 17, 33, 49], and so on. Each job is independent, but its Ring spans a
    long portion of the physical 64-endpoint Ring. Activating several groups
    therefore makes their collective traffic contend for physical links.
    """
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


def selected_scenarios(raw: str) -> set[str]:
    """Validate and normalize the comma-separated scenario selection."""
    scenarios = {part.strip().lower() for part in raw.split(",") if part.strip()}
    allowed = {"iteration", "baseline", "contention"}
    if not scenarios or not scenarios.issubset(allowed):
        raise ValueError(
            "--scenarios must contain iteration, baseline, and/or contention"
        )
    return scenarios


def build_scenarios(config: dict, requested: set[str]) -> list[dict]:
    """Expand requested phases into concrete job-count simulation cases."""
    scenarios: list[dict] = []
    if "iteration" in requested:
        scenarios.append({
            "phase": "iteration",
            "name": "training_iteration",
            "job_count": 1,
            "iterations": config["iteration_demo_count"],
        })
    if "baseline" in requested or "contention" in requested:
        scenarios.append({
            "phase": "baseline",
            "name": "single_job_baseline",
            "job_count": 1,
            "iterations": config["measurement_iterations"],
        })
    if "contention" in requested:
        # The job-count sweep changes only concurrency. Workload, placement,
        # topology, collective algorithm, and time-zero arrivals stay fixed.
        for job_count in config["job_counts"]:
            if job_count == 1:
                continue
            scenarios.append({
                "phase": "contention",
                "name": f"concurrent_{job_count:02d}_jobs",
                "job_count": job_count,
                "iterations": config["measurement_iterations"],
            })
    return scenarios


def validate_fixed_inputs(config: dict, config_dir: Path) -> None:
    """Reject mismatches between experiment metadata and simulator inputs."""
    network_name = config.get("network_configuration", "network_64npu_ring.yml")
    system_name = config.get("system_configuration", "system_ring.json")
    network_text = (config_dir / network_name).read_text()
    expected_network_values = {
        "npus_count": config["topology_npus"],
        "bandwidth": config["bandwidth_GBps"],
        "latency": config["latency_ns"],
    }
    for key, expected in expected_network_values.items():
        match = re.search(rf"^{key}:\s*\[\s*([0-9.]+)\s*\]", network_text, re.MULTILINE)
        if not match or float(match.group(1)) != float(expected):
            raise ValueError(f"{key} in {network_name} must equal {expected}")
    if not re.search(r"^topology:\s*\[\s*Ring\s*\]", network_text, re.MULTILINE):
        raise ValueError(f"{network_name} must use the Ring topology")

    system = json.loads((config_dir / system_name).read_text())
    if system.get("all-reduce-implementation") != ["ring"]:
        raise ValueError(f"{system_name} must select Ring AllReduce")
    if system.get("active-chunks-per-dimension") != 4:
        raise ValueError(f"{system_name} must use four active chunks per dimension")


def nearest_rank_percentile(values: Iterable[float], percentile: float) -> float:
    """Calculate a nearest-rank percentile for the small deterministic samples."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate a percentile of an empty sequence")
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def jain_fairness(values: Iterable[float]) -> float:
    """Calculate Jain's fairness index for nonnegative completion-rate values."""
    samples = list(values)
    if not samples or any(value < 0 for value in samples):
        raise ValueError("fairness requires one or more nonnegative values")
    denominator = len(samples) * sum(value * value for value in samples)
    return 1.0 if denominator == 0 else (sum(samples) ** 2) / denominator


def load_chakra(astra: Path):
    """Load protobuf node types and the encoder from the pinned ASTRA checkout."""
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
    """Write one binary Chakra execution trace for every physical endpoint."""
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
                """Append one node after the previously emitted node for this rank."""
                nonlocal previous_id, node_id
                node = chakra["Node"](
                    id=node_id,
                    name=name,
                    type=node_type,
                    duration_micros=duration_us,
                )
                if previous_id is not None:
                    # This dependency creates compute -> AllReduce -> compute.
                    node.data_deps.append(previous_id)
                node.attr.append(chakra["AttributeProto"](name="is_cpu_op", bool_val=False))
                if collective:
                    # pg_name keeps each training job's AllReduce independent;
                    # traffic from different groups can still share physical links.
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
                # ASTRA-sim still needs a trace for every endpoint in the fixed
                # topology. Inactive ranks perform only this tiny placeholder.
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


def build_trace_preview(
    groups: dict[str, list[int]],
    active_group_ids: list[str],
    iterations: int,
    compute_us: int,
    message_bytes: int,
) -> dict:
    """Return a readable description of the binary traces made for a case."""
    jobs = []
    for group_id in active_group_ids:
        operations = []
        for iteration in range(iterations):
            operations.extend([
                {
                    "order": len(operations) + 1,
                    "operation": "compute",
                    "duration_us": compute_us,
                    "starts_after": "previous operation finishes",
                },
                {
                    "order": len(operations) + 2,
                    "operation": "AllReduce",
                    "message_bytes_per_rank": message_bytes,
                    "collective_algorithm": "ring",
                    "starts_after": "previous operation finishes",
                },
            ])
        operations.append({
            "order": len(operations) + 1,
            "operation": "final compute",
            "duration_us": compute_us,
            "starts_after": "previous operation finishes",
        })
        jobs.append({
            "job_id": int(group_id),
            "simulated_gpu_ranks": groups[group_id],
            "operations_on_each_rank": operations,
        })
    return {
        "what_this_file_is": (
            "A human-readable preview of the binary Chakra .et traces. "
            "ASTRA-sim reads the .et files, not this preview."
        ),
        "jobs": jobs,
    }


def run_case(
    scenario: dict,
    config: dict,
    groups: dict[str, list[int]],
    astra: Path,
    config_dir: Path,
    output_dir: Path,
    chakra: dict,
) -> list[dict]:
    """Generate one case, invoke ASTRA-sim, and return one row per active job."""
    case_dir = output_dir / scenario["name"]
    case_dir.mkdir(parents=True, exist_ok=True)
    # All selected jobs start with the same trace at time zero. Their compute
    # phases align, so their AllReduces become ready at overlapping times.
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
    (case_dir / "trace_preview.json").write_text(
        json.dumps(
            build_trace_preview(
                groups,
                active_group_ids,
                scenario["iterations"],
                config["compute_phase_us"],
                config["message_bytes_per_rank"],
            ),
            indent=2,
        ) + "\n"
    )
    network_name = config.get("network_configuration", "network_64npu_ring.yml")
    system_name = config.get("system_configuration", "system_ring.json")
    shutil.copy2(config_dir / network_name, case_dir / "network.yml")
    shutil.copy2(config_dir / system_name, case_dir / "system.json")

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
    # command.json makes the run reproducible and reveals the exact boundary
    # between this Python orchestration and the compiled ASTRA-sim engine.
    (case_dir / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    result = subprocess.run(
        command,
        cwd=astra,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=180,
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
        # A synchronized job finishes when its slowest participating rank does.
        completion_ns = max(completion_by_rank[rank] for rank in groups[group_id])
        completion_us = completion_ns / 1000.0
        communication_and_wait_us = completion_us - compute_total_us
        rows.append({
            "phase": scenario["phase"],
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
    """Compare every concurrent job with the matched isolated-job JCT."""
    baseline_rows = [row for row in rows if row["case"] == "single_job_baseline"]
    if not baseline_rows:
        for row in rows:
            row["slowdown_vs_single_job"] = ""
        return []
    baseline_us = baseline_rows[0]["jct_us"]
    for row in rows:
        row["slowdown_vs_single_job"] = (
            round(row["jct_us"] / baseline_us, 6)
            if row["phase"] in ("baseline", "contention")
            else ""
        )

    summaries = []
    for job_count in sorted({
        row["job_count"]
        for row in rows
        if row["phase"] in ("baseline", "contention")
    }):
        matching = [
            row for row in rows
            if row["job_count"] == job_count
            and row["phase"] in ("baseline", "contention")
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
    """Write dictionaries as a stable, header-first CSV file."""
    if not rows:
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_svg(path: Path, summaries: list[dict]) -> None:
    """Create a dependency-free chart of mean slowdown versus job count."""
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
    """Write a human-readable summary beside the raw and tabular evidence."""
    iteration_row = next(
        (row for row in rows if row["case"] == "training_iteration"), None
    )
    baseline_row = next(row for row in rows if row["case"] == "single_job_baseline")
    lines = [
        "# Collective-contention baseline results",
        "",
        "These values were generated by `scripts/run_collective_contention.py` with the",
        "checked-in fixed inputs. Times are simulated time; they are not Docker wall time.",
        "",
        "## Training iteration and isolated baseline",
        "",
    ]
    if iteration_row is not None:
        lines.append(
            f"The one-iteration trace completed in {iteration_row['jct_us']:.3f} us: "
            f"{iteration_row['compute_total_us']} us of configured compute replay plus "
            f"{iteration_row['communication_and_wait_us']:.3f} us in AllReduce."
        )
    lines.extend([
        f"The {baseline_row['iterations']}-iteration single-job baseline completed in "
        f"{baseline_row['jct_us']:.3f} us. Its measured timing equals "
        f"{baseline_row['compute_total_us']} us of "
        f"configured compute replay plus {baseline_row['iterations']} AllReduce phases "
        "in this uncontended scenario.",
        "",
        "## Concurrent-job contention sweep",
        "",
        "| Concurrent jobs | Mean JCT (us) | P95 JCT (us) | Mean slowdown | Max slowdown | Jain fairness |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
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
    """Validate provenance, run every selected case, and write all outputs."""
    args = parse_args()
    astra = args.astra.resolve()
    output_dir = args.output.resolve()
    config_dir = args.config.resolve()
    requested = selected_scenarios(args.scenarios)
    config = json.loads((config_dir / "experiment.json").read_text())
    validate_fixed_inputs(config, config_dir)
    groups = build_groups(
        config["maximum_jobs"], config["gpus_per_job"], config["topology_npus"]
    )
    scenarios = build_scenarios(config, requested)
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
