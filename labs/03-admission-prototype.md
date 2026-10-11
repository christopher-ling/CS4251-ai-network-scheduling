# Lab 3: optional coordinated admission prototype

This is a teaching implementation, not a claimed novel congestion-aware scheduler. It adds a reversible patch at the point where a ready collective would otherwise launch. It does not change GPU placement, routing, workload dependencies, or the ring collective implementation.

## Policies

- `immediate`: original upstream issue behavior; no group admission gate.
- `fifo`: one global whole-collective slot, ordered by first-rank readiness and stable insertion order for ties.
- `size_aging`: the SAME single-slot constraint. Prefer requests waiting at least 200 us; among aged requests use FIFO. Otherwise prefer smaller per-rank payload, then FIFO. Aging is not a proven hard waiting bound.

The gate waits for all group members' matching operation before launching it on every rank. It frees the slot after all members complete. A 1 ns decision event batches same-time readiness and is counted in reported timing. Waiting stays within the active trace dependency and therefore counts in elapsed JCT.

The prototype observes ready payloads, request age, and whether its global slot is occupied. It does not observe link-utilization telemetry or per-link congestion. It serializes disjoint paths unnecessarily. A pressure-aware policy that admits nonconflicting collectives is future research, not implemented functionality.

## Apply and build

First follow [the quickstart](00-quickstart.md). Inside Docker, from a clean pinned simulator checkout:

```sh
cd /app/astra-sim
git apply --check /app/team/patches/collective-admission.patch
git apply /app/team/patches/collective-admission.patch
./build/astra_analytical/build.sh
cd /app/team
CS4251_RUN_POLICIES=1 python3 scripts/run_learning_experiments.py \
  --astra /app/astra-sim --output results/policy_experiments
```

Christopher's local checkout already has this patch applied. Do not apply it a second time there. The default/unset `CS4251_POLICY` retains immediate behavior. The generator passes an explicit policy for every run and writes the source diff beside the results.

## Supported teaching workload

This patch is intentionally limited to the generated traces: explicit nonzero, disjoint communication groups; identical collective node IDs and operation order across each group's ranks; one dependent collective at a time per rank; one simulator invocation per process. All participants must eventually reach the matching operation. It is not a general production scheduler and should not be enabled for arbitrary profiled traces.

## Measured comparison

Fixed bidirectional ring with the rank layout from Lab 2, 50 GB/s, 500 ns latency, four active chunks, three collectives and four 100-us compute phases. A uses 16 MiB per collective per rank; B uses 1 MiB. Both start at time zero; GPU assignments and all input configurations are fixed across policies.

| Policy | Large job A JCT (ms) | Small job B JCT (ms) | Mean JCT (ms) | Makespan (ms) |
|---|---:|---:|---:|---:|
| Immediate | 2.143530 | 1.517510 | 1.830520 | 2.143530 |
| FIFO | 2.103673 | 2.140574 | 2.122124 | 2.140574 |
| Size + aging | 2.140574 | 1.509584 | 1.825079 | 2.140574 |

Matching isolated reference: A 2.083140 ms, B 0.508480 ms. Maximum slowdown is 2.984 for immediate, 4.210 for FIFO, and 2.969 for size + aging. FIFO starts the large ready request first, increasing the small job's waiting.

Size + aging reduces mean JCT by about 14.0% versus FIFO, but only 0.30% versus immediate admission. This one deterministic synthetic case establishes that the policy is wired correctly and that FIFO can be a weak baseline. It does not establish general benefit or novelty. The policy can hurt other scenarios; streaming arrivals and starvation remain untested.

## Verification

The optional build succeeded. Immediate runs reproduce the unpatched reference timings. Each policy run reports all 16 endpoints finished. Logs show exactly six admitted collectives (three per group), six matching group completions, and no overlap between global slots. Admission wait equals start minus readiness; all waiting and the 1 ns decision delay remain in final completion time.

Read `CS4251 admit` and `CS4251 complete` lines in the saved logs, as well as `summary.csv` and `policy-summary.csv`. No packet-loss or queue-occupancy measurements are claimed.

## Restore upstream behavior

For ordinary experiments, leave `CS4251_POLICY` unset or use `immediate`. To remove the source change:

```sh
cd /app/astra-sim
git apply --reverse --check /app/team/patches/collective-admission.patch
git apply --reverse /app/team/patches/collective-admission.patch
./build/astra_analytical/build.sh
```

## Team design questions

Which actual network signal should drive admission? Should disjoint paths overlap? What telemetry delay and decision overhead should be modeled? How does the policy perform under arrival skew, many jobs, heterogeneous compute times, and low load? How does the proposed rule differ from the cited literature? Resolve these before promoting the teaching prototype to the project's proposed algorithm.
