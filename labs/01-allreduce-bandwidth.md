# Lab 1: AllReduce bandwidth experiment

## Purpose and measured result

Christopher ran this experiment on October 11, 2026, using an M1 Mac, Docker, and ASTRA-sim's congestion-aware analytical backend. Both runs reported completion for all 16 simulated workers (IDs 0–15).

| Configured link bandwidth | Reported completion time |
|---|---:|
| 50 GB/s | 99,640 cycles |
| 25 GB/s | 136,240 cycles |

Halving bandwidth increased completion time by 36.7%. Source inspection verified a 1 ns tick for this pinned analytical setup; the times equal 99.64 and 136.24 microseconds. These values describe the supplied collective microbenchmark, not a complete training job or multi-job experiment.

## Vocabulary and inputs

- AllReduce: combines participating workers' values and returns the combined result to each.
- Workload: execution traces describing what operations happen. The example folder is labeled `16npus_1MB`; decoding confirms 1048576 bytes (1 MiB) per rank.
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

Start with [the complete quickstart](00-quickstart.md). The recorded simulator commit is `4ce9ecfe746a3ee5fe47559a11d91644d641fa7f`; submodule records are in `results/`. The Docker image and analytical backend must be built. Run the commands below inside the container at `/app/astra-sim`, with the source mounted from the host. The upstream README is separate from this team lab; do not replace it.

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

Continue to [Lab 2](02-training-and-contention.md) for verified compute–communication chains and separate jobs sharing physical links.
