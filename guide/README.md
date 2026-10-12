# ASTRA-sim onboarding

This guide connects the project's code to the distributed-training behavior it
models. Complete the pages in this order:

1. [Environment setup](setup.md)
2. [Compute and AllReduce trace](training-trace.md)
3. [Isolated-job baseline](isolated-baseline.md)
4. [Concurrent-job contention](concurrent-contention.md)

The guide calls the same runner used by the research implementation. It does
not maintain a second experiment script.

## What ASTRA-sim does here

ASTRA-sim does not train a neural network or calculate real gradients. It
replays a dependency graph for each simulated GPU rank:

```text
compute for a configured duration
        |
        v
AllReduce a configured number of bytes
        |
        v
next compute phase
```

The system layer decomposes AllReduce into communication steps. The analytical
network backend models how those steps use the configured topology and how
chunks wait when they request the same link.

## Files to recognize

| Path | Purpose |
|---|---|
| `configs/collective-contention/experiment.json` | Workload and sweep values |
| `configs/collective-contention/network_64npu_ring.yml` | Physical analytical topology |
| `configs/collective-contention/system_ring.json` | Collective algorithm and chunk settings |
| `scripts/run_collective_contention.py` | Trace generation, execution, validation, and analysis |
| `results/collective-contention/` | Recorded reference evidence |

Use [`docs/glossary.md`](../docs/glossary.md) when a term is unfamiliar.

