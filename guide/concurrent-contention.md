# Create contention with several jobs

## What this lesson teaches

**Contention** occurs when communication from different jobs needs the same
limited links at overlapping times. The workload, collective algorithm, and
network stay fixed in this lesson. You change only the number of active jobs.

## 1. Choose the job counts

Open `guide/workspace/experiment.json` and find:

```json
"job_counts": [1, 2, 4, 8, 16]
```

Each job receives four simulated GPUs. All jobs arrive at time zero and issue
the same three AllReduces. Their rank placement makes different logical jobs
traverse shared portions of the 64-NPU physical ring.

Temporarily shorten the sweep to:

```json
"job_counts": [1, 2, 4]
```

## 2. Run and inspect the smaller experiment

Use **Tasks: Run Task > Tutorial: Run contention sweep**. Open:

```text
results/onboarding/contention/contention_summary.csv
results/onboarding/contention/contention-slowdown.svg
```

VS Code previews the SVG chart. In the CSV:

- `mean_jct_us` is mean job completion time;
- `mean_slowdown` divides contended JCT by the one-job baseline;
- `makespan_us` is when the final active job finishes.

The runner includes the one-job baseline automatically so slowdown always has
a matching denominator.

## 3. Increase contention

Restore the full list:

```json
"job_counts": [1, 2, 4, 8, 16]
```

Predict where slowdown will become noticeable, then run the task again. The
checked-in reference results show little change through four jobs, about
`1.844x` mean slowdown at eight jobs, and about `3.599x` at sixteen jobs.

Open one generated `trace_preview.json` under
`results/onboarding/contention/concurrent_16_jobs/`. It shows sixteen jobs,
each with its own four-rank communicator group and the same operation chain.

## 4. State the conclusion carefully

This experiment demonstrates that the constructed analytical ring produces
shared-resource contention as job concurrency increases. It does not yet show
that a new network scheduler improves performance. The next research stage is
to compare explicit admission policies and qualify the packet-level ns-3
backend for queue, utilization, HPCC, and possible MLTCP measurements.

Continue to [Connect the files to the Python runner](how-the-code-works.md).
