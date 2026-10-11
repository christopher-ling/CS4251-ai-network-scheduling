# Start here: ASTRA-sim in one lab

## What the simulator actually does

Imagine a pretend stopwatch for 16 pretend workers. The trace says what each worker does next. The system configuration decides how to implement its communication. The network model decides how long each message takes and whether it waits behind another message. When an operation finishes, dependent operations can start. The program jumps between simulated events and reports the final simulated time.

This lab does not train a model, compute numerical gradients, require 16 physical GPUs, or send real AllReduce traffic through your laptop network. It models operation timing. In the compute-replay lab, a compute node simply advances simulated time by its specified duration.

## What you will learn

1. Reproduce the single-AllReduce bandwidth comparison.
2. Read a trace, collective configuration, and connection map.
3. Run compute–AllReduce dependencies.
4. Compare independent jobs alone and together on shared routes.

## Before starting

Install Git and Docker Desktop (on a Mac) or Docker Engine (on Linux). Start Docker and confirm `docker info` has a Server section. Allow several GB of disk space; building dependencies can take minutes. This setup was exercised on Christopher's M1 Mac. Other host platforms have not been tested by this team.

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

The image supplies Linux and dependencies. The two mounts make your simulator and team files visible inside it. The commit pin fixes the simulator source and its submodules. A clean full rebuild was not repeated for this documentation; Christopher's original build succeeded at this commit. Fresh containers and the launch scripts were verified against that built image.

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

## Explain before moving on

Open `configs/Ring_16npus.yml`: the 16 endpoints form a bidirectional physical ring, with 50 GB/s links and configured latency 500 ns. Open `configs/Ring_4chunks.json`: ring AllReduce is selected, with four preferred data splits and one active chunk per dimension. The trace is one collective with `comm_size = 1048576` bytes (1 MiB), not a whole model-training run. Each rank has its own trace file; the launch command supplies their common prefix.

Ask: Did capacity change, or did workload change? Why do all workers get the AllReduce result? Why is this not evidence of a new scheduler?

## Run the next experiments

Inside the same container:

```sh
cd /app/team
python3 scripts/run_learning_experiments.py --astra /app/astra-sim
```

This generates traces, runs eight small scenarios, checks all 16 endpoints finish, and saves configurations, logs, version records, trace inspection, and `results/learning/summary.csv`. Generated binary traces are ignored by Git because the script reproduces them.

Read [the training-cycle and contention lab](02-training-and-contention.md) to interpret the results. Several results correspond to inactive endpoints that finish quickly; the summary reports only active job groups and takes the maximum completion time over each group's members.

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

The next research task is a live collective-admission scheduler. Existing LIFO/chunk settings are upstream behavior, not the group's new scheduler. Scheduling policy comparisons must keep workload, rank placement, routing, capacity, collective algorithm, and chunk settings fixed and count all scheduling delay.
