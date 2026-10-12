# Run one job and change the network

## Goal

Measure a single job without competing traffic, identify the collective and
network configurations, and test how link capacity affects completion time.

## Follow the three simulation layers

Open these files together:

| Layer | File | Important value |
|---|---|---|
| Workload | `guide/workspace/experiment.json` | `measurement_iterations: 3` |
| System/collective | `guide/workspace/system_ring.json` | `all-reduce-implementation: ["ring"]` |
| Network | `guide/workspace/network_64npu_ring.yml` | `bandwidth: [50.0]` GB/s |

The ring **collective algorithm** describes the order in which ranks exchange
data. The physical ring **network topology** describes the available links.
They are separate layers even though both use the word “ring” here.

In `run_case` inside `scripts/run_collective_contention.py`, find the `command`
list. It passes the generated workload, communicator groups, system JSON,
remote-memory JSON, and network YAML to the analytical ASTRA-sim executable.

## Run the isolated baseline

```sh
docker compose exec astra python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --config guide/workspace \
  --scenarios baseline \
  --output results/onboarding/isolated-baseline
```

Open `results/onboarding/isolated-baseline/per_job_summary.csv`. The initial
JCT should be about `6362.602` microseconds. The job contains three AllReduces
and four compute phases.

Also open the generated case directory. The runner copies `network.yml` and
`system.json` into it so a result remains connected to the exact inputs used.

## Change network capacity

In `guide/workspace/network_64npu_ring.yml`, change:

```yaml
bandwidth: [ 25.0 ]  # GB/s
```

Change the matching metadata in `guide/workspace/experiment.json`:

```json
"bandwidth_GBps": 25.0
```

The validation code requires these values to match, preventing a result from
being labeled with the wrong capacity. The compute work is unchanged, so
predict what halving bandwidth does to JCT. Rerun the baseline command and
compare the CSV.

Restore both files:

```sh
git restore guide/workspace/experiment.json \
  guide/workspace/network_64npu_ring.yml
```

Continue to [Run several jobs and create contention](concurrent-contention.md).
