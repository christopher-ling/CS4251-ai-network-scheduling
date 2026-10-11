# Terminology

| Term | Definition |
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

