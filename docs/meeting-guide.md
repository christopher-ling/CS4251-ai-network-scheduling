# Explain the work at the meeting

## What ASTRA-sim did

ASTRA-sim read a to-do list for each simulated worker. The list specified compute operations and AllReduce exchanges. It modeled how exchanges travel through configured links and wait in queues. When an operation finished, dependent work could start. It reported simulated elapsed time.

The original microbenchmark had one AllReduce operation and no training computation. The new synthetic cycle has repeated compute and communication with explicit dependencies. Neither run trained an actual AI model or computed real gradients.

## What we learned

1. The Docker and simulator setup works on the M1.
2. Halving bandwidth increased the original AllReduce timing by 36.7%.
3. Synthetic compute–AllReduce chains have the expected dependency timing.
4. Explicit independent jobs can share routes in one simulation; in the stress case their completion time increased by 76.8% compared with their matching isolated runs.
5. A switch control had no shared-run slowdown for disjoint endpoints.
6. A coordinated admission prototype works, including scheduler waiting. FIFO can be a weak baseline; size/aging helped substantially against FIFO but barely against immediate admission in the tested heterogeneous case.

## How this answers the teammate's request

The methodology is reflected in three labs and a complete installation quickstart. The README explains jargon. The repository includes launchers, trace generation, exact input descriptions, saved logs, and version records. The team can now reproduce and discuss the same scenarios instead of independently inventing configurations.

## Decisions still needed from the group

Choose a network-state signal and a specific algorithm gap grounded in related work. Agree on representative workloads, arrival patterns, and a more realistic bottleneck topology. Decide whether the current analytical queue model is sufficient or ns-3 is required for the claims. Do not present the teaching size/aging policy as a new telemetry-aware algorithm.

## A short presentation

“Our repository now has an ASTRA-sim quickstart and three labs. We verified a bandwidth experiment, a synthetic training cycle, and two independent jobs sharing ring paths. We also tested optional coordinated admission policies. The infrastructure works, but the final congestion-aware policy and broader evaluation remain research work.”
