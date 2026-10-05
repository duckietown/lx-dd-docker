<p align="center">
<a href="https://duckietown.com"><img src="./assets/images/dtlogo.png" alt="Duckietown Logo" width="50%"></a>
</p>

# Learning Experience (LX): Docker on the Duckiedrone

`Software: ente`; `Hardware: DD24-B`

Duckiedrone software needs a repeatable environment on the base station and on the Duckiedrone. Differences in installed libraries and setup can otherwise make the same project behave differently on each machine. Docker packages software and its dependencies into images, then runs them in containers.

This learning experience (LX) uses small base-station experiments to make that model visible, then connects it to Duckiedrone services and the project workflows used by later LXs. You will learn where software runs, where its data lives, and how to check that an image or container does the intended job.

## Intended learning outcomes

After completing this LX, learners will be able to:

1. Explain Docker's client-daemon architecture and how images, layers, containers, virtual machines, registries, tags, and digests relate.

2. Identify the Docker client, Docker daemon, current context, and central processing unit (CPU) architecture used by a Docker host.

3. Distinguish a local terminal, development container, and Docker practice container, then verify the Docker daemon selected by each environment.

4. Apply least-privilege Docker defaults and distinguish the base station's Docker host from a Duckiedrone's Docker host.

5. Run, inspect, enter, stop, and remove clearly named temporary containers.

6. Build a small image from a Dockerfile and verify its local Hypertext Transfer Protocol (HTTP) response.

7. Distinguish container writable layers, named volumes, and read-only bind mounts.

8. Explain Duckiedrone stacks and the paths connecting sensors, Duckietown Postal Service (DTPS), Robot Operating System 2 (ROS 2), and flight control.

9. Verify Docker and `dts` command targets, and distinguish Docker contexts, `dts` host arguments, Secure Shell (SSH) access to a physical Duckiedrone, and a local virtual Duckiedrone shell.

10. Describe the build, delivery, run, and workbench workflows used by later Duckiedrone LXs.

## Run this LX

Follow the Duckietown Manual's [LX General Instructions](https://docs.duckietown.com/ente/opmanual-dd24/50-learning-experiences/lx-general-procedure.html) to open this LX in a prepared environment. The notebooks provide the topic-specific activities; the prerequisites below describe the local setup.

## Notebooks

Start with [Notebook 1](./notebooks/1-introduction-to-docker.ipynb). The opening chapters establish the image, container, and host model so you can interpret the lifecycle, web-server, and persistence experiments that follow. The Duckiedrone chapters connect that model to its sensor and communication services. The connection and project chapters explain how to reach the right host and run your code on the Duckiedrone. The final development-environment chapter is an optional wrap-up for understanding changes between terminals.

| # | Notebook | Description |
| --- | --- | --- |
| 1 | [Notebook 1](./notebooks/1-introduction-to-docker.ipynb) | Understand how Docker's client, daemon, and objects provide a repeatable runtime |
| 2 | [Notebook 2](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) | Identify the practice host and distinguish image files from container changes |
| 3 | [Notebook 3](./notebooks/3-docker-clients-registries-and-platforms.ipynb) | Identify where images come from and which processor architecture can run them |
| 4 | [Notebook 4](./notebooks/4-docker-security-and-duckiedrone-boundaries.ipynb) | Understand how permissions, mounts, and ports affect host files and services |
| 5 | [Notebook 5](./notebooks/5-run-and-inspect-containers.ipynb) | Observe a temporary container's process, output, and lifecycle |
| 6 | [Notebook 6](./notebooks/6-build-and-test-a-local-image.ipynb) | Turn source into an image and check that its web server handles a local request |
| 7 | [Notebook 7](./notebooks/7-docker-volumes-bind-mounts-and-cleanup.ipynb) | Observe which data survives container removal and how to share host files |
| 8 | [Notebook 8](./notebooks/8-duckiedrone-docker-hosts-and-stacks.ipynb) | Locate the host and stack responsible for a Duckiedrone service |
| 9 | [Notebook 9](./notebooks/9-duckiedrone-data-paths.ipynb) | Trace sensor and flight-controller data through drivers and bridges |
| 10 | [Notebook 10](./notebooks/10-duckiedrone-deployment-boundaries.ipynb) | Match each task to the workflow that supplies its service configuration |
| 11 | [Notebook 11](./notebooks/11-docker-contexts-and-local-targets.ipynb) | Explain which daemon receives a command and check that it responds |
| 12 | [Notebook 12](./notebooks/12-remote-duckiedrone-docker-contexts.ipynb) | Compare Docker clients on the Duckiedrone and base station and the resources they inspect |
| 13 | [Notebook 13](./notebooks/13-dts-devel-build-and-run.ipynb) | Choose where to build, deliver, and run a project image |
| 14 | [Notebook 14](./notebooks/14-dts-code-workbenches.ipynb) | Start a repeatable project workbench and inspect its running environment |
| 15 | [Notebook 15](./notebooks/15-virtual-duckiedrone-connections.ipynb) | Find a virtual Duckiedrone and enter its shell |
| 16 | [Notebook 16](./notebooks/16-development-containers-and-duckietown-workspaces.ipynb) | Explain how changing terminals affects files, tools, and Docker connections |

## Prerequisites

Before running the command notebooks, complete the Duckietown Manual's [Initial Setup](https://docs.duckietown.com/ente/duckietown-manual/10-setup/setup-introduction.html) so Docker and the Duckietown Shell (`dts`) are installed and configured on the base station.

Use `dts code editor` to read and edit this LX. Run `dts` and local Docker-practice commands in a separate base-station terminal, where they can use the host's files, configured daemon, and credentials. The browser editor needs no Docker socket; exposing one would give it control over the daemon's resources.

### Choose the terminal

| Task | Where to run it |
| --- | --- |
| Read and edit notebooks and exercise files | `dts code editor` or another editor |
| Run the local Docker practice notebooks | A base-station terminal connected to a local Docker Engine or Docker Desktop installation |
| Run `dts` project, workbench, or virtual-Duckiedrone commands | A base-station terminal, outside `dts code editor` |
| Inspect a Duckiedrone | A shell on the Duckiedrone or an explicitly named Duckiedrone Docker context |

### Docker foundations and local practice

[Notebook 1](./notebooks/1-introduction-to-docker.ipynb) can be read before installing Docker. The local practice notebooks need the LX files and a terminal with access to Docker Engine or Docker Desktop; all their commands run on the base station. Interactive checkpoints require the notebook metadata supplied by `dts code editor` and a compatible Jupyter/IPython kernel with `ipywidgets` available. The metadata identifies the current notebook so the helper can load its matching questions.

Begin by inspecting the connection settings and contacting the daemon:

```bash
docker context show
printf 'DOCKER_HOST=%s\n' "${DOCKER_HOST:-<unset>}"
printf 'DOCKER_CONTEXT=%s\n' "${DOCKER_CONTEXT:-<unset>}"
docker version
```

`docker context show` reports the selected context name; the two environment variables can override it. A server section in `docker version` confirms that the selected daemon responded. [Notebook 2](./notebooks/2-docker-containers-images-and-safe-local-practice.ipynb) explains how to interpret these results for the local exercises.

Use the base-station daemon for the local practice resources, whose names begin with `lx-docker-`. Remove only named exercise resources: broad cleanup commands such as `docker system prune` can also remove resources belonging to other projects.

### Duckiedrone project workflows

The build and run examples in [Notebook 13](./notebooks/13-dts-devel-build-and-run.ipynb) need a valid Duckietown project. The workbench commands in [Notebook 14](./notebooks/14-dts-code-workbenches.ipynb) also use that project's build settings and startup command. Follow the project's setup instructions to prepare its build and runtime environment.

### Duckiedrone access

Activities on a physical Duckiedrone need its configured connection and setup instructions. Use a Duckiedrone you own or have permission to manage. The local virtual commands in [Notebook 15](./notebooks/15-virtual-duckiedrone-connections.ipynb) need a virtual Duckiedrone set up on the base station. Keep Duckiedrone services separate from the named practice resources when choosing a command target.

## Complete the Docker exercise

The build context for [Notebook 6](./notebooks/6-build-and-test-a-local-image.ipynb) is in `packages/docker_exercises/`. Read its Dockerfile and Python server to see which files enter the image and which process runs. Build it and check the loopback-only web response to verify that the server handles a request through the published port. [Notebook 7](./notebooks/7-docker-volumes-bind-mounts-and-cleanup.ipynb) then shows how data can survive container removal, how a read-only bind mount shares host files, and how to clean up the named exercise resources.

## Further reading

Each notebook's `Further reading` section is the primary reference for its lesson. This guide groups the course's sources:

- __Docker foundations:__ Docker's official guides to [containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/) and [images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/).

- __Hosts and connections:__ Docker's [contexts documentation](https://docs.docker.com/engine/manage-resources/contexts/).

- __Duckiedrone setup and operation:__ the [Duckiedrone DD24 manual](https://docs.duckietown.com/ente/opmanual-dd24/).

## For LX authors

Learner material is in `notebooks/` and `packages/`. Structural checks are in `tests/`, and the exercise image recipe is maintained in the paired `lx-dd-docker-recipe` repository. Run the structural checks from the LX root:

```bash
python3 -m pytest tests/
```
