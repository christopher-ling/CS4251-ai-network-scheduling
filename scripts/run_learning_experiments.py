#!/usr/bin/env python3
"""Run from the team repository inside Docker with --astra /app/astra-sim."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--astra', type=Path, required=True)
parser.add_argument('--output', type=Path, default=Path('results/learning'))
args = parser.parse_args()
astra = args.astra.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(astra))
from extern.graph_frontend.chakra.schema.protobuf.et_def_pb2 import (
    Node, AttributeProto, GlobalMetadata, COMP_NODE, COMM_COLL_NODE, ALL_REDUCE)
from extern.graph_frontend.chakra.src.third_party.utils.protolib import (
    encodeMessage, decodeMessage)

def inspect_trace():
    path = astra / 'examples/workload/microbenchmarks/all_reduce/16npus_1MB/all_reduce.0.et'
    with path.open('rb') as f:
        meta, node = GlobalMetadata(), Node()
        assert decodeMessage(f, meta) and decodeMessage(f, node)
    attrs = {a.name: getattr(a, a.WhichOneof('value')) for a in node.attr}
    (out / 'trace-inspection.json').write_text(json.dumps({
        'node_type': node.type, 'name': node.name, 'attributes': attrs,
        'data_dependencies': list(node.data_deps), 'duration_micros': node.duration_micros,
    }, indent=2))

def traces(case, active, groups, size, iterations, compute_us=100):
    case.mkdir(parents=True, exist_ok=True)
    for rank in range(16):
        gid = next((g for g, ranks in groups.items() if rank in ranks), None)
        with (case / f'workload.{rank}.et').open('wb') as f:
            encodeMessage(f, GlobalMetadata(version='0.0.4'))
            previous, ident = None, 0
            def write(kind, name, duration=0, communication=False):
                nonlocal previous, ident
                node = Node(id=ident, name=name, type=kind, duration_micros=duration)
                if previous is not None:
                    node.data_deps.append(previous)
                node.attr.append(AttributeProto(name='is_cpu_op', bool_val=False))
                if communication:
                    node.attr.extend([
                        AttributeProto(name='comm_type', int64_val=ALL_REDUCE),
                        AttributeProto(name='comm_size', int64_val=(size[gid] if isinstance(size, dict) else size)),
                        AttributeProto(name='pg_name', string_val=str(gid)),
                    ])
                encodeMessage(f, node)
                previous, ident = ident, ident + 1
            if gid not in active:
                write(COMP_NODE, 'idle_endpoint', 1)
            else:
                for i in range(iterations):
                    write(COMP_NODE, f'job_{gid}_compute_{i}', compute_us)
                    write(COMM_COLL_NODE, f'job_{gid}_allreduce_{i}', communication=True)
                write(COMP_NODE, f'job_{gid}_final_compute', compute_us)
    (case / 'groups.json').write_text(json.dumps(groups))
    (case / 'description.json').write_text(json.dumps({
        'active_groups': active, 'groups': groups, 'payload_bytes_per_rank': size,
        'iterations': iterations, 'compute_phase_us': compute_us,
        'final_compute_us': compute_us, 'scheduler': 'immediate readiness; unmodified upstream',
    }, indent=2))

def run(name, active, groups, size, iterations, bandwidth, topology="Ring", active_chunks=4, policy="immediate"):
    case = out / name
    traces(case, active, groups, size, iterations)
    network = case / 'network.yml'
    network.write_text(f'topology: [ {topology} ]\nnpus_count: [ 16 ]\nbandwidth: [ {bandwidth} ]\nlatency: [ 500.0 ]\n')
    system = json.loads((astra / 'examples/system/native_collectives/Ring_4chunks.json').read_text())
    system['active-chunks-per-dimension'] = active_chunks
    (case / 'system.json').write_text(json.dumps(system, indent=2))
    cmd = [str(astra / 'build/astra_analytical/build/bin/AstraSim_Analytical_Congestion_Aware'),
           f'--workload-configuration={case}/workload',
           f'--comm-group-configuration={case}/groups.json',
           f'--system-configuration={case}/system.json',
           f'--remote-memory-configuration={astra}/examples/remote_memory/analytical/no_memory_expansion.json',
           f'--network-configuration={network}', f'--logging-folder={case}/logging']
    (case / 'command.json').write_text(json.dumps(cmd, indent=2))
    result = subprocess.run(cmd, cwd=astra, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=90,
                            env={**os.environ, 'CS4251_POLICY': policy})
    (case / 'run.log').write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f'{name} failed ({result.returncode}); inspect {case}/run.log')
    if policy != 'immediate' and f'CS4251 admit policy={policy}' not in result.stdout:
        raise RuntimeError('Admission prototype was not active; apply the patch and rebuild first')
    matches = re.findall(r'sys\[(\d+)\] finished, (\d+) cycles', result.stdout)
    times = {int(rank): int(t) for rank, t in matches}
    if set(times) != set(range(16)):
        raise RuntimeError(f'{name}: expected 16 completed ranks, got {sorted(times)}')
    rows = []
    for gid in active:
        finish = max(times[r] for r in groups[gid])
        rows.append({'case': name, 'group': gid, 'bandwidth_GBps': bandwidth,
                     'completion_ns': finish, 'completion_us': finish / 1000,
                     'payload_bytes_per_rank': (size[gid] if isinstance(size, dict) else size),
                     'iterations': iterations, 'policy': policy})
    print(name, rows, flush=True)
    return rows

inspect_trace()
rows = []
for bw in (50, 25):
    rows += run(f'training_cycle_{bw}GBps', ['1'], {'1': list(range(16))}, 1024**2, 3, bw, active_chunks=1)
groups = {'1': [0,1,4,5,8,9,12,13], '2': [2,3,6,7,10,11,14,15]}
for name, active in [('job_A_isolated', ['1']), ('job_B_isolated', ['2']), ('two_jobs_shared', ['1','2'])]:
    rows += run(name, active, groups, 16 * 1024**2, 3, 50)
for name, active in [('switch_A_isolated', ['1']), ('switch_B_isolated', ['2']), ('switch_two_jobs', ['1','2'])]:
    rows += run(name, active, groups, 16 * 1024**2, 3, 50, topology='Switch')
if os.environ.get('CS4251_RUN_POLICIES') == '1':
    payloads = {'1': 16 * 1024**2, '2': 1024**2}
    for name, active in [('heterogeneous_A_isolated', ['1']), ('heterogeneous_B_isolated', ['2'])]:
        rows += run(name, active, groups, payloads, 3, 50)
    for policy in ('immediate', 'fifo', 'size_aging'):
        rows += run(f'heterogeneous_{policy}', ['1','2'], groups, payloads, 3, 50, policy=policy)
with (out / 'summary.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
versions = subprocess.check_output(['git', '-C', str(astra), 'rev-parse', 'HEAD'], text=True)
(out / 'astra-sim-commit.txt').write_text(versions)
(out / 'submodule-commits.txt').write_text(subprocess.check_output(
    ['git', '-C', str(astra), 'submodule', 'status', '--recursive'], text=True))

(out / 'source-changes.patch').write_text(subprocess.check_output(
    ['git', '-C', str(astra), 'diff', '--', 'astra-sim/workload/Workload.cc', 'astra-sim/workload/Workload.hh'], text=True))
