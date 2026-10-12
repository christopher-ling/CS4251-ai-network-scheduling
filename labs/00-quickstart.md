# Start here: ASTRA-sim in one lab

## Overview

ASTRA-sim consumes per-rank execution traces and models operation dependencies, collective execution, and network timing. The workload layer releases eligible operations, the system layer decomposes collectives into transfers, and the network backend computes transfer progress and queueing. Completion events release dependent operations.

These experiments model execution timing rather than numerical model training. Compute nodes in replay mode use specified durations. Physical accelerator hardware is not required.

## Objectives

- Reproduce the single-AllReduce bandwidth comparison.
- Identify workload, system, and network inputs.
- Model dependent compute and collective operations.
- Compare independent jobs on shared and nonshared routes.

## Prerequisites

Install Git and Docker Desktop (on a Mac) or Docker Engine (on Linux). Start Docker and confirm `docker info` has a Server section. Allow several GB of disk space; building dependencies can take minutes. Verified host platform: Apple Silicon M1 with Docker Desktop. Other host platforms have not been tested.

Use a new parent directory with two sibling checkouts. Commands in this section run in your normal host terminal, not inside Docker.

```sh
mkdir -p "$HOME/Documents/cs4251-lab"
cd "$HOME/Documents/cs4251-lab"
git clone https://github.com/christopher-ling/CS4251-ai-network-scheduling.git
git clone https://github.com/astra-sim/astra-sim.git
cd astra-sim
git checkout 4ce9ecfe746a3ee5fe47559a11d91644d641fa7f
git submodule update --init --recursive
docker build -t cs4251-astra:local -f Dockerfile .
docker run --rm -it \
  -v "$PWD":/app/astra-sim \
  -v "$PWD/../CS4251-ai-network-scheduling":/app/team \
  -w /app/astra-sim cs4251-astra:local bash
```

The image supplies Linux and dependencies. The two mounts make your simulator and team files visible inside it. The commit pin fixes the simulator source and its submodules. A clean full rebuild was not repeated for this documentation; The original build succeeded at this commit. Fresh containers and the launch scripts were verified against that built image.

## Inside Docker

Your prompt now starts with `root@...`. Run:

```sh
./build/astra_analytical/build.sh
bash /app/team/scripts/run_bandwidth_lab.sh /app/astra-sim
```

The second command uses the team's saved configs, validates completion of all 16 ranks, and writes logs into the mounted team results folder.

Expected reference completion times:

| Capacity | Simulated time |
|---|---:|
| 50 GB/s | 99,640 ns = 99.64 microseconds |
| 25 GB/s | 136,240 ns = 136.24 microseconds |

The program labels its ticks “cycles”; in this pinned analytical configuration, one tick is 1 ns. Do not generalize that conversion to arbitrary configurations or backends.

## Inspect the inputs

Open `configs/Ring_16npus.yml`: the 16 endpoints form a bidirectional physical ring, with 50 GB/s links and configured latency 500 ns. Open `configs/Ring_4chunks.json`: ring AllReduce is selected, with four preferred data splits and one active chunk per dimension. The trace is one collective with `comm_size = 1048576` bytes (1 MiB), not a whole model-training run. Each rank has its own trace file; the launch command supplies their common prefix.

Distinguish collective payload, link capacity, collective algorithm, and physical topology. The bandwidth comparison holds the workload fixed; it is not a scheduling-policy comparison. See [Development workflow](../docs/development-workflow.md) for an editor-based inspection exercise.

## Run methodology Sections 1-3

Inside the same container:

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --output results/sections-1-3
```

This generates traces, runs the one-iteration example, the single-job baseline,
and the 1/2/4/8/16-job sweep. It checks all 64 endpoints finish and saves exact
inputs, commands, raw logs, version records, CSV summaries, and a chart.
Generated binary traces are ignored by Git because the script reproduces them.

Read the [Sections 1-3 tutorial](sections-1-3/README.md) to interpret the
results. Inactive endpoints finish quickly; the summaries report only active
job groups and use the maximum completion time among each job's four ranks.

## Stop and resume

Type `exit` to leave the disposable container. Files under `/app/astra-sim` and `/app/team` survive because they are mounted host folders. To resume, go to your simulator directory in the host terminal and repeat the `docker run` command. There is no need to rebuild the image unless dependencies change.

## Troubleshooting

- No Docker Server: start Docker Desktop and wait for the service to be ready.
- Missing executable: compile inside Docker; inspect the first actual build error.
- Python schema import fails: verify the analytical build generated the schema in this pinned checkout and that `--astra` points to it.
- Missing paths: verify both mounts and that host folders are siblings.
- Different timings: compare simulator/submodule versions, trace payload, configs, and active-chunk count before interpreting the difference.
- A failed run: preserve its log; the scripts fail rather than accepting an incomplete set of workers.

## What comes after this lab

Experiment 3 provides an optional admission prototype. The next research task is a congestion-aware policy informed by a defined network-state signal. Existing LIFO/chunk settings are upstream behavior, not the group's new scheduler. Scheduling policy comparisons must keep workload, rank placement, routing, capacity, collective algorithm, and chunk settings fixed and count all scheduling delay.
