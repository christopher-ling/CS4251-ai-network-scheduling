# Methodology traceability

This document maps the report's proposed work to concrete repository evidence.

| Proposed activity | Implementation or evidence | Status |
|---|---|---|
| Model compute followed by AllReduce | `scripts/run_collective_contention.py` | Implemented |
| Establish isolated Ring AllReduce baseline | `results/collective-contention/single_job_baseline/` | Implemented |
| Sweep concurrent jobs | `results/collective-contention/contention_summary.csv` | Implemented |
| Immediate network-oblivious behavior | Analytical runner uses immediate launch behavior | Implemented for baseline |
| FIFO collective scheduler | Planned scheduler module | Planned |
| HPCC evaluation | ASTRA-sim ns-3 backend qualification | Planned |
| MLTCP evaluation | Transport integration feasibility gate | Planned |
| Proposed congestion-aware scheduler | `src/scheduler/` | Planned |
| Robustness evaluation | Second topology and workload mix | Planned |

An activity becomes complete only when its implementation, configuration,
command, raw output, summarized metrics, and simulator revision are recorded.
