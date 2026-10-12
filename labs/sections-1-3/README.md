# ASTRA-sim tutorial: methodology Sections 1-3

This tutorial implements the first three stages of the project methodology with
one controlled experiment. It teaches ASTRA-sim by connecting each input file
to a research question. The implementation is shared with the recorded
experiment; the tutorial does not contain a second copy of the simulator code.

## Learning path

1. [Represent one training iteration](01-training-iteration.md)
2. [Measure the uncontended single-job baseline](02-single-job-baseline.md)
3. [Increase concurrent jobs and measure contention](03-concurrent-jobs.md)

Complete [the installation and Docker quickstart](../00-quickstart.md) first.
All commands in the three tutorial sections run inside Docker from `/app/team`.

## Fixed design

| Input | Value |
|---|---:|
| Physical topology | 64-NPU bidirectional Ring |
| GPUs per job | 4 |
| Job counts | 1, 2, 4, 8, 16 |
| Collective | Ring AllReduce |
| Message size | 16 MiB per rank per AllReduce |
| Compute replay | 100 us per compute phase |
| Section 1 iterations | 1 |
| Sections 2-3 iterations | 3 |
| Link capacity | 50 GB/s |
| Configured link latency | 500 ns |
| Job arrival time | 0 ns for every active job |

Job `j` receives ranks `[j, j + 16, j + 32, j + 48]`, using zero-based
`j`. The jobs have disjoint simulated GPUs, but their collective routes cross
shared physical links. This satisfies the project boundary: GPU placement is
fixed before the network experiment begins.

## One-command reproduction

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --output results/sections-1-3
```

The launcher generates traces, runs six scenarios, requires all 64 endpoints
to finish, and writes per-job and aggregate CSV files. Binary `.et` traces are
generated evidence and are ignored by Git.

## Where code and evidence live

```text
configs/sections-1-3/       Fixed experiment inputs
scripts/run_sections_1_to_3.py
                             Trace generation, execution, validation, metrics
labs/sections-1-3/          This guided explanation
results/sections-1-3/       Recorded inputs, logs, summaries, and chart
tests/test_sections_1_to_3.py
                             Checks for layout and analysis helpers
```

The older bandwidth-sensitivity and admission-policy labs remain useful
supplementary experiments. They are not alternate implementations of these
three methodology stages.

## Screenshot guidance

Screenshots are optional illustrations, not evidence required to reproduce the
experiment. If the team adds them later, capture only:

- Section 1: the terminal completion line plus the generated description.
- Section 2: the single-job row in `per_job_summary.csv`.
- Section 3: `contention-slowdown.svg` and the final terminal validation.

Keep the commands, CSV files, and raw logs as the authoritative evidence.
