# Four-GPU training-iteration example

This is the smallest example used by the learning guide. All four endpoints
are active, so the output contains four Chakra traces and no inactive ranks.

| File | Purpose |
|---|---|
| `experiment.json` | Compute time, iterations, message size, and rank count |
| `system.json` | Ring collective implementation |
| `network.yml` | Four-endpoint physical Ring with bandwidth and latency |

The example uses a 1-MiB AllReduce message so the relationship between bytes,
bandwidth, and completion time can be explored before moving to the 64-endpoint
research experiment.
