# ASTRA-sim fundamentals

## The simulator's job

ASTRA-sim answers timing questions about a distributed AI system. It does not
train a model or calculate gradients. It receives descriptions of operations
and hardware, simulates their timing, and reports when each rank finishes.

```text
workload trace ────── what each GPU does and in what order
system configuration ─ how a collective such as AllReduce is performed
network configuration ─ topology, link capacity, and link delay
remote-memory config ── whether remote memory is modeled
                              │
                              v
                          ASTRA-sim
                              │
                              v
                  completion time for every rank
```

## The four-GPU example

Open `examples/training-iteration/`. It contains three human-editable inputs:

| File | Read this field first | Meaning |
|---|---|---|
| `experiment.json` | `compute_phase_us` | Duration of a compute node |
| `system.json` | `all-reduce-implementation` | Algorithm used for AllReduce |
| `network.yml` | `topology`, `bandwidth`, `latency` | Physical network model |

The workload itself will be generated as four binary Chakra files:

```text
workload.0.et
workload.1.et
workload.2.et
workload.3.et
```

Each file is the operation graph for one simulated GPU rank. The project also
writes `trace_preview.json`, a readable description of the same operations.

## What happens when a simulation runs

1. The Python runner reads `experiment.json`.
2. It creates one Chakra execution trace per rank.
3. ASTRA-sim's workload layer releases operations when their dependencies are
   satisfied.
4. The system layer breaks Ring AllReduce into network transfers.
5. The analytical backend models those transfers on the configured Ring.
6. The runner collects rank completion times and writes CSV results.

Continue to [Run a four-GPU training iteration](training-trace.md).
