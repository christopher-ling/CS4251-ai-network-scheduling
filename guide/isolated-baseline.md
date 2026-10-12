# Isolated-job baseline

## Objective

Measure the fixed workload without another job competing for network links.

```sh
cd /app/team
python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --scenarios baseline \
  --output results/onboarding/baseline
```

Inspect:

```sh
cat results/onboarding/baseline/per_job_summary.csv
cat results/onboarding/baseline/single_job_baseline/network.yml
cat results/onboarding/baseline/single_job_baseline/system.json
```

The workload has four GPU ranks and three compute/AllReduce iterations followed
by final compute. Its JCT becomes the denominator for slowdown in the
concurrent-job experiment.

The reference JCT is approximately `6362.602 us`. The
`communication_and_wait_us` column subtracts configured compute from JCT. It is
not direct physical-link utilization.

Continue to [Concurrent-job contention](concurrent-contention.md).

