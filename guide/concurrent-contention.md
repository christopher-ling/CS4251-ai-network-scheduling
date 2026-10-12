# Run several jobs and create contention

## Goal

Hold each job and the network fixed while increasing the number of jobs that
communicate at the same time.

## Understand job placement

Open `guide/workspace/experiment.json` and find:

```json
"maximum_jobs": 16,
"gpus_per_job": 4,
"job_counts": [1, 2, 4, 8, 16],
"placement": "strided"
```

Open `build_groups` in `scripts/run_collective_contention.py`. It assigns four
ranks to every job. For example, job 1 uses ranks `[0, 16, 32, 48]`. This
strided placement makes each job's logical AllReduce cross long portions of
the 64-NPU physical ring, so simultaneous jobs request shared links.

`build_scenarios` turns `job_counts` into the cases `concurrent_02_jobs`,
`concurrent_04_jobs`, and so on. Every case keeps the per-job compute,
AllReduce size, collective algorithm, topology, and arrival time fixed.

## Run a short sweep

First change `job_counts` to:

```json
"job_counts": [1, 2, 4]
```

Run:

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config guide/workspace \
  --scenarios contention \
  --output results/onboarding/contention
```

Open:

```text
results/onboarding/contention/contention_summary.csv
results/onboarding/contention/per_job_summary.csv
results/onboarding/contention/contention-slowdown.svg
```

The runner automatically includes a one-job baseline. `mean_slowdown` divides
each contended JCT by that baseline, while `makespan_us` records when the final
active job finishes.

## Run the full sweep

Restore `job_counts` to `[1, 2, 4, 8, 16]`, predict when shared links will
cause noticeable slowdown, and rerun the same command. The reference results
show about `1.844x` mean slowdown at eight jobs and `3.599x` at sixteen jobs.

Open
`results/onboarding/contention/concurrent_16_jobs/trace_preview.json`. It shows
sixteen independent jobs, each with four ranks and the same operation chain.
The difference in completion time comes from their overlapping use of the
network model.

## What this proves

This experiment shows that the constructed analytical ring creates contention
as concurrency increases. It does not yet demonstrate an improved scheduler.
The next research work must compare explicit scheduling policies. Packet-level
queueing, loss, HPCC, and possible MLTCP evaluation require the ns-3 backend.

Restore the input with `git restore guide/workspace/experiment.json`, then
continue to [Understand the experiment runner](how-the-code-works.md).
