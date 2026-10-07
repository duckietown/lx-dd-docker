"""Structural checks for the reviewed 12-notebook Docker LX.

Run python3 -m pytest tests/ from the repository root. These checks validate
notebook structure, links, presentation, and checkpoint integration without
running Docker activities. Editorial wording remains a human review task.
"""

import ast
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import nbformat
import pytest

from packages import checkpoint_self_check

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
CHECKPOINT_DATA_DIR = ROOT / "checkpoint_data"
REQUIRED_NOTEBOOKS = {
    "1-introduction-to-docker.ipynb": "# Introduction to Docker",
    "2-docker-containers-images-and-safe-local-practice.ipynb": "# Practicing with Docker in Duckietown",
    "3-docker-clients-registries-and-platforms.ipynb": "# Docker Clients, Registries, and Platforms",
    "4-docker-security-and-duckiedrone-boundaries.ipynb": "# Docker Security and Duckiedrone Boundaries",
    "5-run-and-inspect-containers.ipynb": "# Run and Inspect Containers",
    "6-build-and-test-a-local-image.ipynb": "# Build and Test a Local Image",
    "7-docker-volumes-bind-mounts-and-cleanup.ipynb": "# Docker Volumes, Bind Mounts, and Cleanup",
    "8-duckiedrone-docker-hosts-and-stacks.ipynb": "# Duckiedrone Docker Hosts and Stacks",
    "9-duckiedrone-container-communication.ipynb": "# Communication Between Containers",
    "10-docker-contexts-and-local-targets.ipynb": "# Docker Contexts and Local Targets: choosing the right host for a command",
    "11-other-docker-uses-in-duckietown.ipynb": "# Docker Behind the Duckietown Shell",
    "12-development-containers-and-duckietown-workspaces.ipynb": "# The Duckietown Workspace: Docker for Development",
}

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
    source = cell["source"]
    return "".join(source) if isinstance(source, list) else source


def load_notebook(name: str) -> dict[str, Any]:
    return json.loads((NOTEBOOK_DIR / name).read_text())


def markdown_source(notebook: dict[str, Any]) -> str:
    return "\n\n".join(
        cell_source(c)
        for c in notebook["cells"]
        if c["cell_type"] == "markdown"
    )


def heading_fragment(title: str) -> str:
    """Match VS Code's heading anchors, including inline code in titles."""
    title = re.sub(r"\s+", "-", title.strip().lower())
    return title.translate(
        str.maketrans("", "", "[]!/'\"#$%&()*+,./:;<=>?@\\^{}|~`")
    ).strip("-")


def without_code(source: str) -> str:
    return re.sub(
        r"^```[^\n]*\n.*?^```\s*$", "", source, flags=re.MULTILINE | re.DOTALL
    )


class Markup(HTMLParser):
    def __init__(self, source: str) -> None:
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.elements.append((tag, dict(attrs)))


def anchors(source: str) -> set[str]:
    text = without_code(source)
    headings = re.findall(r"^#{1,6} (.+)$", text, re.MULTILINE)
    return {heading_fragment(h) for h in headings} | {
        attrs["id"] for _, attrs in Markup(text).elements if "id" in attrs
    }


def links(source: str) -> list[str]:
    text = without_code(source)
    result = re.findall(r"!?\[[^\]\n]*\]\(([^\s)]+)\)", text)
    for tag, attrs in Markup(text).elements:
        attr = "src" if tag == "img" else "href"
        if tag in {"a", "img"} and attr in attrs:
            result.append(attrs[attr])
    return result


def assert_local_links(source: str, path: Path) -> None:
    for link in links(source):
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (
            (path.parent / unquote(url.path)).resolve() if url.path else path
        )
        assert target.is_file(), f"{path.name}: missing target {link}"
        if url.fragment and target.suffix in {".md", ".ipynb"}:
            target_source = target.read_text()
            if target.suffix == ".ipynb":
                target_source = markdown_source(json.loads(target_source))
            assert unquote(url.fragment) in anchors(target_source), (
                f"{path.name}: missing anchor {link}"
            )


def assert_layout(notebook: dict[str, Any]) -> None:
    cells = notebook["cells"]
    assert [c["cell_type"] for c in cells] == [
        "markdown",
        "markdown",
        "code",
        "markdown",
    ]
    logo = cell_source(cells[0])
    assert re.fullmatch(
        r"\s*<p[^>]*>\s*<a[^>]*>\s*<img[^>]*>\s*</a>\s*</p>\s*", logo
    )
    images = [attrs for tag, attrs in Markup(logo).elements if tag == "img"]
    assert images == [
        {
            "src": "../assets/images/dtlogo.png",
            "alt": "Duckietown Logo",
            "width": "30%",
        }
    ]
    lesson = cell_source(cells[1])
    assert "dtlogo.png" not in lesson
    assert lesson.count("## Checkpoint\n") == 1
    assert "## Further reading\n" in lesson
    assert lesson.index("## Further reading\n") < lesson.index(
        "## Checkpoint\n"
    )
    tail = lesson.split("## Checkpoint\n", 1)[1]
    assert "Run the self-check in the next cell" in tail
    assert not re.search(r"^## ", tail, re.MULTILINE)
    assert cell_source(cells[2]).splitlines() == CHECKPOINT_CODE_SOURCE
    summary = cell_source(cells[3])
    assert summary.startswith("## Summary and conclusions\n\n")
    assert markdown_source(notebook).count("## Summary and conclusions\n") == 1
    assert len(summary.split()) < 120


def assert_presentation(notebook: dict[str, Any]) -> None:
    """Styles must share the lesson cell with the material they format."""
    lesson = cell_source(notebook["cells"][1])
    for cell in (notebook["cells"][0], notebook["cells"][-1]):
        assert "<style" not in cell_source(cell)
    styles = re.findall(r"<style>(.*?)</style>", lesson, re.DOTALL)
    has_media = bool(
        re.search(r"<(?:table|figure)\b|^\|.*\|$", lesson, re.MULTILINE)
    )
    if has_media:
        assert len(styles) == 1
        assert lesson.index("<style>") < lesson.index("# ")
        css = styles[0]
        for selector in [
            ".lx-table",
            ".lx-table caption",
            ".lx-figure",
            ".lx-figure figcaption",
            "table",
        ]:
            assert re.search(re.escape(selector) + r"\s*\{[^}]+\}", css)
        assert "caption-side: top" in css
    else:
        assert not styles
    elements = Markup(without_code(lesson)).elements
    ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
    assert len(ids) == len(set(ids)), "Duplicate HTML IDs"
    for kind, caption_tag in [("table", "caption"), ("figure", "figcaption")]:
        for match in re.finditer(
            rf"<{kind}\b([^>]*)>(.*?)</{kind}>", lesson, re.DOTALL
        ):
            attrs = dict(Markup(f"<{kind}{match[1]}>").elements[0][1])
            assert f"lx-{kind}" in attrs.get("class", "").split()
            assert re.fullmatch(rf"{kind}-[1-9]\d*", attrs.get("id", ""))
            caption = re.search(
                rf"<{caption_tag}[^>]*>(.*?)</{caption_tag}>",
                match[2],
                re.DOTALL,
            )
            assert caption
            number = attrs["id"].split("-")[1]
            assert caption[1].strip().startswith(f"{kind.title()} {number}:")


def test_notebook_inventory() -> None:
    assert set(REQUIRED_NOTEBOOKS) == {
        p.name for p in NOTEBOOK_DIR.glob("*.ipynb")
    }


@pytest.mark.parametrize("name", REQUIRED_NOTEBOOKS)
def test_notebook_structure_and_presentation(name: str) -> None:
    notebook = load_notebook(name)
    nbformat.validate(notebook)
    assert_layout(notebook)
    assert_presentation(notebook)
    ids = [c["id"] for c in notebook["cells"]]
    assert len(ids) == len(set(ids))
    for c in notebook["cells"]:
        assert c["metadata"]["id"] == c["id"]
        assert c["metadata"]["language"] == (
            "markdown" if c["cell_type"] == "markdown" else "python"
        )
        if c["cell_type"] == "markdown":
            assert cell_source(c).endswith("\n") and not cell_source(
                c
            ).endswith("\n\n")
    headings = re.findall(
        r"^# .+$", cell_source(notebook["cells"][1]), re.MULTILINE
    )
    assert headings == [REQUIRED_NOTEBOOKS[name]]
    summary = cell_source(notebook["cells"][-1])
    names = list(REQUIRED_NOTEBOOKS)
    index = names.index(name)
    if index + 1 < len(names):
        assert f"./{names[index + 1]}" in links(summary)
    else:
        assert "https://github.com/duckietown/lx-dd-middleware-ros2" in links(
            summary
        )
    assert_local_links(markdown_source(notebook), NOTEBOOK_DIR / name)


def test_readme_notebook_guide() -> None:
    path = ROOT / "README.md"
    source = path.read_text()
    assert_local_links(source, path)
    section = source.split("## Notebooks\n", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(
        r"^\| (\d+) \| \[([^]]+)\]\(\./notebooks/([^)]+)\) \| (.+) \|$",
        section,
        re.MULTILINE,
    )
    assert len(rows) == len(REQUIRED_NOTEBOOKS)
    for i, (name, title) in enumerate(REQUIRED_NOTEBOOKS.items(), 1):
        number, label, target, description = rows[i - 1]
        assert (number, label, target) == (
            str(i),
            title.removeprefix("# "),
            name,
        )
        assert description.strip()
    for title in [
        "Intended learning outcomes",
        "Run this LX",
        "Prerequisites",
        "Further reading",
        "For LX authors",
    ]:
        assert f"## {title}\n" in source
    assert "python3 -m pytest tests/" in source


def checkpoint_path(name: str) -> Path:
    return CHECKPOINT_DATA_DIR / (
        name.split("-", 1)[1].removesuffix(".ipynb") + ".json"
    )


def test_checkpoint_inventory() -> None:
    assert set(CHECKPOINT_DATA_DIR.glob("*.json")) == {
        checkpoint_path(n) for n in REQUIRED_NOTEBOOKS
    }


@pytest.mark.parametrize("name", REQUIRED_NOTEBOOKS)
def test_checkpoint_data_and_answer_links(name: str) -> None:
    data = json.loads(checkpoint_path(name).read_text())
    assert set(data) == {"checkpoints"}
    questions = data["checkpoints"]
    assert questions
    assert len({q["id"] for q in questions}) == len(questions)
    lesson = cell_source(load_notebook(name)["cells"][1])
    headings = set(re.findall(r"^#{2,6} (.+)$", lesson, re.MULTILINE))
    for q in questions:
        required = {"id", "question", "model_answer", "evidence"}
        assert set(q) == required | (
            {"choices", "correct_choice"} if "choices" in q else set()
        )
        for field in ["id", "question", "model_answer"]:
            assert isinstance(q[field], str) and q[field].strip()
        if "choices" in q:
            assert len(q["choices"]) >= 2
            assert len(set(q["choices"])) == len(q["choices"])
            assert all(isinstance(v, str) and v.strip() for v in q["choices"])
            assert q["correct_choice"] in q["choices"]
        assert q["evidence"]
        for e in q["evidence"]:
            assert set(e) == {"label", "anchor"}
            assert e["label"] in headings, f"{name}: {e}"
            assert e["anchor"] == "#" + heading_fragment(e["label"])


@pytest.mark.parametrize("name", REQUIRED_NOTEBOOKS)
def test_actual_notebook_context_loads_and_reveals_all_answers(
    name: str,
) -> None:
    """Exercise filename inference, the real sidecar, and every reveal button."""

    class Kernel:
        def get_parent(self) -> dict[str, Any]:
            return {
                "metadata": {
                    "cellId": f"vscode-notebook-cell://workspace/notebooks/{name}#checkpoint"
                }
            }

    class Shell:
        kernel = Kernel()

    with (
        patch.object(
            checkpoint_self_check, "get_ipython", return_value=Shell()
        ),
        patch.object(checkpoint_self_check, "display") as display,
    ):
        checkpoint_self_check.display_checkpoint_self_checks()
    widget = display.call_args.args[0]
    questions = json.loads(checkpoint_path(name).read_text())["checkpoints"]
    assert "checkpoint-self-checks" in widget.get_state()["_dom_classes"]
    assert len(widget.children) == len(questions) + 1
    for definition in questions:
        check = checkpoint_self_check.CheckpointSelfCheck(
            question_number=1,
            question=definition["question"],
            checkpoint_id=definition["id"],
            checkpoint_data_relative_path=checkpoint_path(name).relative_to(
                ROOT
            ),
            choices=tuple(definition["choices"])
            if "choices" in definition
            else None,
        )
        if "choices" in definition:
            index = definition["choices"].index(definition["correct_choice"])
            check.choice_options[index].value = True
        else:
            check.answer.value = "My response"
        check.reveal_answer(check.reveal_button)
        assert check.model_answer.layout.display == ""
        assert "<strong>" in check.model_answer.value
        for e in definition["evidence"]:
            assert f"href='{e['anchor']}'" in check.model_answer.value
        assert check.status.value == ""


def test_remote_context_cleanup_follows_queries() -> None:
    source = cell_source(
        load_notebook("10-docker-contexts-and-local-targets.ipynb")["cells"][1]
    )
    name = "duckiedrone-DUCKIEDRONE_NAME"
    assert source.index(f"docker context create {name}") < source.index(
        f"docker --context {name}"
    )
    assert source.rindex(f"docker --context {name}") < source.index(
        f"docker context rm {name}"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "logo-width",
        "missing-summary",
        "style-in-logo",
        "missing-style",
        "duplicate-id",
    ],
)
def test_layout_and_style_checks_reject_regressions(mutation: str) -> None:
    notebook = load_notebook("1-introduction-to-docker.ipynb")
    if mutation == "logo-width":
        notebook["cells"][0]["source"] = cell_source(
            notebook["cells"][0]
        ).replace("30%", "50%")
    elif mutation == "missing-summary":
        notebook["cells"].pop()
    elif mutation in {"style-in-logo", "missing-style"}:
        source = cell_source(notebook["cells"][1])
        style = re.search(r"<style>.*?</style>", source, re.DOTALL)[0]
        notebook["cells"][1]["source"] = source.replace(style, "")
        if mutation == "style-in-logo":
            notebook["cells"][0]["source"] = (
                cell_source(notebook["cells"][0]) + style
            )
    else:
        notebook["cells"][1]["source"] = cell_source(
            notebook["cells"][1]
        ).replace('id="figure-2"', 'id="figure-1"')
    with pytest.raises(AssertionError):
        assert_notebook_layout_and_style(notebook)


def test_link_checks_reject_missing_target_and_anchor() -> None:
    path = ROOT / "README.md"
    for link in [
        "[missing](./notebooks/nonexistent.ipynb)",
        "[missing](#no-such-heading)",
    ]:
        with pytest.raises(AssertionError):
            assert_local_links(link, path)


def test_docker_exercise_build_context_is_complete() -> None:
    """Keep the small Dockerfile exercise ready to build and inspect."""
    expected_files = {".dockerignore", "Dockerfile", "server.py"}
    assert expected_files == {
        path.name
        for path in (ROOT / "packages" / "docker_exercises").iterdir()
        if path.is_file()
    }

    dockerfile = (
        (ROOT / "packages" / "docker_exercises") / "Dockerfile"
    ).read_text(encoding="utf-8")
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

    server_path = (ROOT / "packages" / "docker_exercises") / "server.py"
    server_source = server_path.read_text(encoding="utf-8")
    ast.parse(server_source, filename=str(server_path))
    assert 'HOST = "0.0.0.0"' in server_source
    assert "PORT = 8080" in server_source
    assert "ThreadingHTTPServer" in server_source


def assert_notebook_layout_and_style(notebook: dict[str, Any]) -> None:
    assert_layout(notebook)
    assert_presentation(notebook)
