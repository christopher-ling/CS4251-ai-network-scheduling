# ASTRA-sim tutorial

This tutorial teaches ASTRA-sim by connecting every experiment to the files
and code that create it. Use any IDE to browse and edit the project. Use its
terminal to build the simulator and run the experiments when instructed.

Complete the lessons in order:

1. [Set up ASTRA-sim and the project](setup.md)
2. [Create and change a training trace](training-trace.md)
3. [Run one job and change the network](isolated-baseline.md)
4. [Run several jobs and create contention](concurrent-contention.md)
5. [Understand the experiment runner](how-the-code-works.md)

Each lesson follows this process:

```text
read the relevant file -> identify the code responsible
       -> change one input -> predict the effect
       -> run ASTRA-sim -> inspect the generated evidence
```

## What ASTRA-sim does

ASTRA-sim models the timing of distributed AI systems. It does not train a
neural network or calculate numerical gradients. The project gives it a trace
describing work that a real training job would perform:

```text
GPU compute -> local gradients become ready -> AllReduce
            -> every GPU receives the combined result -> next compute phase
```

One simulated job in this tutorial has four GPU **ranks**. The workload trace
says when compute and AllReduce become ready. The system configuration says
how to implement AllReduce. The network configuration says which physical
links carry the communication. ASTRA-sim calculates when each operation and
job finishes, including waiting caused by shared links.

## What each file controls

| File | Role in the simulation |
|---|---|
| `guide/workspace/experiment.json` | Workload size, iteration count, GPU count, and concurrent-job sweep |
| `guide/workspace/system_ring.json` | Collective algorithm and chunk behavior |
| `guide/workspace/network_64npu_ring.yml` | Physical topology, bandwidth, and latency |
| `scripts/run_collective_contention.py` | Trace generation, ASTRA-sim invocation, validation, and analysis |
| `compose.yaml` | Docker environment containing both repositories |

The `guide/workspace/` files are editable practice copies. The original
research inputs remain in `configs/collective-contention/`. Use the
[glossary](../docs/glossary.md) whenever a term is unfamiliar.
