# Experiment 2: synthetic training cycles and shared-link contention

Run `python3 scripts/run_learning_experiments.py --astra /app/astra-sim` inside Docker from `/app/team`. See [the quickstart](00-quickstart.md) for installation and mounts.

## Compute-replay workload

The generated trace is a chain:

```text
compute 100 us → AllReduce → compute 100 us → AllReduce
→ compute 100 us → AllReduce → final compute 100 us
```

Each arrow is a dependency: the next operation must wait for the preceding one. There are three collectives and four compute phases, with the final phase representing dependent work after the third exchange. The script puts these operations into each rank's Chakra trace. Roofline modeling is disabled; compute replay uses the supplied duration rather than simulating numerical GPU arithmetic.

Reference results with one active chunk per dimension and a 1 MiB collective on all 16 workers:

| Bandwidth | Final completion | Check |
|---|---:|---|
| 50 GB/s | 698.920 us | 400 us compute + 3 × 99.640 us communication |
| 25 GB/s | 808.720 us | 400 us compute + 3 × 136.240 us communication |

These exact equalities verify the generated dependency chain's timing in this scenario. This is a synthetic fixed-work training-cycle model; it does not represent a profiled real model, its loss, optimizer, or accuracy convergence.

## Independent communicator groups

The experiment uses 16 physical endpoints on a bidirectional ring. Group A uses `[0,1,4,5,8,9,12,13]`; group B uses `[2,3,6,7,10,11,14,15]`. Group IDs 1 and 2 are explicit, nonzero communicator groups. Each group has its own AllReduce results; values are not mixed between jobs.

Both use three collectives of 16 MiB per rank, four 100-us compute phases, 50 GB/s links, configured latency 500 ns, and **four active chunks per dimension**. Each collective requests four preferred splits. This active-chunk setting differs from the original single-collective lab. It is held constant across all isolated and paired runs here.

The network uses shortest ring routes (clockwise on equal-distance ties). Example overlapping routes: A's 1 → 4 passes through 1 → 2 → 3 → 4; B's 3 → 6 passes through 3 → 4 → 5 → 6. Both need directed link 3 → 4. Other exchanges also share paths. Queue service is in-order in the analytical link model.

## Results and controls

| Network / scenario | Job A completion | Job B completion |
|---|---:|---:|
| Ring, A alone | 2.083140 ms | Inactive |
| Ring, B alone | Inactive | 2.083140 ms |
| Ring, both | 3.682600 ms | 3.682600 ms |
| Switch, A alone | 2.072875 ms | Inactive |
| Switch, B alone | Inactive | 2.072875 ms |
| Switch, both | 2.072875 ms | 2.072875 ms |

In the ring, sharing increased each job's completion time by about 76.8% (slowdown 1.768). In the modeled nonblocking switch, the disjoint groups use separate endpoint links and have no paired-run slowdown. Do not generalize that observation to an oversubscribed real switch fabric.

All jobs start at simulated time zero, so completion timestamps equal their fixed-work elapsed completion time. In isolated runs, the other group's endpoints contain an idle operation and finish quickly; they are not part of the active job's metric.

## Why earlier layouts showed little slowdown

Pilot runs with one active chunk showed no slowdown for even/odd or contiguous groups. The final eight-rank overlapping-path layout at one active chunk showed only about 0.0125% slowdown. Four active chunks increase concurrent offered traffic enough to produce a substantial shared-run effect. This is a sensitivity finding, not a reason to change settings between policy comparisons. The chosen scenario is a stress test, not proof of real-cluster prevalence.

## Inspect the evidence

- `results/learning/summary.csv`: per-job final timing.
- Each case's `description.json`: group membership, payload, compute and iteration settings.
- Each case's `network.yml` and `system.json`: exact simulation inputs.
- Each case's `run.log`: all 16 completed ranks.
- Each case's `command.json`: invocation from the verification container.
- `trace-inspection.json`: inspected supplied single-AllReduce trace.

Binary traces are reproducible and ignored by Git. Logs remain measured results; descriptions and generators expose the modeling assumptions.

## Next step

Read [Lab 3: scheduler prototype](03-admission-prototype.md). Existing ASTRA-sim LIFO and active-chunk settings are not the team's admission scheduler.
