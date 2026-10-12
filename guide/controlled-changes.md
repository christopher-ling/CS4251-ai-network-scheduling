# Controlled changes

This lesson changes one input at a time. Make a prediction before each run,
then compare `results/learning/training-iteration/per_job_summary.csv`.

Use this command after every edit:

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config examples/training-iteration \
  --scenarios iteration \
  --output results/learning/training-iteration
```

## Change 1: compute duration

In `examples/training-iteration/experiment.json`, change
`compute_phase_us` from `100` to `200`.

The demonstration has two compute nodes. Increasing each by 100 us should add
approximately 200 us to `jct_us`. The AllReduce portion should remain the same.

## Change 2: message size

Restore `compute_phase_us` to `100`, then change
`message_bytes_per_rank` from `1048576` (1 MiB) to `2097152` (2 MiB).

The network must carry more data, so the AllReduce and iteration times should
increase while configured compute time remains 200 us.

## Change 3: network capacity

Restore the message size to `1048576`. Change `bandwidth` in `network.yml`
from `50.0` to `25.0`, and change the matching `bandwidth_GBps` metadata in
`experiment.json` to `25.0`.

Compute work remains fixed. Lower network capacity should increase AllReduce
time. The runner requires the two bandwidth values to match so a result cannot
be labeled with the wrong configuration.

Restore the starting inputs when finished:

```sh
git restore examples/training-iteration
```

Continue to [Measure the isolated-job baseline](isolated-baseline.md).
