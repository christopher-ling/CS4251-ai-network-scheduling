# Experiment review checklist

## Bandwidth experiment

Identify the workload, ring collective algorithm, physical topology, payload, and time units. Show the single changed field: bandwidth. Verify all 16 ranks finish. Explain the 36.7% increase as capacity sensitivity rather than scheduler performance.

## Training-cycle and contention experiment

Identify the three collectives, four compute phases, and their dependencies. Explain duration replay. Identify independent groups and shared routes. Compare each job against its matching isolated case. Explain the 76.8% ring slowdown, switch control, and fixed active-chunk setting.

## Admission prototype

Distinguish immediate admission, FIFO, and size priority with aging. Explain group coordination, the single global slot, and included waiting. Report mean JCT, makespan, and slowdown. The measured advantage is approximately 14.0% versus FIFO and 0.30% versus immediate admission in one scenario. Link telemetry and the final congestion-aware policy remain unimplemented.

## Reproducibility

Distinguish experiments personally reproduced by the presenter from repository reference results. Preserve versions, inputs, logs, and source changes. Review limitations before making real-system claims.

## Team decisions

Select a network-state signal, algorithmic gap, representative workloads, fairness criteria, and additional bottleneck topology. Determine whether analytical queueing is sufficient or another backend is needed. Confirm citations and baseline implementation scope.
