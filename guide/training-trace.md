# Create and change a training trace

## Goal

Learn how the project describes GPU compute and AllReduce, then change that
description and observe the simulated completion time.

## Read the inputs and code

Open `guide/workspace/experiment.json` and find:

```json
"compute_phase_us": 100,
"iteration_demo_count": 1,
"message_bytes_per_rank": 16777216
```

This describes one iteration with 100 microseconds of compute, one 16-MiB
AllReduce per rank, and a final 100-microsecond compute operation:

```text
compute -> AllReduce -> final compute
```

Open `scripts/run_collective_contention.py` and find `write_traces`. This
function creates each compute and collective node. The `data_deps` field makes
each operation wait for the preceding node. For an AllReduce node, the code
sets:

```text
comm_type = ALL_REDUCE
comm_size = message_bytes_per_rank
pg_name   = this job's communicator-group ID
```

The code writes one binary Chakra `.et` trace per simulated rank.

## Run the one-iteration simulation

From the team repository, run:

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config guide/workspace \
  --scenarios iteration \
  --output results/onboarding/training-trace
```

The options mean:

- `--astra` tells the runner where the simulator is mounted;
- `--config` selects the editable tutorial inputs;
- `--scenarios iteration` requests the one-iteration demonstration;
- `--output` selects the generated-results directory.

Open these generated files:

```text
results/onboarding/training-trace/training_iteration/trace_preview.json
results/onboarding/training-trace/training_iteration/command.json
results/onboarding/training-trace/per_job_summary.csv
```

`trace_preview.json` is the readable version of the binary trace.
`command.json` records the exact ASTRA-sim binary and input files used.
`per_job_summary.csv` contains JCT. The starting JCT should be about
`2187.534` simulated microseconds.

## Answers to the methodology's Section 1 questions

### 1. How is computation represented?

Computation is a Chakra `COMP_NODE`. The runner reads `compute_phase_us` from
`experiment.json` and writes that value into the node's `duration_micros`
field. Because `roofline-enabled` is `0` in `system_ring.json`, this experiment
replays the configured compute duration rather than calculating it from a
hardware performance model.

### 2. When does the AllReduce begin?

The AllReduce becomes ready only after the preceding compute node completes.
`write_traces` adds the compute node's ID to the AllReduce node's `data_deps`.
After that dependency is satisfied, ASTRA-sim's system layer decomposes the
collective into network operations. Under contention, ready communication may
still wait for the modeled network resources.

### 3. What determines the communication size?

`message_bytes_per_rank` in `experiment.json` determines it. The starting
value, `16777216`, is 16 MiB. `write_traces` stores it as the collective node's
`comm_size` attribute for every participating rank. This is the configured
message size per rank, not a claim that the total bytes carried across all
physical links equal 16 MiB.

### 4. How long does one complete training iteration take?

The recorded uncontended iteration time is `2087.534 us`: `100 us` of compute
plus `1987.534 us` of modeled AllReduce communication and waiting. The complete
demonstration trace finishes at `2187.534 us` because it includes another
`100 us` compute node representing the beginning of the next iteration. These
values appear as `mean_iteration_us`, `mean_allreduce_and_wait_us`, and `jct_us`
in `per_job_summary.csv`.

## Change the workload

Change `compute_phase_us` from `100` to `200`. There are two compute nodes, so
predict how much JCT should increase. Run the same command and inspect the CSV.

Then change `message_bytes_per_rank` from `16777216` to `8388608` (8 MiB).
Predict whether AllReduce becomes faster or slower, rerun, and compare JCT.

Restore the practice input when finished:

```sh
git restore guide/workspace/experiment.json
```

Continue to [Run one job and change the network](isolated-baseline.md).
