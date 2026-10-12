# Editable collective-contention inputs

These are safe practice copies of the research inputs in
`configs/collective-contention/`. The learning commands read this folder, so
edits here do not change the recorded research configuration.

| File | What it controls |
|---|---|
| `experiment.json` | Jobs, GPUs per job, compute time, iteration count, and AllReduce message size |
| `network.yml` | Physical network shape, capacity, and link delay |
| `system.json` | The algorithm used to carry out collective communication |

`bandwidth_GBps` and `latency_ns` in `experiment.json` describe the experiment
and are checked against the values in the network YAML. When changing either
network value, edit both files so the runner can catch accidental mismatches.

Use your IDE's source-control interface or
`git restore examples/collective-contention` to return these files to the
starting values after an exercise.
