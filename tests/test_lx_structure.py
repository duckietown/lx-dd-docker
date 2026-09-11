"""Sanity tests for the Docker learning experience.

Run from the LX root with:

    pytest tests/

These tests validate learner material without requiring a Docker daemon, so they
can run inside the editor container or on a plain Python host.
"""

import ast
import json
import re
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
EXERCISE_DIR = ROOT / "packages" / "docker_exercises"
README_PATH = ROOT / "README.md"
CHECKPOINT_DATA_DIR = ROOT / "checkpoint_data"
CHECKPOINT_SELF_CHECK_PATH = ROOT / "packages" / "checkpoint_self_check.py"
checkpoint_self_check = import_module("packages.checkpoint_self_check")
LIST_ITEM = re.compile(r"^\s*(?:[-*+] |\d+\. )")
VSCODE_HEADING_PUNCTUATION = "[]!/'\"#$%&()*+,./:;<=>?@\\^{}|~`"
REQUIRED_NOTEBOOKS = {
    "1-docker-foundations-and-architecture.ipynb": "# Docker Foundations and Architecture",
    "2-docker-fundamentals.ipynb": "# Docker Fundamentals",
    "3-docker-clients-registries-and-platforms.ipynb": "# Docker Clients, Registries, and Platforms",
    "4-docker-security-and-duckiedrone-boundaries.ipynb": "# Docker Security and Duckiedrone Boundaries",
    "5-run-and-inspect-containers.ipynb": "# Run and Inspect Containers",
    "6-build-and-test-a-local-image.ipynb": "# Build and Test a Local Image",
    "7-docker-volumes-bind-mounts-and-cleanup.ipynb": "# Docker Volumes, Bind Mounts, and Cleanup",
    "8-duckiedrone-docker-hosts-and-stacks.ipynb": "# Duckiedrone Docker Hosts and Stacks",
    "9-duckiedrone-platform-data-paths.ipynb": "# Duckiedrone Platform Data Paths",
    "10-duckiedrone-deployment-boundaries.ipynb": "# Duckiedrone Deployment Boundaries",
    "11-docker-contexts-and-local-targets.ipynb": "# Docker Contexts and Local Targets",
    "12-remote-duckiedrone-docker-contexts.ipynb": "# Remote Duckiedrone Docker Contexts",
    "13-dts-devel-build-and-run.ipynb": "# dts devel Build and Run",
    "14-dts-code-workbenches.ipynb": "# dts code Workbenches",
    "15-virtual-duckiedrone-connections.ipynb": "# Virtual Duckiedrone Connections",
    "16-development-containers-and-duckietown-workspaces.ipynb": "# Development Containers and Duckietown Workspaces",
}
INTERACTIVE_CHECKPOINT_NOTEBOOKS = set(REQUIRED_NOTEBOOKS)
CHECKPOINT_CODE_SOURCE = [
    "import sys",
    "from pathlib import Path",
    "",
    "working_directory = Path.cwd()",
    "parent_directory = working_directory.parent",
    'if (parent_directory / "packages").is_dir():',
    "    parent_directory_path = str(parent_directory)",
    "    sys.path.insert(0, parent_directory_path)",
    "",
    "from packages.checkpoint_self_check import display_checkpoint_self_checks",
    "",
    "display_checkpoint_self_checks()",
]


def cell_source(cell: dict[str, Any]) -> str:
    """Return a cell source regardless of its valid notebook representation."""
    source = cell["source"]
    if isinstance(source, list):
        if all(line.endswith("\n") for line in source[:-1]):
            return "".join(source)
        return "\n".join(source)
    return source


def checkpoint_data_path(notebook_name: str) -> Path:
    """Return the sidecar path implied by one numbered notebook name."""
    _, _, checkpoint_name = notebook_name.partition("-")
    return (
        CHECKPOINT_DATA_DIR / f"{checkpoint_name.removesuffix('.ipynb')}.json"
    )


def vscode_heading_fragment(heading: str) -> str:
    """Return the fragment assigned to an ASCII Markdown heading by VS Code."""
    normalized_heading = re.sub(r"\s+", "-", heading.strip().lower())
    return "".join(
        character
        for character in normalized_heading
        if character not in VSCODE_HEADING_PUNCTUATION
    ).strip("-")


def assert_reveal_self_check(notebook_name: str) -> None:
    """Check one interactive checkpoint without embedding its data in a notebook."""
    notebook_path = NOTEBOOK_DIR / notebook_name
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    markdown_source = cell_source(notebook["cells"][0])
    code_source = cell_source(notebook["cells"][1])
    checkpoint_data = json.loads(
        checkpoint_data_path(notebook_name).read_text(encoding="utf-8"),
    )

    assert set(checkpoint_data) == {"checkpoints"}
    assert code_source.splitlines() == CHECKPOINT_CODE_SOURCE
    assert (
        "Write or select a response before revealing the answer."
        in markdown_source
    )

    checkpoints = checkpoint_data["checkpoints"]
    assert isinstance(checkpoints, list) and checkpoints
    checkpoint_ids = set()
    for checkpoint in checkpoints:
        assert isinstance(checkpoint, dict)
        required_fields = {"id", "question", "model_answer", "evidence"}
        if "choices" in checkpoint:
            assert set(checkpoint) == required_fields | {
                "choices",
                "correct_choice",
            }
            choices = checkpoint["choices"]
            correct_choice = checkpoint["correct_choice"]
            assert isinstance(choices, list) and len(choices) >= 2
            assert len(choices) == len(set(choices))
            assert all(
                isinstance(choice, str) and choice.strip()
                for choice in choices
            )
            assert (
                isinstance(correct_choice, str) and correct_choice in choices
            )
        else:
            assert set(checkpoint) == required_fields

        checkpoint_id = checkpoint["id"]
        question = checkpoint["question"]
        model_answer = checkpoint["model_answer"]
        evidence = checkpoint["evidence"]
        assert isinstance(checkpoint_id, str) and checkpoint_id
        assert isinstance(question, str) and question
        assert isinstance(model_answer, str) and model_answer
        assert isinstance(evidence, list) and evidence
        assert question not in markdown_source
        assert model_answer not in markdown_source
        assert checkpoint_id not in checkpoint_ids
        checkpoint_ids.add(checkpoint_id)

        for evidence_item in evidence:
            assert set(evidence_item) == {"label", "anchor"}
            source_section = evidence_item["label"]
            anchor = evidence_item["anchor"]
            assert isinstance(source_section, str) and source_section
            assert isinstance(anchor, str) and anchor.startswith("#")
            assert f"## {source_section}" in markdown_source
            assert anchor == f"#{vscode_heading_fragment(source_section)}"


def test_notebook_cells_have_consistent_metadata() -> None:
    """Keep notebook cells compatible with the reviewed LX convention."""
    notebook_paths = sorted(NOTEBOOK_DIR.glob("*.ipynb"))
    assert set(REQUIRED_NOTEBOOKS) == {path.name for path in notebook_paths}

    for notebook_path in notebook_paths:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        assert notebook["nbformat"] == 4
        expected_cell_count = (
            2 if notebook_path.name in INTERACTIVE_CHECKPOINT_NOTEBOOKS else 1
        )
        assert len(notebook["cells"]) == expected_cell_count

        for cell in notebook["cells"]:
            assert isinstance(cell["metadata"], dict)
            assert isinstance(cell["id"], str)
            assert cell["id"]
            assert cell["id"] == cell["metadata"]["id"]

        markdown_cell = notebook["cells"][0]
        assert markdown_cell["cell_type"] == "markdown"
        assert markdown_cell["metadata"]["language"] == "markdown"
        assert cell_source(markdown_cell).startswith(
            REQUIRED_NOTEBOOKS.get(notebook_path.name, "#"),
        )

        if notebook_path.name in INTERACTIVE_CHECKPOINT_NOTEBOOKS:
            code_cell = notebook["cells"][1]
            assert code_cell["cell_type"] == "code"
            assert code_cell["metadata"]["language"] == "python"


def test_checkpoint_data_matches_interactive_notebooks() -> None:
    """Keep every interactive Docker notebook paired with one sidecar."""
    expected_paths = {
        checkpoint_data_path(notebook_name)
        for notebook_name in INTERACTIVE_CHECKPOINT_NOTEBOOKS
    }
    assert set(CHECKPOINT_DATA_DIR.glob("*.json")) == expected_paths

    for notebook_name in INTERACTIVE_CHECKPOINT_NOTEBOOKS:
        assert_reveal_self_check(notebook_name)


def test_shared_checkpoint_self_check_helper_is_valid() -> None:
    """Keep the reusable checkpoint implementation available and parseable."""
    helper_source = CHECKPOINT_SELF_CHECK_PATH.read_text(encoding="utf-8")
    ast.parse(helper_source, filename=str(CHECKPOINT_SELF_CHECK_PATH))

    for required_text in (
        "class CheckpointSelfCheck",
        "def load_checkpoint_definitions",
        "def render_model_answer",
        "def display_checkpoint_self_checks",
        "Checkbox",
        "Reveal answer",
        "Try again",
    ):
        assert required_text in helper_source


def test_model_answer_uses_compact_paragraph_spacing() -> None:
    """Keep wrapped model answers readable in the notebook renderer."""
    self_check = checkpoint_self_check.CheckpointSelfCheck(
        question_number=1,
        question="Question",
        checkpoint_id="checkpoint",
        checkpoint_data_relative_path=Path("checkpoint_data/checkpoint.json"),
    )

    model_answer_state = self_check.model_answer.get_state()
    assert "checkpoint-model-answer" in model_answer_state["_dom_classes"]
    assert (
        ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p {"
        "line-height: 1.5;"
        "margin: 0 0 8px;"
        "}"
        in checkpoint_self_check.CHECKPOINT_WIDGET_STYLE
    )
    assert (
        ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p:last-child {"
        "margin-bottom: 0;"
        "}"
        in checkpoint_self_check.CHECKPOINT_WIDGET_STYLE
    )

    self_check.answer.value = "Response"
    with patch.object(
        checkpoint_self_check,
        "load_model_answer",
        return_value=("Answer", [{"label": "Source", "anchor": "#source"}]),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert self_check.model_answer.layout.display == ""
    assert "<strong>Model answer:</strong> Answer" in self_check.model_answer.value
    assert "<a href='#source' onclick='event.preventDefault()'>Source</a>" in self_check.model_answer.value


def test_markdown_lists_are_spaced() -> None:
    """Keep rendered lists readable for beginners."""
    documents = [README_PATH.read_text(encoding="utf-8")]

    for notebook_path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        documents.extend(cell_source(cell) for cell in notebook["cells"])

    for document in documents:
        lines = document.splitlines()
        has_tight_list = any(
            LIST_ITEM.match(line) and LIST_ITEM.match(next_line)
            for line, next_line in pairwise(lines)
        )
        assert not has_tight_list


def test_docker_exercise_build_context_is_complete() -> None:
    """Keep the small Dockerfile exercise ready to build and inspect."""
    expected_files = {".dockerignore", "Dockerfile", "server.py"}
    assert expected_files == {
        path.name for path in EXERCISE_DIR.iterdir() if path.is_file()
    }

    dockerfile = (EXERCISE_DIR / "Dockerfile").read_text(encoding="utf-8")
    for instruction in (
        "FROM cgr.dev/chainguard/python:latest@sha256:780029a86e72bf3a58b1795cb77ab73b8f48dfea8c94ab154345396dc3d3237a",
        "WORKDIR /app",
        "COPY --chown=65532:65532 server.py ./",
        "USER nonroot",
        "EXPOSE 8080",
        'ENTRYPOINT ["/usr/bin/python"]',
        'CMD ["server.py"]',
    ):
        assert instruction in dockerfile

    server_path = EXERCISE_DIR / "server.py"
    server_source = server_path.read_text(encoding="utf-8")
    ast.parse(server_source, filename=str(server_path))
    assert 'HOST = "0.0.0.0"' in server_source
    assert "PORT = 8080" in server_source
    assert "ThreadingHTTPServer" in server_source


def test_readme_has_shared_lx_structure() -> None:
    """Keep the README aligned with the reviewed LX structure."""
    readme = README_PATH.read_text(encoding="utf-8")
    assert "TODO" not in readme
    assert "`Software: ente`; `Hardware: DD24-B`" in readme
    for heading in (
        "## Notebooks",
        "## What you need",
        "## Complete the Docker exercise",
        "## For LX authors",
    ):
        assert heading in readme
    assert "pytest tests/" in readme
