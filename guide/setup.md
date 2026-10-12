# Set up the VS Code workspace

## Goal

At the end of this page, VS Code will show two folders in one window:

```text
Team project and tutorial                 <- files you will edit
ASTRA-sim engine (read after tutorial)    <- upstream simulator source
```

They are separate Git repositories because the first belongs to the class
team, while the second belongs to the ASTRA-sim maintainers. They are siblings
so Docker can mount both without copying one project into the other.

## One-time preparation

Docker Desktop must be open. In a terminal, create one parent folder and clone
the two repositories into it:

```sh
mkdir -p ~/Desktop/School/astra-project
cd ~/Desktop/School/astra-project
git clone https://github.com/astra-sim/astra-sim.git
git clone --branch tutorial/astra-sim https://github.com/christopher-ling/CS4251-ai-network-scheduling.git
cd astra-sim
git checkout 4ce9ecfe746a3ee5fe47559a11d91644d641fa7f
git submodule update --init --recursive
```

The long value is a Git commit ID. It makes every teammate use the exact
ASTRA-sim version that produced the project's reference results. Seeing
`detached HEAD` after checkout is expected because this dependency is pinned.

## Open the supplied workspace

In VS Code, choose **File > Open Workspace from File...**, then open:

```text
CS4251-ai-network-scheduling/astra-sim-tutorial.code-workspace
```

In the Explorer, expand **Team project and tutorial**, then open these three
files side by side:

- `guide/workspace/experiment.json`
- `guide/workspace/system_ring.json`
- `guide/workspace/network_64npu_ring.yml`

Read the field names only. You do not need to understand every value yet.

## Build with VS Code tasks

Open the Command Palette with **Cmd+Shift+P**, select **Tasks: Run Task**, and
run these tasks in order:

1. **Setup 1: Build and start Docker**
2. **Setup 2: Compile ASTRA-sim analytical backend**

These tasks show their output in VS Code's integrated terminal. The first can
take several minutes on a new computer. The second creates the analytical
simulator binary used by all three lessons.

If both tasks finish without an error, continue to
[Build and change one training trace](training-trace.md).
