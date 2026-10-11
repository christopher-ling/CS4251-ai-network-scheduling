#!/usr/bin/env bash
set -euo pipefail
ASTRA_ROOT=${1:-/app/astra-sim}
TEAM_ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$TEAM_ROOT/results/bandwidth_reproduced"
mkdir -p "$OUT"
for bandwidth in 50 25; do
  network="$TEAM_ROOT/configs/Ring_16npus.yml"
  if [ "$bandwidth" = 25 ]; then
    network="$TEAM_ROOT/configs/Ring_16npus_half_bw.yml"
  fi
  "$ASTRA_ROOT/build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Aware" \
    --workload-configuration="$ASTRA_ROOT/examples/workload/microbenchmarks/all_reduce/16npus_1MB/all_reduce" \
    --system-configuration="$TEAM_ROOT/configs/Ring_4chunks.json" \
    --remote-memory-configuration="$TEAM_ROOT/configs/no_memory_expansion.json" \
    --network-configuration="$network" \
    --logging-folder="$OUT/logging_${bandwidth}" \
    2>&1 | tee "$OUT/allreduce_${bandwidth}GBps.log"
done
python3 - "$OUT" <<'PY'
from pathlib import Path
import re, sys
out = Path(sys.argv[1])
for bw in (50, 25):
    text = (out / f'allreduce_{bw}GBps.log').read_text()
    times = {int(r): int(t) for r, t in re.findall(r'sys\[(\d+)\] finished, (\d+) cycles', text)}
    if set(times) != set(range(16)):
        raise SystemExit(f'{bw} GB/s: incomplete run, found ranks {sorted(times)}')
    print(f'{bw} GB/s: 16 ranks completed; collective completion = {max(times.values())} ns')
PY
