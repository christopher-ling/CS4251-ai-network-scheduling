# Create and change a training trace

## Goal

Learn how the project describes GPU compute and AllReduce, then change that
description and observe the simulated completion time.

The practical purpose is to verify that ASTRA-sim can represent the smallest
training sequence required by this project:

```text
four GPUs compute -> the four GPUs run AllReduce -> the next compute starts
```

Completing this experiment gives the project a known working workload before
multiple jobs and network contention are introduced. It also answers where
compute time, communication size, operation order, and iteration time come
from. You do not need to read the binary `.et` files individually.

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

### Why are there 64 `workload.*.et` files?

The physical test topology contains 64 simulated endpoints, so ASTRA-sim
requires one trace file for every endpoint. This one-job experiment activates
four ranks: `[0, 16, 32, 48]`. Those four ranks perform the training sequence.
The remaining endpoint traces contain a one-microsecond inactive operation.
Keeping the physical 64-endpoint topology fixed makes the later 1-, 2-, 4-,
8-, and 16-job results comparable.

### How to read the result row

The initial `training_iteration` row means:

| CSV column | Starting value | Meaning |
|---|---:|---|
| `job_count` | 1 | One training job is active |
| `job_id` | 1 | This row reports job 1 |
| `gpus_per_job` | 4 | Four simulated GPU ranks participate |
| `iterations` | 1 | One compute/AllReduce iteration is measured |
| `message_bytes_per_rank` | 16777216 | Each rank's AllReduce message is 16 MiB |
| `compute_total_us` | 200 | Two 100-us compute operations appear in the complete demo trace |
| `completion_ns` | 2187534 | The job's final rank completes at this simulated nanosecond |
| `jct_us` | 2187.534 | Complete demo-trace time in microseconds |
| `communication_and_wait_us` | 1987.534 | JCT after subtracting configured compute time |
| `mean_iteration_us` | 2087.534 | Compute plus AllReduce, excluding the final next-iteration compute |

The empty `slowdown_vs_single_job` cell is expected. This run contains only
the training-iteration demonstration; slowdown is calculated later using the
matched baseline and concurrent-job cases.

At this point you have shown that the trace dependency works, four ranks
participate in one Ring AllReduce, and ASTRA-sim produces a simulated iteration
time. The edits in the next section show which parts of that time come from
workload choices rather than a hard-coded answer.

## Key Questions and Findings

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
