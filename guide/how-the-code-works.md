# Connect the files to the Python runner

Do this page after the three experiments. The goal is to recognize the parts
of the code, not to understand every Python statement.

Open `scripts/run_collective_contention.py` in VS Code and use **Cmd+F** to
find these functions in order:

| Function | Its job |
|---|---|
| `build_groups` | Assign four physical ranks to each simulated training job |
| `build_scenarios` | Turn the selected job counts into cases to run |
| `write_traces` | Encode compute, AllReduce, and dependencies as Chakra `.et` files |
| `build_trace_preview` | Write the readable version used in the tutorial |
| `run_case` | Copy inputs, launch the ASTRA-sim binary, and collect completion times |
| `add_slowdown_and_summarize` | Calculate slowdown, makespan, and fairness |

## Follow one AllReduce through the code

Inside `write_traces`, find the call whose name contains `allreduce`. The node
has three important attributes:

- `comm_type` is `ALL_REDUCE`;
- `comm_size` comes from `message_bytes_per_rank`;
- `pg_name` identifies the four-rank communicator group for that job.

The preceding compute node's ID is placed in `data_deps`, which prevents
AllReduce from becoming ready before compute finishes. ASTRA-sim then reads:

1. the generated workload trace;
2. `system_ring.json` for the ring collective algorithm;
3. `network_64npu_ring.yml` for network capacity and delay;
4. `groups.json` for the ranks participating in each job.

It writes a completion time for every rank. `run_case` takes the latest rank
completion within a job as that job's JCT.

## When would you edit ASTRA-sim itself?

The tutorial changes workload and network inputs, so no upstream C++ changes
are required. You would edit the ASTRA-sim or ns-3 source when implementing
behavior the configuration files cannot express, such as a new collective
admission scheduler, a new network-state signal, or an MLTCP transport model.

That distinction is useful for this project:

```text
change an experiment              -> edit JSON/YAML or trace generation
add a new scheduling mechanism    -> edit simulator scheduling code
add/change packet transport       -> edit the ns-3 backend
```
