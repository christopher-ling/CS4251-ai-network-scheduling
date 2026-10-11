# Lab 2: AllReduce bandwidth experiment

## Purpose and measured result

Christopher ran this experiment on October 11, 2026, using an M1 Mac, Docker, and ASTRA-sim's congestion-aware analytical backend. Both runs reported completion for all 16 simulated workers (IDs 0–15).

| Configured link bandwidth | Reported completion time |
|---|---:|
| 50 GB/s | 99,640 cycles |
| 25 GB/s | 136,240 cycles |

Halving bandwidth increased completion time by 36.7%. Preserve the log's label “cycles” until the checked-out source's time convention is verified. These values describe the supplied collective microbenchmark, not a complete training job or multi-job experiment.

## Vocabulary and inputs

- AllReduce: combines participating workers' values and returns the combined result to each.
- Workload: execution traces describing what operations happen. The example folder is labeled `16npus_1MB`; exact trace payload semantics still need inspection.
- System configuration: selects the ring collective implementation and requests four dataset splits/chunks.
- Network configuration: a 16-endpoint ring, configured 500 ns latency, and either 50 or 25 GB/s bandwidth.
- Backend: the simulator component modeling network behavior.
- GB/s: gigabytes per second, not gigabits per second.

Fixed inputs:

```text
examples/workload/microbenchmarks/all_reduce/16npus_1MB/all_reduce
examples/system/native_collectives/Ring_4chunks.json
examples/remote_memory/analytical/no_memory_expansion.json
```

The workload argument is a prefix; ASTRA-sim reads the corresponding `all_reduce.0.et` through `all_reduce.15.et` files. The workload chooses AllReduce; the system file also contains settings for other operations that this experiment does not request.

## Prerequisites

Use the same upstream source/submodule versions as Christopher's checkout (record still pending). The Docker image and analytical backend must be built. Run the commands below inside the container at `/app/astra-sim`, with the source mounted from the host. The upstream README is separate from this team lab; do not replace it.

## Prepare the changed input

```sh
cp examples/network/analytical/Ring_16npus.yml examples/network/analytical/Ring_16npus_half_bw.yml
sed -i 's/bandwidth: \[ 50.0 \]/bandwidth: [ 25.0 ]/' examples/network/analytical/Ring_16npus_half_bw.yml
cat examples/network/analytical/Ring_16npus_half_bw.yml
```

Confirm only bandwidth differs. This `sed` command is for the Linux container.

## Run both configurations and preserve logs

```sh
mkdir -p results
set -o pipefail
for bandwidth in 50 25; do
  network=examples/network/analytical/Ring_16npus.yml
  if [ "$bandwidth" = 25 ]; then
    network=examples/network/analytical/Ring_16npus_half_bw.yml
  fi
  ./build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Aware \
    --workload-configuration=examples/workload/microbenchmarks/all_reduce/16npus_1MB/all_reduce \
    --system-configuration=examples/system/native_collectives/Ring_4chunks.json \
    --remote-memory-configuration=examples/remote_memory/analytical/no_memory_expansion.json \
    --network-configuration="$network" \
    2>&1 | tee "results/allreduce_${bandwidth}GBps.log" || break
done
```

These invocations were verified individually by Christopher. The loop above packages them for convenience and has not been separately executed.

Inspect each log for all 16 IDs and completion times. Do not sum workers' times: they execute concurrently.

```sh
grep 'finished,' results/allreduce_50GBps.log
grep 'finished,' results/allreduce_25GBps.log
```

## Interpretation and limits

Lower capacity increased communication time. The total did not double because other timing contributions remain. This comparison establishes bandwidth sensitivity; it does not measure contention between independent jobs, packet loss, scheduler improvements, or training convergence. The system's existing LIFO setting is unchanged and is not a newly implemented inter-job scheduler.

## Record before sharing

Save the simulator commit, recursive submodule commits, Docker image identity, input files, commands, and logs. Example measurements are reproducible only with a matching setup; other versions may differ.

Next research milestone: compute–communication dependencies, followed by separate jobs sharing physical links in one simulation.
