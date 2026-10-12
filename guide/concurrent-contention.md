# Concurrent-job contention

## Objective

Keep the topology and workload fixed while increasing the number of active
jobs.

```sh
cd /app/team
python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --scenarios contention \
  --output results/onboarding/contention
```

Selecting `contention` automatically runs the matched isolated baseline.

Inspect:

```sh
cat results/onboarding/contention/contention_summary.csv
cat results/onboarding/contention/per_job_summary.csv
```

Open `results/onboarding/contention/contention-slowdown.svg` in a browser or VS
Code.

Every job retains four GPUs, three iterations, 100-us compute phases, 16-MiB
AllReduce messages, and a time-zero arrival. Only active job count changes.

Expected reference behavior:

| Jobs | Mean JCT | Mean slowdown |
|---:|---:|---:|
| 1 | 6.363 ms | 1.000x |
| 2 | 6.392 ms | 1.005x |
| 4 | 6.450 ms | 1.014x |
| 8 | 11.731 ms | 1.844x |
| 16 | 22.901 ms | 3.599x |

This demonstrates contention in the constructed analytical Ring. It does not
demonstrate that a scheduler improves performance. The next research task is
packet-level backend qualification followed by matched policy baselines.

## What requires code changes?

- Changing experiment values edits JSON, YAML, or the trace generator.
- Adding a collective admission policy changes ASTRA-sim scheduling behavior.
- HPCC and MLTCP evaluation requires the ns-3 transport implementation and its
  packet-level signals.

The current onboarding experiments do not modify upstream ASTRA-sim source.
