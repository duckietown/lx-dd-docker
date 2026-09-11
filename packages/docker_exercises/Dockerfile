# Use an explicitly tagged Python base image with current security fixes.
# Use a verified Python runtime, pinned so each build uses the same contents.
FROM cgr.dev/chainguard/python:latest@sha256:780029a86e72bf3a58b1795cb77ab73b8f48dfea8c94ab154345396dc3d3237a

# Later commands and the running program use this directory.
WORKDIR /app

# Copy only the program needed by this image, owned by the non-root runtime user.
COPY --chown=65532:65532 server.py ./

# Avoid writing bytecode beside the read-only application source.
ENV PYTHONDONTWRITEBYTECODE=1

# The base image supplies this unprivileged account; keep it explicit for learners.
USER nonroot

# Document the port used by the web server. docker run publishes it separately.
EXPOSE 8080

# Start this exact interpreter, then pass the program name as its default argument.
ENTRYPOINT ["/usr/bin/python"]
CMD ["server.py"]
