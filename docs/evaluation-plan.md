# Evaluation plan

## Research questions

1. At what concurrency does collective contention materially increase JCT?
2. How do immediate, FIFO, and size-aware collective scheduling differ under a
   fixed transport?
3. How do default congestion control, HPCC, and MLTCP differ under fixed
   collective admission?
4. Does combining runtime network state with job-level information improve JCT
   without unacceptable tail slowdown or unfairness?

## Workloads

The initial synthetic trace fixes four GPUs per job and repeats compute followed
by AllReduce. The evaluation will add three communication intensities by varying
compute duration and message size, plus homogeneous and mixed job sets.

Arrival patterns:

- simultaneous arrivals for maximum overlap;
- staggered arrivals for transient contention;
- mixed short and long jobs for starvation and fairness analysis.

## Topologies

- Analytical 64-NPU Ring for fast shared-path stress testing.
- ns-3 leaf-spine or fat-tree with an explicit oversubscribed bottleneck for
  packet-level policy evaluation.
- One additional topology or oversubscription ratio for robustness.

The logical collective remains Ring AllReduce during the primary comparison.

## Baselines

Scheduling baselines:

- immediate admission;
- FIFO admission;
- size-aware admission with aging.

Transport baselines:

- the selected default ns-3 transport or DCQCN;
- HPCC;
- MLTCP if the implementation passes its feasibility and validation gate.

## Metrics

Application and scheduling metrics:

- collective completion time;
- training iteration time;
- mean, median, and p95 JCT;
- makespan;
- per-job slowdown against matched isolated execution;
- Jain fairness over completion rate;
- scheduling wait and decision overhead.

Packet-level metrics from ns-3:

- link utilization;
- queue occupancy;
- packet loss and retransmissions;
- transport rate or congestion-window behavior.

## Controlled variables

Within a policy comparison, hold topology, routing, placement, GPU count,
collective algorithm, message sizes, compute durations, iterations, arrivals,
and random seeds fixed. Change one policy axis at a time.

## Claim limits

The analytical backend's completion output is not direct link-utilization
telemetry. Synthetic workloads establish controlled behavior, not production
representativeness. General claims require packet-level results, multiple
workloads, a second topology condition, and repeated trials where randomness is
present.
