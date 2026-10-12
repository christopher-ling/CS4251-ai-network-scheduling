# Network Scheduling for Distributed AI Training

> This branch includes the team onboarding guide. Start with
> [`guide/README.md`](guide/README.md). The guide calls the same experiment
> runner and configurations as the research implementation.

This repository studies how collective communication from already-running
distributed training jobs should share a congested network. GPU placement is
fixed before each experiment. The research target is network scheduling:
collective admission, ordering, priority, or rate control after communication
becomes ready.

## Current implementation

The first reproducible experiment models repeated GPU computation and Ring
AllReduce, establishes an isolated-job reference, and sweeps 1, 2, 4, 8, and
16 concurrent jobs while holding the workload and network inputs fixed.

```text
compute -> AllReduce -> compute -> ... -> job completion
```

The implementation uses ASTRA-sim's congestion-aware analytical backend for
fast trace and contention validation. Packet-level congestion-control studies
will use the ns-3 backend.

## Run the baseline

Use ASTRA-sim commit `4ce9ecfe746a3ee5fe47559a11d91644d641fa7f` and build
the analytical backend in the upstream Docker image. Mount the ASTRA-sim
checkout at `/app/astra-sim` and this repository at `/app/team`, then run:

```sh
cd /app/team
python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --output results/collective-contention
```

The runner generates Chakra traces, launches every scenario, requires all 64
simulated endpoints to finish, and writes raw logs plus per-job and aggregate
CSV summaries.

## Controlled design

| Input | Value |
|---|---:|
| Analytical topology | 64-NPU bidirectional Ring |
| GPUs per job | 4 |
| Concurrent jobs | 1, 2, 4, 8, 16 |
| Collective | Ring AllReduce |
| Message size | 16 MiB per rank per collective |
| Compute phase | 100 us |
| Measured iterations | 3 |
| Link capacity | 50 GB/s |
| Configured link latency | 500 ns |

The analytical Ring is an initial shared-path stress model. It is not the final
packet-level topology for HPCC or MLTCP evaluation.

## Recorded results

| Concurrent jobs | Mean JCT | Slowdown vs. isolated job |
|---:|---:|---:|
| 1 | 6.362602 ms | 1.000x |
| 2 | 6.391649 ms | 1.005x |
| 4 | 6.449742 ms | 1.014x |
| 8 | 11.730527 ms | 1.844x |
| 16 | 22.901272 ms | 3.599x |

These are simulated times for one controlled synthetic workload. See
[`results/collective-contention/`](results/collective-contention/README.md) for
exact inputs, raw logs, per-job data, provenance, and limitations.

## Repository structure

```text
configs/      Fixed experiment inputs
docs/         Architecture, terminology, evaluation plan, and roadmap
scripts/      Trace generation, experiment execution, and analysis
results/      Recorded evidence and generated summaries
tests/        Checks for workload construction and metric calculations
```

## Research plan

The project separates scheduling policy from transport congestion control.
Scheduler comparisons will hold the transport fixed; transport comparisons
will hold scheduler behavior fixed.

1. Validate compute/AllReduce traces and concurrent-job contention.
2. Reproduce the workload with the ASTRA-sim ns-3 backend.
3. Implement immediate, FIFO, and size-aware scheduling baselines.
4. Reproduce HPCC and evaluate MLTCP integration feasibility.
5. Implement a congestion-aware collective scheduler using network state and
   job progress.
6. Evaluate JCT, slowdown, fairness, queueing, utilization, loss, and overhead.
7. Run robustness experiments with another topology and workload mix.

See the [project plan](docs/project-plan.md) and
[evaluation plan](docs/evaluation-plan.md) for acceptance criteria.

## Documentation

- [Architecture](docs/architecture.md)
- [Project plan](docs/project-plan.md)
- [Evaluation plan](docs/evaluation-plan.md)
- [Methodology traceability](docs/methodology-traceability.md)
- [Terminology](docs/glossary.md)
- [ASTRA-sim assessment](docs/tool-assessment.md)

## Attribution

ASTRA-sim is maintained upstream. Copied configuration formats are covered by
the upstream MIT license in [`configs/UPSTREAM-LICENSE.txt`](configs/UPSTREAM-LICENSE.txt).
