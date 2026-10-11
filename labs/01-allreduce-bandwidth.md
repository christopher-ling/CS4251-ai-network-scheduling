# Experiment 1: AllReduce bandwidth sensitivity

## Purpose and measured result

The reference experiment was run on ASTRA-sim's congestion-aware analytical backend. Both runs reported completion for all 16 simulated workers (IDs 0–15).

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

## Reproduction

Use the checked-in launcher from the mounted team repository:

```sh
bash /app/team/scripts/run_bandwidth_lab.sh /app/astra-sim
```

This launcher reads the reference configuration copies under `/app/team/configs/`, validates completion for IDs 0–15, and writes logs to `/app/team/results/bandwidth_reproduced/`. It has been executed successfully in Docker.

The two network files differ only in bandwidth. Inspect them before launching:

```sh
diff -u /app/team/configs/Ring_16npus.yml /app/team/configs/Ring_16npus_half_bw.yml
```

Exit status 1 from `diff` is expected when a difference is found. The simulator invocations preserve the same workload, system, and memory inputs. See the launcher for the complete argument list.

## Configuration exercise

Open the two YAML files in an editor and identify the changed field. No C++ or Python changes are required for this experiment. For an additional case, create a separate copy with a different bandwidth and use it in a separate invocation, preserving the reference inputs and writing a separate log.

Record the capacity, latency, rank count, payload, and completion time. Distinguish simulated elapsed time from the host time needed to execute the simulator.

## Interpretation and limits

Lower capacity increased communication time. The total did not double because other timing contributions remain. This comparison establishes bandwidth sensitivity; it does not measure contention between independent jobs, packet loss, scheduler improvements, or training convergence. The system's existing LIFO setting is unchanged and is not a newly implemented inter-job scheduler.

## Record before sharing

Save the simulator commit, recursive submodule commits, Docker image identity, input files, commands, and logs. Example measurements are reproducible only with a matching setup; other versions may differ.

Continue to [Lab 2](02-training-and-contention.md) for verified compute–communication chains and separate jobs sharing physical links.
