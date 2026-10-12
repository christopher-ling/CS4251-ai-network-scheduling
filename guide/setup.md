# Environment setup

## Prerequisites

- Docker Desktop is running.
- Git is installed.
- The ASTRA-sim and team repositories are sibling directories.

From their parent directory:

```sh
git clone https://github.com/astra-sim/astra-sim.git
git clone https://github.com/christopher-ling/CS4251-ai-network-scheduling.git

cd astra-sim
git checkout 4ce9ecfe746a3ee5fe47559a11d91644d641fa7f
git submodule update --init --recursive
docker build -t astra-sim:latest -f Dockerfile .
cd ..
```

Check out this onboarding branch in the team repository:

```sh
cd CS4251-ai-network-scheduling
git switch tutorial/astra-sim-onboarding
cd ..
```

Start the container from the parent directory:

```sh
docker run --rm -it --name astra-sim-onboarding --shm-size=8g \
  -v "$PWD/astra-sim:/app/astra-sim" \
  -v "$PWD/CS4251-ai-network-scheduling:/app/team" \
  astra-sim:latest bash
```

Inside Docker, compile the analytical backend if the binary does not already
exist:

```sh
cd /app/astra-sim
./build/astra_analytical/build.sh
```

Verify the project runner:

```sh
cd /app/team
python3 scripts/run_collective_contention.py --help
```

Continue to [Compute and AllReduce trace](training-trace.md).

