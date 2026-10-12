# Measure one job and change the network

## What this lesson teaches

An **isolated baseline** measures one job without competing jobs. Later, each
job's slowdown is calculated by dividing its contended completion time by this
baseline. You will also change link capacity and observe the effect without
changing the workload.

## 1. See the difference between workload, system, and network

Open these files side by side in VS Code:

| File | Setting to find | Meaning |
|---|---|---|
| `guide/workspace/experiment.json` | `measurement_iterations: 3` | Repeat compute and AllReduce three times |
| `guide/workspace/system_ring.json` | `all-reduce-implementation: ["ring"]` | Use the ring procedure for the exchange |
| `guide/workspace/network_64npu_ring.yml` | `bandwidth: [ 50.0 ]` | Each physical ring link carries 50 GB/s |

The **collective algorithm** and **network topology** are different. The ring
algorithm describes how ranks exchange pieces of data. The physical ring
describes which links are available to carry those exchanges.

## 2. Run the isolated baseline

Use **Tasks: Run Task > Tutorial: Run isolated baseline**. Open:

```text
results/onboarding/isolated-baseline/per_job_summary.csv
```

The starting JCT should be about `6362.602` us. The job performs three
AllReduces and four compute phases. `communication_and_wait_us` is JCT minus
configured compute time; it is not measured link utilization.

## 3. Reduce the network capacity

In `guide/workspace/network_64npu_ring.yml`, change:

```yaml
bandwidth: [ 25.0 ]  # GB/s
```

Also change the matching description in `guide/workspace/experiment.json`:

```json
"bandwidth_GBps": 25.0
```

The runner requires these two values to match so an experiment cannot be
reported with the wrong label. Predict the result: the compute work stays the
same, but communication over a half-capacity network should take longer.

Run **Tutorial: Run isolated baseline** again and compare `jct_us`. This is a
controlled experiment because bandwidth is the only modeled variable you
changed.

Discard both edits in VS Code Source Control before continuing to
[Create contention with several jobs](concurrent-contention.md).
