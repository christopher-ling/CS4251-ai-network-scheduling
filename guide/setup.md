# Set up ASTRA-sim and the project

## Repository layout

Create one parent directory containing two separate repositories:

```text
astra-project/
├── astra-sim/                       upstream simulator engine
└── CS4251-ai-network-scheduling/    team code, inputs, guide, and results
```

They remain separate because they have different owners and Git histories.
Keeping them beside each other allows the Docker environment to mount both.

## One-time installation

Open Docker Desktop, then run:

```sh
mkdir -p ~/Desktop/School/astra-project
cd ~/Desktop/School/astra-project

git clone https://github.com/astra-sim/astra-sim.git
git clone --branch tutorial/astra-sim \
  https://github.com/christopher-ling/CS4251-ai-network-scheduling.git

cd astra-sim
git checkout 4ce9ecfe746a3ee5fe47559a11d91644d641fa7f
git submodule update --init --recursive
cd ../CS4251-ai-network-scheduling
```

What these commands do:

- `git clone` downloads the simulator and the team project.
- `git checkout <commit>` selects the exact ASTRA-sim version used to produce
  the reference results. A detached-HEAD message is normal here.
- `git submodule update` downloads the specific Chakra and backend code needed
  by that ASTRA-sim version.

Open the `astra-project` directory in your IDE so you can browse both folders.

## Build the environment

From `CS4251-ai-network-scheduling`, run:

```sh
docker compose up -d --build
docker compose exec astra bash -lc \
  'cd /app/astra-sim && ./build/astra_analytical/build.sh'
```

The first command builds and starts the Linux container. `compose.yaml` mounts
the upstream simulator at `/app/astra-sim` and the team project at `/app/team`.
The second command compiles the congestion-aware analytical backend. You do
not need to rebuild it before every experiment unless its source changes.

Check that the experiment runner is available:

```sh
docker compose exec astra \
  python3 scripts/run_collective_contention.py --help
```

Continue to [Create and change a training trace](training-trace.md).
