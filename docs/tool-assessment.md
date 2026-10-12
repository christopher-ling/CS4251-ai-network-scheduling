# ASTRA-sim fit and evaluation scope

## What has been demonstrated

At simulator commit `4ce9ecfe746a3ee5fe47559a11d91644d641fa7f`, the analytical backend supports compute replay dependencies, explicit independent communicator groups, and shared ring-path contention. The collective-contention runner was exercised against a clean pinned checkout in the project's Docker environment.

ASTRA-sim is a suitable tool for this narrowed, synthetic communication-timing study. Workload generation and attribution are now explicit. Real training behavior still requires validated trace selection; this initial model does not establish representativeness.

## Verified units and trace semantics

`astra-sim/common/Common.hh` sets `CLOCK_PERIOD = 1` ns and frequency 1 GHz. `CommonNetworkApi::sim_get_time()` returns nanoseconds, and `Sys::boostedTick()` divides that time by the clock period. Therefore the printed cycles in this analytical setup correspond to nanoseconds.

Decoding the supplied rank-0 AllReduce trace gave `comm_size = 1048576` bytes: 1 MiB. The label `1MB` in the example path is not an assertion that the total on-wire collective traffic is only 1 MiB. The operation is represented by metadata and message sizes, not actual numerical gradients.

`Workload::issue_replay()` converts `duration_micros` to nanoseconds. With roofline disabled, compute is duration replay. `Workload::initialize_comm_groups()` reads a JSON mapping of nonzero group IDs to rank arrays. `extract_comm_group()` uses the trace's `pg_name`. Group 0/empty is reserved for all ranks.

## Modeling constraints

This pinned congestion-aware backend constructs one-dimensional Ring, Switch, or FullyConnected topologies. Its helper rejects multidimensional configurations. It models per-link chunk queueing; this study does not measure packet loss, retransmissions, transport congestion control, switch buffers, or actual link telemetry. A realistic leaf–spine evaluation needs another supported topology implementation or backend, likely the appropriate ns-3 integration.

Use the ring as an initial shared-path stress topology and the switch as a control. Do not claim this exhausts the professor's topology request. Add another relevant bottleneck topology when the required backend is qualified.

## Concrete next evaluation

- Workloads: fixed 3-iteration compute/AllReduce chains; 1 and 16 MiB payloads; equal and heterogeneous pairs; later vary compute periods, arrival offsets, and number of jobs.
- Topologies: verified bidirectional ring stress case and nonblocking switch control; later an explicitly constrained fabric.
- Metrics: mean/maximum fixed-work JCT, makespan, per-job slowdown versus its matching isolated run, collective admission wait, service time, decision count.
- Baselines: immediate readiness admission and clearly implemented coordinated FIFO admission.
- Proposed prototype: smaller ready collectives first with aging; same single-slot limit as FIFO. This demonstrates policy plumbing, not novelty or link awareness.

Hold chunk count, capacity, placement, routes, compute work, and collective algorithm fixed across policy comparisons. Separate experiments varying those inputs are sensitivity studies.

## Remaining research gap

The group still must select a network-state signal, design a contention-aware policy, establish a literature-grounded gap, and evaluate more than one selected stress case. Admission priority alone is not a demonstrated novel contribution. Confirm full titles and mechanisms for FORESIGHT, PACE, HPCC, and Gsched before claiming implementation or comparison. The unidentified Gupta et al. citation remains unresolved.
