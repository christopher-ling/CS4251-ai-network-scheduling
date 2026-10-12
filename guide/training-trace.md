# Build and change one training trace

## What this lesson teaches

A **trace** is ASTRA-sim's to-do list for each simulated GPU. You will change
that to-do list through JSON, run it, and inspect a readable preview of the
binary Chakra trace that ASTRA-sim receives.

## 1. Read the workload inputs

Open `guide/workspace/experiment.json` in VS Code. Find:

```json
"compute_phase_us": 100,
"iteration_demo_count": 1,
"message_bytes_per_rank": 16777216
```

These values mean:

- each compute operation lasts 100 simulated microseconds;
- the demonstration contains one compute/AllReduce iteration;
- each of the four ranks contributes 16 MiB to AllReduce.

The trace ends with one final compute phase, so the operation sequence is:

```text
compute 100 us -> AllReduce 16 MiB/rank -> final compute 100 us
```

## 2. Run the starting version

Use **Cmd+Shift+P > Tasks: Run Task > Tutorial: Run training trace**.

When it finishes, use the VS Code Explorer to open:

```text
results/onboarding/training-trace/training_iteration/trace_preview.json
```

Read the first job:

- `simulated_gpu_ranks` lists the four participants;
- every operation waits for the preceding operation;
- `AllReduce` has no fixed duration in the trace because ASTRA-sim calculates
  its duration from the collective and network configurations.

Then open `results/onboarding/training-trace/per_job_summary.csv`. The `jct_us`
cell is the simulated completion time. It should be about `2187.534` us with
the starting inputs.

## 3. Edit the trace instead of copying another command

Return to `guide/workspace/experiment.json` and change:

```json
"compute_phase_us": 200
```

Before running, make a prediction: there are two compute operations, and each
became 100 us longer, so JCT should grow by about 200 us. Run **Tutorial: Run
training trace** again and compare `jct_us` in the CSV.

Now change:

```json
"message_bytes_per_rank": 8388608
```

This is 8 MiB. Predict whether AllReduce and JCT should become shorter or
longer, run the same task, and inspect `trace_preview.json` and the CSV again.

## 4. Explain what happened

You edited a workload description. The Python runner converted it into one
binary Chakra `.et` trace per simulated rank. ASTRA-sim replayed each rank's
dependencies and used the system and network inputs to calculate the AllReduce
time. The generated `trace_preview.json` is for people; ASTRA-sim reads the
binary `.et` files.

Use VS Code's Source Control panel to discard your changes to
`guide/workspace/experiment.json`, returning to 100 us and 16777216 bytes.
Then continue to [Measure one job and change the network](isolated-baseline.md).
