# CS4251 · Network Scheduling for Distributed AI Training

Reproducible ASTRA-sim experiments for studying collective communication contention and admission policies across concurrent training workloads.

**Status:** preliminary experiments and an optional admission prototype. The project’s final congestion-aware algorithm and broader evaluation are in development.

## Research scope

The project evaluates network scheduling for already-running distributed training jobs. GPU placement, routing, and collective algorithms are held fixed during scheduling-policy comparisons. The objective is to reduce mean job completion time while accounting for scheduler-induced waiting and per-job slowdown.

ASTRA-sim is used for execution-timing simulation. Current workloads are synthetic dependency graphs rather than profiled model training runs.

## Getting started

Follow [Installation and quickstart](labs/00-quickstart.md) to clone the pinned simulator, build the Docker environment, and mount both repositories.

With the environment configured, run inside Docker:

```sh
# Single-collective bandwidth experiment
bash /app/team/scripts/run_bandwidth_lab.sh /app/astra-sim

# Synthetic training cycles and shared-link experiments
cd /app/team
python3 scripts/run_learning_experiments.py --astra /app/astra-sim
```

The scripts capture inputs and logs and require completion of all 16 simulated endpoints. Outputs are written to the mounted team repository. Enabling admission-policy comparisons requires the optional patch documented in Experiment 3.

## Experiments

| Experiment | Objective | Source changes required |
|---|---|---|
| [1. AllReduce bandwidth](labs/01-allreduce-bandwidth.md) | Measure collective timing at fixed workload with different link capacities | None; configuration only |
| [2. Training cycles and contention](labs/02-training-and-contention.md) | Model compute dependencies and compare isolated versus concurrent jobs | None; generated traces and configurations |
| [3. Collective admission](labs/03-admission-prototype.md) | Compare immediate admission, FIFO, and size-based priority with aging | Optional simulator patch |

See [Development workflow](docs/development-workflow.md) for the distinction between running experiments, editing configurations, generating traces, and modifying the scheduler.

## Reference results

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

Fresh containers and experiment launchers were verified using the successfully built image. A second clean end-to-end image rebuild was not performed. The optional patch is stored separately and its diff is recorded with policy results.

## Repository structure

```text
configs/    Reference network, system, and memory configurations
scripts/    Experiment launchers and synthetic trace generator
labs/       Installation and reproducible experiment protocols
docs/       Architecture, terminology, workflow, and tool assessment
patches/    Optional coordinated admission prototype
results/    Recorded logs, summaries, input descriptions, and versions
```

Generated binary traces are excluded from version control and recreated by the generator.

## Limitations and next work

Current evaluation covers a bidirectional ring stress case and a nonblocking switch control. The pinned analytical backend models chunk queueing and supports one-dimensional topologies; packet loss, retransmissions, and real telemetry are outside these experiments. The admission prototype has a single global slot and limited trace assumptions.

Next work is to select a network-state signal, establish a literature-grounded algorithm gap, expand workloads and bottleneck topologies, and evaluate timing and fairness against matched baselines. See [Tool assessment](docs/tool-assessment.md).

## Documentation

- [Terminology](docs/glossary.md)
- [Development workflow](docs/development-workflow.md)
- [Experiment review checklist](docs/meeting-guide.md)
- [Official ASTRA-sim installation](https://astra-sim.github.io/astra-sim-docs/getting-started/setup.html)
- [Official analytical build instructions](https://astra-sim.github.io/astra-sim-docs/getting-started/build.html)

## Attribution

ASTRA-sim is developed and maintained upstream. Copied configuration files are covered by the upstream MIT license included at [configs/UPSTREAM-LICENSE.txt](configs/UPSTREAM-LICENSE.txt). No separate license has been selected for team-authored code.
