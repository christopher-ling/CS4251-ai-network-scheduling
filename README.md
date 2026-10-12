# CS4251 · Network Scheduling for Distributed AI Training

Reproducible ASTRA-sim experiments for studying collective communication contention and admission policies across concurrent training workloads.

**Status:** preliminary experiments and an optional admission prototype. The project’s final congestion-aware algorithm and broader evaluation are in development.

## Research scope

The project evaluates network scheduling for already-running distributed training jobs. GPU placement, routing, and collective algorithms are held fixed during scheduling-policy comparisons. The objective is to reduce mean job completion time while accounting for scheduler-induced waiting and per-job slowdown.

ASTRA-sim is used for execution-timing simulation. Current workloads are synthetic dependency graphs rather than profiled model training runs.

## Running the methodology implementation

Build the pinned ASTRA-sim revision with its Docker environment, then mount the
ASTRA-sim checkout at `/app/astra-sim` and this repository at `/app/team`. Run:

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --output results/sections-1-3
```

This command reproduces methodology Sections 1-3: one compute/AllReduce iteration, a matched single-job baseline, and a 1/2/4/8/16-job contention sweep. It captures inputs and logs and requires completion of all 64 simulated endpoints. Outputs are written to the mounted team repository.

## Methodology implementation

| Stage | Objective | Primary artifacts |
|---|---|---|
| 1. Training iteration | Generate the compute/AllReduce dependency trace | `scripts/run_sections_1_to_3.py` |
| 2. Single-job baseline | Measure the fixed workload without inter-job contention | `results/sections-1-3/section2_single_job_baseline/` |
| 3. Concurrent jobs | Hold inputs fixed while sweeping 1/2/4/8/16 active jobs | `results/sections-1-3/contention_summary.csv` |

See [Development workflow](docs/development-workflow.md) for the distinction between running experiments, editing configurations, generating traces, and modifying the scheduler.

## Reference results

The controlled Sections 1-3 run uses a fixed 64-NPU Ring, four GPUs per job,
three AllReduce iterations, 16 MiB per rank per collective, and 100-us compute
phases. Only the number of active jobs changes in the contention sweep.

| Concurrent jobs | Mean JCT | Mean slowdown vs. one job |
|---:|---:|---:|
| 1 | 6.362602 ms | 1.000x |
| 2 | 6.391649 ms | 1.005x |
| 4 | 6.449742 ms | 1.014x |
| 8 | 11.730527 ms | 1.844x |
| 16 | 22.901272 ms | 3.599x |

The constructed placement shows little slowdown at two and four jobs, then a
clear contention threshold at eight jobs. See the
[recorded results](results/sections-1-3/README.md), per-job CSV, raw logs, and
generated chart before drawing policy conclusions. The ordinary analytical
output does not expose direct per-link utilization; the repository does not
label elapsed communication-and-wait time as utilization.

Earlier preliminary experiments used a different 16-NPU configuration:

| Scenario | Simulated completion time |
|---|---:|
| Single 16-rank AllReduce, 50 GB/s | 99.640 µs |
| Single 16-rank AllReduce, 25 GB/s | 136.240 µs |
| Three-collective training cycle, 50 GB/s | 698.920 µs |
| Three-collective training cycle, 25 GB/s | 808.720 µs |
| Shared-ring job, isolated | 2.083140 ms |
| Shared-ring job, concurrent pair | 3.682600 ms per job |

The bandwidth comparison increases collective duration by 36.7%. The shared-ring stress case increases each job’s elapsed completion time by 76.8% versus its isolated reference. The experiments use different payloads and active-chunk settings; see their specifications before comparing across rows. A nonblocking-switch control shows no concurrent-run slowdown for the disjoint endpoint groups.

In the heterogeneous admission experiment, size/aging reduces mean JCT by approximately 14.0% versus FIFO and 0.30% versus immediate admission. This is one deterministic synthetic scenario, not evidence of general superiority or algorithmic novelty. The prototype uses ready-request metadata and a global admission slot, not link telemetry.

## Reproducibility

- Simulator: [ASTRA-sim](https://github.com/astra-sim/astra-sim), commit `4ce9ecfe746a3ee5fe47559a11d91644d641fa7f`.
- Backend: congestion-aware analytical network model.
- Verified environment: Docker on Apple Silicon (M1).
- Time convention: 1 ns per printed tick for the pinned analytical configuration.
- Workload payload: the supplied `1MB` example encodes 1,048,576 bytes (1 MiB) per rank.
- Evidence: configuration copies, logs, summaries, and recursive submodule records under `results/`.

The Sections 1-3 suite was verified after a clean end-to-end analytical build
at the pinned simulator commit. `results/sections-1-3/astra-sim-status.txt` is
empty, confirming that the recorded run used no simulator source changes. The
optional admission patch is stored separately and its diff is recorded with
the older policy results.

Run the lightweight layout and analysis checks from the team repository:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Repository structure

```text
configs/    Fixed and reference network, system, and workload parameters
scripts/    Reusable experiment launchers, trace generation, and analysis
docs/       Architecture, terminology, workflow, and tool assessment
patches/    Optional coordinated admission prototype
results/    Recorded logs, summaries, input descriptions, and versions
tests/      Lightweight checks for experiment layout and analysis helpers
```

Generated binary traces are excluded from version control and recreated by the generator.

## Limitations and next work

Current evaluation includes the fixed 64-NPU Ring concurrency sweep plus an earlier 16-NPU ring stress case and nonblocking-switch control. The pinned analytical backend models chunk queueing and supports one-dimensional topologies; packet loss, retransmissions, direct link-utilization telemetry, and real congestion feedback are outside these experiments. The admission prototype has a single global slot and limited trace assumptions.

Next work is to select a network-state signal, establish a literature-grounded algorithm gap, expand workloads and bottleneck topologies, and evaluate timing and fairness against matched baselines. See [Tool assessment](docs/tool-assessment.md).

## Documentation

- [Terminology](docs/glossary.md)
- [Development workflow](docs/development-workflow.md)
- [Experiment review checklist](docs/meeting-guide.md)
- [Official ASTRA-sim installation](https://astra-sim.github.io/astra-sim-docs/getting-started/setup.html)
- [Official analytical build instructions](https://astra-sim.github.io/astra-sim-docs/getting-started/build.html)

## Attribution

ASTRA-sim is developed and maintained upstream. Copied configuration files are covered by the upstream MIT license included at [configs/UPSTREAM-LICENSE.txt](configs/UPSTREAM-LICENSE.txt). No separate license has been selected for team-authored code.
