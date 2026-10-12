# Project plan

## Deliverable 1: controlled analytical baseline

- Generate compute/AllReduce dependency traces.
- Establish a matched isolated-job completion time.
- Sweep 1, 2, 4, 8, and 16 concurrent jobs.
- Record exact inputs, simulator revisions, raw logs, and CSV summaries.
- Treat the analytical Ring as a stress topology rather than a production
  network model.

Exit criteria: all endpoints finish, workload inputs stay fixed across the
sweep, slowdown uses the matched isolated run, and the results are reproduced
from a clean pinned simulator checkout.

## Deliverable 2: packet-level backend qualification

- Build the ASTRA-sim ns-3 backend in a reproducible container.
- Define a small leaf-spine or fat-tree physical topology with a controlled
  bottleneck and Ring AllReduce as the logical collective.
- Reproduce an isolated job and a concurrent contention case.
- Export queue occupancy, utilization, packet loss, retransmissions, and flow
  completion information.

Exit criteria: overlapping jobs demonstrably share the intended bottleneck and
packet-level metrics can be attributed to each scenario.

## Deliverable 3: policy baselines

- Immediate admission: every ready collective launches.
- FIFO: collectives launch in readiness order.
- Size-aware with aging: shorter remaining communication receives priority,
  while waiting time prevents starvation.
- HPCC: reproduce the supported ns-3 implementation under fixed admission.
- MLTCP feasibility: identify the transport code path, iteration-byte signal,
  validation test, and implementation cost before committing to a full port.

Exit criteria: every policy uses identical workloads, topology, placement,
collective algorithm, and arrival pattern.

## Deliverable 4: proposed scheduler

Use network state and training progress to score ready collectives. Candidate
inputs are shared-path queue occupancy, estimated demand, collective size,
waiting time, and remaining job progress. Actions may include admission delay,
priority, or a rate cap.

Exit criteria: the policy has a precise algorithm description, bounded
decision overhead, starvation protection, and an ablation showing which input
signals affect the result.

## Deliverable 5: evaluation and report

- Run homogeneous and heterogeneous workloads.
- Test simultaneous and staggered arrivals.
- Report mean, median, and p95 JCT; slowdown; makespan; Jain fairness; network
  metrics; and scheduler overhead.
- Add one topology or collective robustness experiment.
- Update the report so every methodology claim points to configuration,
  implementation, and recorded evidence.

## Work sequence

1. Analytical baseline and repository foundation.
2. Separate ASTRA-sim onboarding branch for the team.
3. ns-3 backend qualification.
4. Scheduler baselines.
5. HPCC reproduction and MLTCP feasibility gate.
6. Proposed scheduler and ablations.
7. Robustness evaluation and report revision.
