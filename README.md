<p align="center">
<a href="https://duckietown.com"><img src="./assets/images/dtlogo.png" alt="Duckietown Logo" width="50%"></a>
</p>

# Learning Experience (LX): Docker on the Duckiedrone

`Software: ente`; `Hardware: DD24-B`

This learning experience (LX) introduces Docker through the container model used by Duckietown. Focused notebooks cover images, containers, local ports, persistent data, Duckiedrone platform boundaries, and the authorized connection workflows used by later LXs. The practical commands use only learner-owned Docker resources on an authorized base station; they do not modify Duckiedrone platform containers.

## Intended learning outcomes

After completing this LX, learners will be able to:

1. Explain Docker's client-daemon architecture and how images, layers, containers, virtual machines, registries, tags, and digests relate.

2. Identify the Docker client, Docker daemon, current context, and central processing unit (CPU) platform used by an authorized Docker host.

3. Distinguish a local terminal, development container, and Docker practice container, then verify the Docker daemon selected by each environment.

4. Apply least-privilege Docker defaults and distinguish a local practice host from Duckiedrone platform hosts.

5. Run, inspect, enter, stop, and remove clearly named temporary containers.

6. Build a small image from a Dockerfile and verify its local Hypertext Transfer Protocol (HTTP) response.

7. Distinguish container writable layers, named volumes, and read-only bind mounts.

8. Explain Duckiedrone platform stacks and the paths connecting sensors, Duckietown Postal Service (DTPS), Robot Operating System 2 (ROS 2), and flight control.

9. Verify Docker and `dts` command targets, and distinguish Docker contexts, `dts` host arguments, physical-device Secure Shell (SSH) access, and a local virtual Duckiedrone shell.

10. Describe the authorized build, delivery, run, and workbench workflows used by later Duckiedrone LXs.

## Run this LX

Follow the Duckietown Manual's [LX General Instructions](https://docs.duckietown.com/ente/opmanual-dd24/50-learning-experiences/lx-general-procedure.html) to open this LX in a prepared environment. The notebooks provide the topic-specific activities; the prerequisites below describe the local setup.

## Notebooks

Start with [Notebook 1](./notebooks/1-docker-engine-and-core-concepts.ipynb) before Docker commands. The core Docker notebook sequence develops local practice, platform boundaries, and authorized connection workflows. The development-environment wrap-up is optional.

| # | Notebook | Description |
| --- | --- | --- |
| 1 | [Notebook 1](./notebooks/1-docker-engine-and-core-concepts.ipynb) | Docker Engine client-daemon architecture, core objects, registries, and host-kernel relationship |
| 2 | [Notebook 2](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) | Safe local preflight, containers versus virtual machines, images, layers, and containers |
| 3 | [Notebook 3](./notebooks/3-docker-clients-registries-and-platforms.ipynb) | Docker clients, daemons, registries, tags, platforms, and read-only resource inspection |
| 4 | [Notebook 4](./notebooks/4-docker-security-and-duckiedrone-boundaries.ipynb) | Least-privilege Docker defaults and the boundary around Duckiedrone platform services |
| 5 | [Notebook 5](./notebooks/5-run-and-inspect-containers.ipynb) | Pull, run, monitor, inspect, enter, stop, and remove a temporary container |
| 6 | [Notebook 6](./notebooks/6-build-and-test-a-local-image.ipynb) | Inspect a build context, build a local web image, publish it to loopback, and verify its Hypertext Transfer Protocol (HTTP) response |
| 7 | [Notebook 7](./notebooks/7-docker-volumes-bind-mounts-and-cleanup.ipynb) | Named volumes, read-only bind mounts, and cleanup of only LX resources |
| 8 | [Notebook 8](./notebooks/8-duckiedrone-docker-hosts-and-stacks.ipynb) | The base-station and Duckiedrone Docker hosts, responsibilities, and managed stacks |
| 9 | [Notebook 9](./notebooks/9-duckiedrone-platform-data-paths.ipynb) | Optional stacks plus sensor, Duckietown Postal Service (DTPS), Robot Operating System 2 (ROS 2), and flight-control data paths |
| 10 | [Notebook 10](./notebooks/10-duckiedrone-deployment-boundaries.ipynb) | Authorized deployment boundaries and keeping platform roles separate from Docker practice |
| 11 | [Notebook 11](./notebooks/11-docker-contexts-and-local-targets.ipynb) | Current-context inspection and explicit local Docker targets |
| 12 | [Notebook 12](./notebooks/12-remote-duckiedrone-docker-contexts.ipynb) | Authorized SSH-backed contexts, SSH comparisons, and separate host inventories |
| 13 | [Notebook 13](./notebooks/13-dts-devel-build-and-run.ipynb) | Authorized `dts devel` build, delivery, and run architecture |
| 14 | [Notebook 14](./notebooks/14-dts-code-workbenches.ipynb) | Later-LX `dts code` workbench workflow and shell attachment |
| 15 | [Notebook 15](./notebooks/15-virtual-duckiedrone-connections.ipynb) | Local virtual Duckiedrone connections and selecting the appropriate connection path |
| 16 | [Notebook 16](./notebooks/16-development-containers-and-duckietown-workspaces.ipynb) | Optional local-terminal, development-container, and [Duckietown Workspace](https://github.com/duckietown/workspace) wrap-up |

## Prerequisites

Before running the command notebooks, complete the Duckietown Manual's [Initial Setup](https://docs.duckietown.com/ente/duckietown-manual/10-setup/setup-introduction.html) so Docker and the Duckietown Shell (`dts`) are installed and configured on the base station. This LX teaches Docker use and boundaries; it assumes that established base-station setup rather than replacing it.

`dts code editor` is a separate browser editor. Use it to read and edit this LX, but do not use its terminal as the Docker practice host or give it a Docker socket. Start `dts` commands and the local Docker-practice commands in a separate base-station terminal, where the Docker client can identify its intended daemon and use the base station's credentials.

Interactive checkpoints require the notebook metadata supplied by `dts code editor`; a compatible Jupyter/IPython kernel with `ipywidgets` available is not sufficient by itself.

| Task | Where to run it |
| --- | --- |
| Read and edit notebooks and exercise files | `dts code editor` or another editor |
| Run the local Docker practice notebooks | A base-station terminal connected to an authorized local Docker Engine or Docker Desktop installation |
| Run `dts` project, workbench, or virtual-Duckiedrone commands | A base-station terminal, outside `dts code editor` |
| Inspect a Duckiedrone | The Duckiedrone shell after the authorized connection workflow, or one explicitly named authorized Docker context |

[Notebook 1](./notebooks/1-docker-engine-and-core-concepts.ipynb) needs no Docker installation. The core Docker practice notebooks need a terminal with access to an authorized local Docker Engine or Docker Desktop installation. Begin with:

```bash
docker context show
printf 'DOCKER_HOST=%s\n' "${DOCKER_HOST:-<unset>}"
printf 'DOCKER_CONTEXT=%s\n' "${DOCKER_CONTEXT:-<unset>}"
docker version
```

`docker context show` reports the selected context name, not proof of the effective daemon target. [Notebook 2](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) explains how `DOCKER_HOST` and `DOCKER_CONTEXT` can change that target before a modifying command.

Do not use a remote Docker context, the Docker daemon of a Duckiedrone, or a shared Docker host for the local practice notebooks. The platform and connection workflow notebooks explain separate responsibilities; only use their physical-device commands within an authorized operating procedure defined by the device owner. The local practice notebooks use only resources beginning with `lx-docker-`; do not use broad cleanup commands such as `docker system prune`.

## Complete the Docker exercise

The build context for [Notebook 6](./notebooks/6-build-and-test-a-local-image.ipynb) is in `packages/docker_exercises/`. Read its Dockerfile and Python server before building it. [Notebook 6](./notebooks/6-build-and-test-a-local-image.ipynb) guides you through building the image and checking the loopback-only web response. [Notebook 7](./notebooks/7-docker-volumes-bind-mounts-and-cleanup.ipynb) then uses a named volume, inspects a read-only bind mount, and removes only the resources created by the workflow.

## Further reading

See Docker's official guides to [containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/), [images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), and [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/). For Duckiedrone operating context, see the [Duckiedrone DD24 manual](https://docs.duckietown.com/ente/opmanual-dd24/).

## For LX authors

Learner material is in `notebooks/` and `packages/`. Structural checks are in `tests/`, and the exercise image recipe is maintained in the paired `lx-dd-docker-recipe` repository. Run the structural checks from the LX root:

```bash
python3 -m pytest tests/
```
