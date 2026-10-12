# Scale to the multi-job contention experiment

## What changes from the learning example

The research experiment expands the physical topology from 4 to 64 endpoints,
uses 16-MiB messages, and activates up to 16 independent four-GPU jobs.

Open `examples/collective-contention/experiment.json`:

```json
"topology_npus": 64,
"maximum_jobs": 16,
"gpus_per_job": 4,
"job_counts": [1, 2, 4, 8, 16],
"message_bytes_per_rank": 16777216
```

`build_groups` in `scripts/run_collective_contention.py` gives every job four
strided ranks. Job 1 uses `[0, 16, 32, 48]`, job 2 uses `[1, 17, 33, 49]`, and
so on. Their logical Ring AllReduces traverse shared portions of the physical
Ring, creating contention when communication overlaps.

## Run the sweep

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config examples/collective-contention \
  --scenarios contention \
  --output results/learning/collective-contention
```

Open:

```text
results/learning/collective-contention/contention_summary.csv
results/learning/collective-contention/per_job_summary.csv
results/learning/collective-contention/contention-slowdown.svg
```

The runner includes a matched one-job baseline automatically. The checked-in
research evidence shows little slowdown through four jobs, about `1.844x` mean
slowdown at eight jobs, and about `3.599x` at sixteen jobs.

This demonstrates contention in the constructed analytical Ring. It does not
demonstrate a new scheduler. Packet queues, loss, measured link utilization,
HPCC, and possible MLTCP evaluation require the later ns-3 work.

Continue to [Understand the experiment runner](how-the-code-works.md).
