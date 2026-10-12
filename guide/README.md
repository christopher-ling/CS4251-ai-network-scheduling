# Learn ASTRA-sim in VS Code

This tutorial is for someone who has never used ASTRA-sim. You will edit
simulation inputs in VS Code, run them with named VS Code tasks, and inspect
the files produced by the simulator. The terminal only starts Docker and
ASTRA-sim; it is not the subject of the tutorial.

Complete these lessons in order:

1. [Set up the VS Code workspace](setup.md)
2. [Build and change one training trace](training-trace.md)
3. [Measure one job and change the network](isolated-baseline.md)
4. [Create contention with several jobs](concurrent-contention.md)
5. [Connect the files to the Python runner](how-the-code-works.md)

Each lesson follows the same loop:

```text
open an input file -> change one value -> predict the effect
       -> run a named VS Code task -> inspect generated files
       -> explain what ASTRA-sim modeled
```

## What you are actually simulating

ASTRA-sim does not train a model and does not calculate gradients. It receives
a description of work that a real distributed training job would perform:

```text
GPU compute -> gradients are ready -> AllReduce -> updated values are available
```

For this project, one simulated job has four GPU **ranks**. Each rank performs
compute, then all four ranks participate in the same AllReduce. The system
configuration says to perform that collective using a ring algorithm. The
network configuration says the simulated machines are connected by a physical
ring with limited-capacity links. ASTRA-sim calculates when the operations
finish, including waiting caused by overlapping communication.

## The four kinds of files

| File | Question it answers |
|---|---|
| `guide/workspace/experiment.json` | What work do the jobs perform, and how many jobs run? |
| `guide/workspace/system_ring.json` | Which collective algorithm carries out AllReduce? |
| `guide/workspace/network_64npu_ring.yml` | What physical network carries the messages? |
| `scripts/run_collective_contention.py` | How are traces generated, ASTRA-sim launched, and results summarized? |

The files in `guide/workspace/` are practice copies. Editing them will not
change the checked-in research results. If an experiment becomes confusing,
open VS Code's **Source Control** panel, select the changed file, and choose
**Discard Changes**.

Use [the glossary](../docs/glossary.md) whenever a term is unfamiliar.
