<p align="center">
<a href="https://duckietown.com"><img src="./assets/images/dtlogo.png" alt="Duckietown Logo" width="50%"></a>
</p>

# Learning Experience (LX): Docker on the Duckiedrone

`Software: ente`; `Hardware: DD24-B`

This learning experience (LX) introduces Docker through the container model used by
Duckietown. Focused modules cover images, containers, local ports, persistent
data, Duckiedrone platform boundaries, and the authorized connection workflows
used by later learning experiences. The practical commands use only
learner-owned Docker resources on an authorized base station; they do not
modify a physical Duckiedrone's platform containers.

## Intended learning outcomes

After completing this learning experience, learners will be able to:

1. Explain Docker's client-daemon architecture and how images, layers,
    containers, virtual machines, registries, tags, and digests relate.

2. Identify the Docker client, Docker daemon, current context, and central
    processing unit (CPU) platform
    used by an authorized Docker host.

3. Distinguish a local terminal, development container, and Docker practice
    container, then verify the Docker daemon selected by each environment.

4. Apply least-privilege Docker defaults and distinguish a local practice host
    from a physical Duckiedrone platform host.

5. Run, inspect, enter, stop, and remove clearly named temporary containers.

6. Build a small image from a Dockerfile and verify its local Hypertext Transfer
    Protocol (HTTP) response.

7. Distinguish container writable layers, named volumes, and read-only bind
    mounts.

8. Explain Duckiedrone platform stacks and the paths connecting sensors,
    Duckietown Postal Service (DTPS), Robot Operating System 2 (ROS 2), and
    flight control.

9. Verify Docker and `dts` command targets, and distinguish Docker contexts,
    `dts` host arguments, physical-device Secure Shell (SSH) access, and a local
    virtual Duckiedrone shell.

10. Describe the authorized build, delivery, run, and workbench workflows used
    by later Duckiedrone learning experiences.

## Notebooks

Start with required Module 1 before Docker commands. Work through Modules 2
through 15 for the Docker sequence. Module 16 is an optional wrap-up that
applies Docker concepts to development environments.

| # | Notebook | Description |
| --- | --- | --- |
| 1 | `1-docker-foundations-and-architecture.ipynb` | Docker Engine client-daemon architecture, core objects, registries, and host-kernel relationship |
| 2 | `2-docker-fundamentals.ipynb` | Safe local preflight, containers versus virtual machines, images, layers, and containers |
| 3 | `3-docker-clients-registries-and-platforms.ipynb` | Docker clients, daemons, registries, tags, platforms, and read-only resource inspection |
| 4 | `4-docker-security-and-duckiedrone-boundaries.ipynb` | Least-privilege Docker defaults and the boundary around Duckiedrone platform services |
| 5 | `5-run-and-inspect-containers.ipynb` | Pull, run, monitor, inspect, enter, stop, and remove a temporary container |
| 6 | `6-build-and-test-a-local-image.ipynb` | Inspect a build context, build a local web image, publish it to loopback, and verify its Hypertext Transfer Protocol (HTTP) response |
| 7 | `7-docker-volumes-bind-mounts-and-cleanup.ipynb` | Named volumes, read-only bind mounts, and cleanup of only LX resources |
| 8 | `8-duckiedrone-docker-hosts-and-stacks.ipynb` | The base-station and Duckiedrone Docker hosts, responsibilities, and managed stacks |
| 9 | `9-duckiedrone-platform-data-paths.ipynb` | Optional stacks plus sensor, Duckietown Postal Service (DTPS), Robot Operating System 2 (ROS 2), and flight-control data paths |
| 10 | `10-duckiedrone-deployment-boundaries.ipynb` | Authorized deployment boundaries and keeping platform roles separate from Docker practice |
| 11 | `11-docker-contexts-and-local-targets.ipynb` | Current-context inspection and explicit local Docker targets |
| 12 | `12-remote-duckiedrone-docker-contexts.ipynb` | Authorized SSH-backed contexts, SSH comparisons, and separate host inventories |
| 13 | `13-dts-devel-build-and-run.ipynb` | Authorized `dts devel` build, delivery, and run architecture |
| 14 | `14-dts-code-workbenches.ipynb` | Later-LX `dts code` workbench workflow and shell attachment |
| 15 | `15-virtual-duckiedrone-connections.ipynb` | Local virtual Duckiedrone connections and selecting the appropriate connection path |
| 16 | `16-development-containers-and-duckietown-workspaces.ipynb` | Optional local-terminal, development-container, and [Duckietown Workspace](https://github.com/duckietown/workspace) wrap-up |

## What you need

Module 1 needs no Docker installation. Notebooks 2-7 need a terminal with
access to an authorized local Docker Engine or Docker Desktop installation.
Begin with:

```bash
docker version
docker context show
```

Do not use a remote Docker context, a physical Duckiedrone's Docker daemon, or
a shared laboratory host unless you own it or have explicit permission from its
owner. Notebooks 8-15 explain platform and connection workflows; only use their
physical-device commands within an authorized operating procedure. In an
instructor-led setting, follow the instructor's additional procedures. The local
practice notebooks use only resources beginning with `lx-docker-`; do not use
broad cleanup commands such as `docker system prune`.

## Complete the Docker exercise

The build context for Notebook 6 is in `packages/docker_exercises/`. Read its
Dockerfile and Python server before building it. Notebook 6 guides you through
building the image and checking the loopback-only web response. Notebook 7 then
uses a named volume, inspects a read-only bind mount, and removes only the
resources created by the workflow.

## Further reading

See Docker's official guides to
[containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/),
[images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/),
and [Docker contexts](https://docs.docker.com/engine/manage-resources/contexts/).
For Duckiedrone operating context, see the
[Duckiedrone DD24 manual](https://docs.duckietown.com/ente/opmanual-dd24/).

## For LX authors

Learner material is in `notebooks/` and `packages/`. Structural checks are in
`tests/`, and the exercise image recipe is maintained in the paired
`lx-dd-docker-recipe` repository. Run the structural checks from the LX root:

```bash
pytest tests/
```
