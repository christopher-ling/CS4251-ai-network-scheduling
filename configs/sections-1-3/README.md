# Sections 1-3 fixed experiment inputs

These files define the controlled environment used by the methodology
Sections 1-3 implementation and its recorded results.

- `experiment.json` contains workload and sweep parameters.
- `network_64npu_ring.yml` fixes a 64-endpoint physical ring.
- `system_ring.json` selects Ring AllReduce and four active chunks.

Each job owns four endpoints. Job `j` uses ranks
`[j, j + 16, j + 32, j + 48]`, with zero-based `j`. This strided placement
causes each four-rank logical Ring AllReduce to traverse long portions of the
physical ring. Concurrent jobs therefore share physical links while GPU
placement, topology, message size, and compute duration remain fixed.

The launcher copies these inputs into each result directory. Generated Chakra
trace files are intentionally ignored by Git because the launcher recreates
them.
