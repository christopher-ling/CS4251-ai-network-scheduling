# Section 1: represent one training iteration

## Question

How does ASTRA-sim represent the repeated compute -> communication -> compute
structure of distributed training?

ASTRA-sim does not execute a neural network or calculate gradients here. Each
simulated rank replays an execution trace. A compute node has a configured
duration, an AllReduce node has a payload and communicator, and dependencies
prevent a node from starting until its predecessor finishes.

For one iteration, every active rank receives this chain:

```text
compute (100 us) -> AllReduce (16 MiB/rank) -> final compute (100 us)
```

The four ranks in job 1 use communicator group `1`. Their AllReduce nodes have
the same operation order and group name, allowing ASTRA-sim to treat them as
participants in the same collective.

## Run only Section 1

Inside Docker:

```sh
cd /app/team
python3 scripts/run_sections_1_to_3.py \
  --astra /app/astra-sim \
  --sections 1 \
  --output results/tutorial-section-1
```

The run succeeds only if ranks 0 through 63 report completion. Four ranks run
the job; the other 60 replay a one-microsecond inactive operation so the fixed
64-endpoint topology remains unchanged.

## Inspect the generated model

```sh
cat results/tutorial-section-1/section1_one_iteration/description.json
cat results/tutorial-section-1/section1_one_iteration/groups.json
cat results/tutorial-section-1/section1_one_iteration/command.json
```

The `.et` files are binary protobuf traces, so `cat` is not useful for them.
Read `scripts/run_sections_1_to_3.py` and find `write_traces` to see how each
node and dependency is encoded.

## Answers to the methodology questions

- **How is computation represented?** A replay node with
  `duration_micros = 100`; roofline modeling is disabled.
- **When does AllReduce begin?** After the preceding compute node completes,
  because its ID is listed as a data dependency.
- **What determines communication size?** The AllReduce node's `comm_size`
  attribute, fixed here at 16,777,216 bytes per rank.
- **How long does an iteration take?** The simulator's final completion time
  includes both compute phases and the collective. The launcher reports this
  value as JCT for the one-iteration teaching case.

## Check your understanding

Changing `description.json` after the run does not alter a trace. Which input or
generator value would you change to create a different compute duration? Why
must every rank in the communicator agree on collective order?

Continue to [Section 2](02-single-job-baseline.md).
