# Compute and AllReduce trace

## Objective

Run one synthetic training iteration and connect its operations to the trace
generator.

```sh
cd /app/team
python3 scripts/run_collective_contention.py \
  --astra /app/astra-sim \
  --scenarios iteration \
  --output results/onboarding/iteration
```

Inspect the generated description and communicator groups:

```sh
cat results/onboarding/iteration/training_iteration/description.json
cat results/onboarding/iteration/training_iteration/groups.json
```

Each active rank replays:

```text
compute 100 us -> AllReduce 16 MiB/rank -> final compute 100 us
```

In `scripts/run_collective_contention.py`, `write_traces` creates each Chakra
node. `data_deps` prevents an operation from starting before its predecessor.
The collective attributes define the AllReduce type, message size, and
communicator group.

The `.et` files are binary protobuf traces; opening them as ordinary text is
not useful. Read the generator and the JSON description instead.

Expected reference completion time: approximately `2187.534 us`. That value is
simulated time: 200 us of configured compute replay plus the modeled AllReduce.

Continue to [Isolated-job baseline](isolated-baseline.md).

