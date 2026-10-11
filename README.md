# CS4251: AI Network Scheduling

We are investigating how already-running distributed AI training jobs should share network resources. GPU assignments stay fixed; our proposed scheduler will control when collective communication proceeds.

## The idea in plain language

A training job uses several workers, often GPUs. Each worker computes suggested model changes called gradients. An AllReduce operation combines these values and returns the combined result to every participating worker. The workers update their model copies and repeat.

When independent jobs send data through the same limited-capacity links, their traffic can compete. We plan to test whether organizing communication can improve completion times while avoiding excessive waiting for individual jobs.

## Current progress

- Built the Docker environment and ASTRA-sim analytical backend on an M1 Mac.
- Ran the supplied AllGather example as an installation check.
- Ran a 16-worker ring AllReduce microbenchmark with the congestion-aware analytical backend.
- Compared 50 GB/s and 25 GB/s link bandwidth with workload, topology, latency, and system settings unchanged.
- Saved both AllReduce logs, input configurations, and simulator/submodule version records.

No new inter-job scheduler or multi-job contention experiment has been implemented yet.

## First measured experiment

| Configured link bandwidth | Reported AllReduce completion time |
|---|---:|
| 50 GB/s | 99,640 cycles |
| 25 GB/s | 136,240 cycles |

All 16 workers (IDs 0–15) reported completion at the listed time in each run. Halving bandwidth increased completion time by approximately 36.7%. These are simulated collective timings, not laptop execution time or full training-job JCT. We retain the output's “cycles” label pending verification of the source's time convention.

The workload folder is labeled `16npus_1MB`; the precise payload semantics remain to be inspected. The topology is a 16-endpoint ring with configured latency 500 ns. The system selects ring AllReduce and requests four dataset splits.

This experiment demonstrates bandwidth sensitivity. It does not demonstrate contention between independent jobs, packet loss, or improvement from a new scheduler.

## Reproduce the lab

Read [Lab 1: AllReduce bandwidth experiment](labs/01-allreduce-bandwidth.md).

Simulator commit used:

```text
4ce9ecfe746a3ee5fe47559a11d91644d641fa7f
```

The lab's prerequisites require the upstream simulator and a built analytical backend. Refer to the [official installation guide](https://astra-sim.github.io/astra-sim-docs/getting-started/setup.html) and [build instructions](https://astra-sim.github.io/astra-sim-docs/getting-started/build.html). This team repository contains experiment documentation and evidence; the simulator is maintained separately.

## Repository contents

- `labs/`: explanations and reproduction commands.
- `configs/`: copies of the network, system, and memory inputs used.
- `results/`: saved logs and exact simulator/submodule version records.

## Terms we use

| Term | Plain-language meaning |
|---|---|
| GPU | A processor suited to many parallel calculations. |
| Worker / rank | A participant in a distributed job; rank is an identifier within its group. |
| Gradient | Values describing suggested changes to model parameters. |
| AllReduce | Combines participants' values and returns the combined result to each. |
| Collective algorithm | A procedure implementing that exchange, such as ring AllReduce. |
| Workload / execution trace | A description of operations and dependencies for the simulator. |
| Chakra | The execution-trace format used here. |
| Topology | The map of network connections; distinct from the collective algorithm. |
| Bandwidth | Data-carrying capacity per unit time. GB/s means gigabytes per second. |
| Latency | A communication delay. ns means nanoseconds. |
| Contention | Transfers compete for the same limited network resource. |
| Backend | The component that models network behavior. |
| Microbenchmark | A small test isolating an operation. |
| Baseline | A specified reference policy or configuration for comparison. |
| Network scheduler | A policy controlling communication admission, order, priority, or rate. |
| JCT | Job completion time, including waiting imposed by scheduling. |

## Next milestones

1. Verify trace payload and time-unit interpretation; finish installation/reproduction documentation.
2. Represent a compute → AllReduce → dependent compute cycle and repeated iterations.
3. Represent independent jobs sharing physical links within ONE simulation; compare shared and isolated runs.
4. Establish explicit network-oblivious and FIFO admission baselines.
5. Add a communication admission policy and evaluate timing and fairness using identical scenarios.

Changing bandwidth is a learning experiment. Scheduling comparisons will hold capacity, placement, routing, and collective algorithm fixed. Any deliberate scheduler waiting must count toward completion time.

Upstream ASTRA-sim is available at [astra-sim/astra-sim](https://github.com/astra-sim/astra-sim). Copied upstream configuration files retain their upstream licensing obligations; see the simulator's LICENSE.
