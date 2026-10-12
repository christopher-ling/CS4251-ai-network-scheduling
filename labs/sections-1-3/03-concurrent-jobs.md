# Section 3: increase concurrent jobs

## Question

How does shared-link contention change completion time when more independent
training jobs communicate concurrently?

This sweep activates 1, 2, 4, 8, and 16 jobs. Every job keeps four GPUs, three
iterations, 100-us compute phases, a 16-MiB-per-rank AllReduce, and a time-zero
arrival. The physical 64-NPU Ring does not change.

## Run the matched baseline and sweep

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --sections 3 \
  --output results/tutorial-section-3
```

Selecting Section 3 automatically runs the Section 2 single-job baseline.
Without that matched baseline, slowdown would not have a valid denominator.

Inspect:

```sh
column -s, -t results/tutorial-section-3/contention_summary.csv
column -s, -t results/tutorial-section-3/per_job_summary.csv | less -S
```

Open `results/tutorial-section-3/contention-slowdown.svg` in a browser or VS
Code to view the generated plot.

## Why the jobs contend

The four ranks of each job are spaced 16 positions apart. A logical Ring
transfer between those ranks traverses multiple physical-ring links. Adjacent
job groups therefore request overlapping physical routes. Increasing active
jobs increases the number of collective chunks queued on shared links.

The launcher holds the following constant:

- physical topology and routing behavior;
- GPUs per job and rank placement;
- Ring AllReduce configuration;
- compute duration and iteration count;
- message size, capacity, and latency;
- simultaneous job arrival.

Only the number of active jobs changes.

## Interpret the outputs

- `mean_jct_us`: average completion time across active jobs.
- `p95_jct_us`: nearest-rank 95th percentile across active jobs.
- `makespan_us`: completion of the final job.
- `mean_slowdown`: mean JCT divided by the isolated Section 2 JCT.
- `max_slowdown`: worst individual-job slowdown.
- `jain_fairness_completion_rate`: Jain's index applied to reciprocal JCT.

A larger slowdown demonstrates contention in this constructed stress case. It
does not by itself prove that a scheduling policy improves performance or that
the workload represents a production model. Sections 4 and later must compare
policies using these same controlled inputs.

## Completion checklist

- All six scenario directories have a raw log and exact input copies.
- Every run reports all 64 endpoints finished.
- The single-job baseline is exactly the Section 2 workload.
- Job count is the only intentionally changed independent variable.
- Results are reported as simulated time, not Docker execution time.
- Claims distinguish completion slowdown from direct link-utilization data.
