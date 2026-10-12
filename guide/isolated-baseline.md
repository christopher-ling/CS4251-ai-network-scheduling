# Measure the isolated-job baseline

## Why a baseline is needed

The baseline measures one job without another job competing for links. Later,
each contended job's completion time is divided by this value to calculate
slowdown.

The same four-GPU example now runs three compute/AllReduce iterations followed
by final compute. Open `examples/training-iteration/experiment.json` and find
`measurement_iterations: 3`.

## Run the baseline

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config examples/training-iteration \
  --scenarios baseline \
  --output results/learning/isolated-baseline
```

Open:

```text
results/learning/isolated-baseline/per_job_summary.csv
results/learning/isolated-baseline/single_job_baseline/description.json
results/learning/isolated-baseline/single_job_baseline/network.yml
results/learning/isolated-baseline/single_job_baseline/system.json
```

Verify that the row reports one job, four GPUs, three iterations, and a 1-MiB
message. `compute_total_us` should be 400 because three iterations plus final
compute create four 100-us compute operations.

The verified starting baseline is `489.4 us`: 400 us of configured compute and
89.4 us across three AllReduce phases, or 29.8 us per AllReduce in this
uncontended analytical example.

The copied JSON and YAML files preserve the exact inputs used for this result.
`communication_and_wait_us` is JCT minus configured compute time. It is not
measured physical-link utilization.

Continue to [Scale to the multi-job contention experiment](concurrent-contention.md).
