# Architecture

## Scope boundary

The project assumes that jobs are already running and that GPU placement has
already occurred. The scheduler controls communication after an AllReduce
becomes ready. It does not decide which machines receive a training job.

## Simulation layers

```text
Chakra execution traces
  compute nodes, collective nodes, dependencies, communicator groups
                          |
                          v
ASTRA-sim system layer
  collective decomposition and scheduling hooks
                          |
                          v
Network backend
  analytical: fast chunk-level contention validation
  ns-3: packets, queues, loss, telemetry, congestion control
                          |
                          v
Experiment analysis
  JCT, iteration time, slowdown, fairness, utilization, queueing
```

The analytical backend establishes workload correctness and controlled
contention. The ns-3 backend is required for claims involving HPCC, MLTCP,
packet loss, retransmissions, switch queues, or measured link utilization.

## Scheduling interface

The planned scheduling decision occurs between collective readiness and
communication launch:

```text
collective ready
      |
observe demand, path state, waiting time, and job progress
      |
admit now / delay / prioritize / rate-limit
      |
collective communication
```

The first policy baselines are immediate admission, FIFO collective admission,
and size-aware admission with aging. The proposed scheduler will add runtime
contention information while preserving an aging mechanism to prevent
starvation.

## Comparison discipline

Scheduling and congestion control are independent experimental axes:

- Scheduler evaluation fixes the transport configuration.
- Congestion-control evaluation fixes collective admission behavior.
- Combined experiments are reported only after both components have isolated
  baselines.
