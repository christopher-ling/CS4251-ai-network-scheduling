# Section 2: measure the single-job baseline

## Question

How long does the fixed training workload take when no other job competes for
the network?

The baseline keeps the Section 1 model and expands it to three iterations:

```text
(compute 100 us -> AllReduce 16 MiB/rank) x 3 -> final compute 100 us
```

Only job 1 is active. It has four GPUs at ranks `[0, 16, 32, 48]`. The physical
network is still the 64-NPU Ring used by every later contention run.

## Run only Section 2

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --sections 2 \
  --output results/tutorial-section-2
```

Inspect the evidence:

```sh
cat results/tutorial-section-2/per_job_summary.csv
cat results/tutorial-section-2/section2_single_job_baseline/network.yml
cat results/tutorial-section-2/section2_single_job_baseline/system.json
```

## Metrics

- `jct_us`: completion time of the slowest rank in the job.
- `compute_total_us`: four replayed compute phases, totaling 400 us.
- `communication_and_wait_us`: JCT minus configured compute replay time.
- `mean_allreduce_and_wait_us`: that remainder divided across three
  collectives.
- `mean_iteration_us`: `(JCT - final compute) / 3`.

`communication_and_wait_us` includes collective transfer and any contention
waiting. It is not measured physical-link utilization. The pinned analytical
backend's ordinary completion output does not expose a per-link utilization
series, so this tutorial does not invent one.

The Section 2 JCT becomes the denominator for every Section 3 slowdown. Keeping
the baseline in the same topology matters: changing network size, placement,
message size, or GPUs per job would confound the comparison.

## Acceptance checks

- All 64 endpoints finish.
- The active job contains exactly four ranks.
- The active ranks finish at the same collective result time.
- `jct_us` is greater than the configured 400 us of compute replay.
- The command, exact inputs, raw log, and simulator revision are saved.

Continue to [Section 3](03-concurrent-jobs.md).
