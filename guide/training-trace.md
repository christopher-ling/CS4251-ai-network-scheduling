# Run a four-GPU training iteration

## What you are proving

This experiment verifies the smallest training sequence needed by the project:

```text
four GPUs compute -> all four run AllReduce -> the next compute begins
```

The example has exactly four endpoints, so it produces four workload traces.
Every endpoint participates in the same job.

## Read the workload description

Open `examples/training-iteration/experiment.json` and find:

```json
"topology_npus": 4,
"gpus_per_job": 4,
"compute_phase_us": 100,
"iteration_demo_count": 1,
"message_bytes_per_rank": 1048576
```

The message is 1 MiB per rank. The generated operation order is:

```text
compute 100 us -> AllReduce 1 MiB/rank -> final compute 100 us
```

## Run it

From the team repository, run:

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config examples/training-iteration \
  --scenarios iteration \
  --output results/learning/training-iteration
```

The project runner generates the Chakra traces and then launches the compiled
`AstraSim_Analytical_Congestion_Aware` executable. Open:

```text
results/learning/training-iteration/training_iteration/trace_preview.json
results/learning/training-iteration/training_iteration/command.json
results/learning/training-iteration/per_job_summary.csv
```

Use the files in this order:

1. `trace_preview.json` shows the operation order for each of the four ranks.
2. `command.json` shows every file passed to the ASTRA-sim executable.
3. `per_job_summary.csv` shows the resulting simulated time.

The `.et` files are binary protobuf traces consumed by ASTRA-sim. The preview
exists so you can understand their contents without decoding binary data.

With the starting inputs, the reference row reports:

| Measurement | Value |
|---|---:|
| Configured compute in the complete trace | 200 us |
| AllReduce communication and waiting | 29.8 us |
| Compute-plus-AllReduce iteration | 129.8 us |
| Complete trace including final compute | 229.8 us |

## Key Questions and Findings

### How is computation represented?

The runner creates a Chakra `COMP_NODE`. `compute_phase_us` becomes the node's
`duration_micros`. With `roofline-enabled` set to `0`, the configured duration
is replayed directly.

### When does AllReduce begin?

The AllReduce node lists the preceding compute node in `data_deps`. It becomes
ready when that compute node completes. ASTRA-sim then uses the system and
network layers to simulate the collective.

### What determines communication size?

`message_bytes_per_rank` becomes the AllReduce node's `comm_size`. The starting
example uses 1,048,576 bytes, or 1 MiB, for each participating rank.

### How long does one iteration take?

The starting `mean_iteration_us` is `129.8 us`: 100 us of compute plus 29.8 us
of modeled AllReduce communication and waiting. `jct_us` is `229.8 us` because
the complete demonstration also contains the 100-us final compute node that
represents the beginning of the next iteration.

Continue to [Controlled changes](controlled-changes.md).
