# Development workflow

## Activity and required changes

| Activity | Files involved | C++ changes | Rebuild |
|---|---|---|---|
| Run reference AllReduce | Existing traces and launcher | None | Initial build only |
| Change bandwidth | YAML network configuration | None | No |
| Change collective algorithm | Compatible JSON system configuration | None | No |
| Create workload/dependencies | Python generator and Chakra traces | None | Regenerate traces |
| Implement admission policy | `Workload.cc` and `Workload.hh` patch | Required | Required |

VS Code is an editor, not a simulator prerequisite. Tutorials can use it to inspect files, generate traces, or develop simulator behavior. Identify the activity before treating it as part of installation.

## Preparation for presenting

1. Reproduce Experiment 1 and inspect the two network configurations.
2. Reproduce Experiment 2 and inspect a generated workload description and summary.
3. Review Experiment 3's mechanism and assumptions. The prototype is optional for the introductory demonstration.
4. Distinguish personally reproduced results from previously recorded results.

Do not repeat installation when the image and compiled pinned simulator already exist.

## Editor inspection

Open the team repository with File → Open Folder in VS Code, or use another editor. Inspect these files in order:

- `configs/Ring_16npus.yml`: network capacity, latency, topology, and rank count.
- `configs/Ring_16npus_half_bw.yml`: the controlled bandwidth change.
- `configs/Ring_4chunks.json`: collective implementation and chunk parameters.
- `scripts/run_bandwidth_lab.sh`: executable and input arguments.
- `results/allreduce_50GBps.log`: completion messages.
- `scripts/run_learning_experiments.py`: workload generation and communicator groups.

Inspecting files does not require editing them. The baseline uses the checked-in inputs.

## Configuration exercise

Create a copy of `configs/Ring_16npus.yml` named `configs/Ring_16npus_custom.yml`. Open it and select a positive bandwidth, for example 30.0 GB/s. Keep the other fields fixed. Save it and run inside the mounted container:

```sh
mkdir -p /app/team/results/custom
/app/astra-sim/build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Aware \
  --workload-configuration=/app/astra-sim/examples/workload/microbenchmarks/all_reduce/16npus_1MB/all_reduce \
  --system-configuration=/app/team/configs/Ring_4chunks.json \
  --remote-memory-configuration=/app/team/configs/no_memory_expansion.json \
  --network-configuration=/app/team/configs/Ring_16npus_custom.yml \
  --logging-folder=/app/team/results/custom/logging
```

This optional case has no published reference timing. Verify all ranks finish and record the actual result separately. The intervention is a configuration value, not a change to the simulator algorithm.

## Trace-generation exercise

After Experiment 2, read `results/learning/training_cycle_50GBps/description.json` and the generator. The trace has three AllReduce phases, four 100-us compute phases, and explicit dependencies. Then read the independent-job group definitions for the shared-ring case.

The result descriptions record provenance; the launcher does not read them as inputs. Editing a description after a run does not change the workload. To change generated operations, modify generator parameters and rerun with a separate output directory.

## Scheduler development

The optional patch coordinates collective readiness across ranks, queues requests, and releases a global admission slot after all participants complete. This task requires C++ source changes and recompilation. The final project still needs a justified congestion-aware policy and network-state signal.
