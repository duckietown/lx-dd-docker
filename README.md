<p align="center">
<a href="https://duckietown.com"><img src="./assets/images/dtlogo.png" alt="Duckietown Logo" width="50%"></a>
</p>

# Learning Experience (LX): Docker on the Duckiedrone

`Software: ente`; `Hardware: DD24-B`

In addition to source code, robotics software needs compatible libraries, tools, and startup settings. Docker packages that environment into images and runs applications in containers.

This learning experience (LX) introduces Docker through small experiments on your base station. You will inspect containers, build and test a web-server image, preserve data, and connect applications over a Docker network. You will then relate those observations to Duckiedrone services, Docker contexts, the Duckietown Shell, and the Duckietown Workspace.

## Intended learning outcomes

After completing this LX, learners will be able to:

1. Explain what Docker does and why reproducible software environments are useful in robotics.
2. Distinguish images, layers, containers, virtual machines, clients, daemons, and registries, and interpret image tags, digests, and platforms.
3. Identify the daemon receiving a Docker command and distinguish practice resources from physical or virtual Duckiedrone services.
4. Explain how daemon access, mounts, container permissions, and published ports affect isolation.
5. Run, inspect, enter, stop, restart, and remove containers, using logs and process information to understand their state.
6. Build an image from a Dockerfile, inspect its configuration, and verify the application's response through a published port.
7. Compare container writable layers, named volumes, and bind mounts, and clean up exercise resources by name.
8. Demonstrate communication between containers and interpret the network, socket, and mount settings in a Duckiedrone Compose configuration.
9. Use Docker contexts to inspect local and remote daemons, and distinguish context selection from Duckietown Shell target options.
10. Explain how the Duckietown Shell and Workspace use Docker to support project builds, workbenches, virtual robots, and development environments.

## Run this LX

Follow the [LX General Instructions](https://docs.duckietown.com/ente/opmanual-dd24/50-learning-experiences/lx-general-procedure.html) to open this LX in a prepared environment. Work through the notebooks in order, run the activities in the terminal specified by each notebook, and answer the checkpoint questions before revealing their answers.

## Notebooks

Notebooks 1–4 establish the concepts and practice environment. Notebooks 5–7 follow containers, images, and data through their lifecycles. Notebooks 8–10 connect those ideas to cooperating services and multiple Docker hosts. Notebooks 11–12 explain how Duckietown packages these operations into development workflows.

| # | Notebook | What you will learn or do |
| --- | --- | --- |
| 1 | [Introduction to Docker](./notebooks/1-introduction-to-docker.ipynb) | Explain why containers are useful and how images, registries, clients, and daemons fit together. |
| 2 | [Practicing with Docker in Duckietown](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) | Choose a terminal, inspect connection settings, and verify the local practice daemon. |
| 3 | [Docker Clients, Registries, and Platforms](./notebooks/3-docker-clients-registries-and-platforms.ipynb) | Read image references, check the daemon's platform, and distinguish images from running and stopped containers. |
| 4 | [Docker Security and Duckiedrone Boundaries](./notebooks/4-docker-security-and-duckiedrone-boundaries.ipynb) | Understand how permissions, daemon access, file sharing, and port publishing affect container isolation. |
| 5 | [Run and Inspect Containers](./notebooks/5-run-and-inspect-containers.ipynb) | Follow a container's lifecycle using logs, process and resource inspection, an additional shell, and cleanup. |
| 6 | [Build and Test a Local Image](./notebooks/6-build-and-test-a-local-image.ipynb) | Read a Dockerfile, build a web-server image, observe caching, and verify a response through a published port. |
| 7 | [Docker Volumes, Bind Mounts, and Cleanup](./notebooks/7-docker-volumes-bind-mounts-and-cleanup.ipynb) | Observe persistent data, inspect host files through a read-only mount, and remove exercise resources individually. |
| 8 | [Duckiedrone Docker Hosts and Stacks](./notebooks/8-duckiedrone-docker-hosts-and-stacks.ipynb) | Identify where Duckiedrone services run and how Compose stacks group related containers. |
| 9 | [Communication Between Containers](./notebooks/9-duckiedrone-container-communication.ipynb) | Connect two practice containers and examine networking, shared sockets, and runtime settings in real Duckiedrone configuration. |
| 10 | [Docker Contexts and Local Targets: choosing the right host for a command](./notebooks/10-docker-contexts-and-local-targets.ipynb) | Inspect and select daemon connections, then compare remote inspection through an SSH shell and a Docker context. |
| 11 | [Docker Behind the Duckietown Shell](./notebooks/11-other-docker-uses-in-duckietown.ipynb) | Connect `dts devel`, `dts code`, and virtual-robot commands to the Docker operations they automate. |
| 12 | [The Duckietown Workspace: Docker for Development](./notebooks/12-development-containers-and-duckietown-workspaces.ipynb) | Compare terminal environments, distinguish inner and outer daemons, and locate project files and persistent storage. |

## Prerequisites

Familiarity with shell commands, paths, permissions, and basic networking is useful. The [Linux and Networking LX](https://github.com/duckietown/lx-dd-linux-and-networking) introduces these topics.

For the local exercises, use a prepared development environment with Docker, the Duckietown Shell (`dts`), the LX repository, and `curl`. Follow the [Initial Setup instructions](https://docs.duckietown.com/ente/duckietown-manual/10-setup/setup-introduction.html) for your computer. Internet access is needed to obtain images and dependencies that are not already available locally.

### Choose the terminal and daemon

Read and edit the notebooks using `dts code editor`. Run the shell commands in a separate terminal in your prepared base-station environment. This may be a native Linux environment or the Duckietown Workspace; it is distinct from the LX editor container.

Before creating resources, follow [Notebook 2](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) to check the endpoint, environment overrides, and daemon response. Keep the local activities on the same verified practice daemon so their images, containers, and volumes remain available where you expect them.

The build and bind-mount exercises use files under `packages/docker_exercises/`. Run them from the LX repository root as directed. The shell's files and the daemon's filesystem are separate concerns when using remote connections; [Notebook 12](./notebooks/12-development-containers-and-duckietown-workspaces.ipynb) explains this distinction.

### Robot and project activities

A physical Duckiedrone is not required for the local container, image, storage, and network experiments. Additional activities have their own prerequisites:

- **Notebook 9:** inspecting live platform configuration requires an existing physical or virtual deployment; the source-reading and local network activities can be completed without one.
- **Notebook 10:** the remote comparison requires a physical Duckiedrone, configured SSH authentication, and a remote account with Docker access.
- **Notebook 11:** build and workbench examples require a suitable Duckietown project and its setup instructions; the virtual connection example requires an existing running virtual Duckiedrone. The command-help and source-reading activities explain the wrappers without deploying a project.
- **Notebook 12:** comparing terminals requires a running Workspace, but its configuration can also be studied without setting one up.

Use resources you own or have permission to manage. Keep `lx-docker-*` practice resources separate from platform services and remove only the resources identified by each exercise.

### Interactive checkpoints

Checkpoint cells use the notebook context supplied by the editor and a compatible Jupyter/IPython kernel with `ipywidgets`. Use the prepared LX environment for these cells. The shell command blocks are activities to run in the indicated terminal, not commands executed automatically by reading the notebook.

## Further reading

Each notebook links to references for its topic. For a broader overview, see the [Duckietown Docker introduction](https://docs.duckietown.com/ente/duckietown-manual/70-developer-manual/basics/development/developer-basics-docker.html), Docker's guides to [containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/), [images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), and [contexts](https://docs.docker.com/engine/manage-resources/contexts/), and the [Duckiedrone DD24 manual](https://docs.duckietown.com/ente/opmanual-dd24/).

## For LX authors

Learner material is in `notebooks/`, the practice web-server build context is in `packages/docker_exercises/`, and checkpoint support is in `packages/checkpoint_self_check.py` and `checkpoint_data/`. The paired [LX recipe repository](https://github.com/duckietown/lx-dd-docker-recipe) supplies the LX environment recipe; it is separate from the image learners build in Notebook 6.

Install the test dependencies in your Python environment, then check notebook links and checkpoint mappings and run the checks from the LX root:

```bash
python3 -m pip install -r tests/requirements.txt
python3 -m pytest tests/
```

These checks complement the manual activities; they do not establish that every Docker command works in a learner's environment.
