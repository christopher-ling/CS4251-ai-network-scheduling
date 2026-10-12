# Editable tutorial inputs

These are safe practice copies of the research inputs in
`configs/collective-contention/`. The VS Code tutorial tasks read this folder,
so edits here do not change the recorded research configuration.

| File | What it controls |
|---|---|
| `experiment.json` | Jobs, GPUs per job, compute time, iteration count, and AllReduce message size |
| `network_64npu_ring.yml` | Physical network shape, capacity, and link delay |
| `system_ring.json` | The algorithm used to carry out collective communication |

`bandwidth_GBps` and `latency_ns` in `experiment.json` describe the experiment
and are checked against the values in the network YAML. When changing either
network value, edit both files so the runner can catch accidental mismatches.

Use **Source Control: Discard Changes** in VS Code to return these files to the
starting values after an exercise.
