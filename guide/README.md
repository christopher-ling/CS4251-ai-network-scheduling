# ASTRA-sim learning path

This guide begins with four simulated GPUs and one AllReduce. It introduces
the 64-endpoint, multi-job research experiment only after the simulator's
inputs and outputs are clear.

Complete the pages in order:

1. [Set up ASTRA-sim and the project](setup.md)
2. [Understand ASTRA-sim's inputs and execution](fundamentals.md)
3. [Run a four-GPU training iteration](training-trace.md)
4. [Change compute, message size, and bandwidth](controlled-changes.md)
5. [Measure the isolated-job baseline](isolated-baseline.md)
6. [Scale to the multi-job contention experiment](concurrent-contention.md)
7. [Understand the experiment runner](how-the-code-works.md)

The learning process is:

```text
understand one file -> predict a result -> run the simulator
       -> read the evidence -> change one variable -> explain the difference
```

## Two examples, one implementation

| Example | Purpose |
|---|---|
| `examples/training-iteration/` | Four endpoints, one job, and a small 1-MiB message for learning |
| `examples/collective-contention/` | 64 endpoints and up to 16 jobs for the project experiment |

Both examples use `scripts/run_collective_contention.py`. The smaller example
teaches the mechanism; the larger example produces the controlled contention
study described in the report. The recorded research inputs remain in
`configs/collective-contention/`, and the recorded evidence remains in
`results/collective-contention/`.

Use the [glossary](../docs/glossary.md) whenever a term is unfamiliar.
