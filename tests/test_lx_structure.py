"""Structural checks for the reviewed 12-notebook Docker LX.

Run python3 -m pytest tests/ from the repository root. These checks validate
notebook structure, links, presentation, and checkpoint integration without
running Docker activities. Editorial guards enforce the agreed LX conventions;
human review remains necessary for technical accuracy and clarity.
"""

import ast
import json
import re
from collections.abc import Callable
from html import unescape
from html.parser import HTMLParser
from itertools import pairwise
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

LIST_ITEM = re.compile(r"^(?P<indent>[ \t]*)(?:[-*+] |\d+[.)] )")
UNLINKED_NOTEBOOK_REFERENCE_PATTERN = re.compile(
    r"(?<![\w\[])_*Notebooks?\s+\[?\d+",
    re.IGNORECASE,
)

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


LIST_ITEM = re.compile(r"^(?P<indent>[ \t]*)(?:[-*+] |\d+[.)] )")
MARKDOWN_TABLE_SEPARATOR = re.compile(
    r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$"
)
MARKDOWN_LITERAL_PATTERN = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?"
    r"^[ \t]*(?P=fence)[`~]*[ \t]*(?:\n|$)"
    r"|(?P<ticks>`+)(?!`).*?(?P=ticks)(?!`)"
    r"|<(?P<tag>pre|style|script|code)\b[^>]*>.*?</(?P=tag)>"
    r"|\$\$.*?\$\$|\$[^\n$]*\$"
    r"|(?<=\]\()[^\n)]*(?=\))"
    r"|<[^>\n]+>|\\.",
    re.MULTILINE | re.DOTALL,
)
ASTERISK_EMPHASIS_PATTERN = re.compile(
    r"(?<!\*)(?P<marker>\*+)(?![\s*])"
    r"(?:(?!\n[ \t]*\n).)*?\S(?P=marker)(?!\*)",
    re.DOTALL,
)
NON_ASCII_STYLE_PATTERN = re.compile(
    r"[\u00a0\u2000-\u200f\u2010-\u201f\u2026\u2028-\u202f"
    r"\u205f\u2060\ufeff\u2190-\u21ff\u2500-\u27ff"
    r"\u2900-\u297f\u2b00-\u2bff\U0001f300-\U0001faff]"
)
ACRONYM_EXPANSIONS = {
    "API": "application programming interface",
    "CPU": "central processing unit",
    "DTPS": "Duckietown Postal Service",
    "HTTP": "Hypertext Transfer Protocol",
    "ID": "identifier",
    "IDE": "integrated development environment",
    "IP": "Internet Protocol",
    "LX": "learning experience",
    "MAVLink": "Micro Air Vehicle Link",
    "OS": "operating system",
    "PEM": "Privacy Enhanced Mail",
    "ROS 2": "Robot Operating System 2",
    "SSH": "Secure Shell",
    "TCP": "Transmission Control Protocol",
    "TLS": "Transport Layer Security",
    "ToF": "time of flight",
    "UID": "user identifier",
    "URL": "Uniform Resource Locator",
    "UTC": "Coordinated Universal Time",
    "VM": "virtual machine",
    "VS Code": "Visual Studio Code",
    "YAML": "YAML Ain't Markup Language",
}
PRODUCT_NAMES = {"DD24", "PX4"}
ACRONYM_PATTERN = re.compile(
    r"\b(?:"
    + "|".join(re.escape(acronym) + "s?" for acronym in ACRONYM_EXPANSIONS)
    + r"|[A-Z][A-Z0-9]+s?)\b"
)
EDITORIAL_LITERAL_PATTERN = re.compile(
    r"<code\b[^>]*>.*?</code>|" + MARKDOWN_LITERAL_PATTERN.pattern,
    MARKDOWN_LITERAL_PATTERN.flags,
)
ROBOT_WORD = re.compile(r"(?<![\w/])robots?(?![\w/])", re.IGNORECASE)
GENERIC_ROBOT_CONTEXT = re.compile(
    r"\bgeneric robots?\b|\brobots? in general\b|\bany other robots?\b"
    r"|\bother types of robots?\b|\bfrom phones to robots\b",
    re.IGNORECASE,
)
NAME_INTRODUCTION = ", where `DUCKIEDRONE_NAME` is the name of your Duckiedrone"
NAME_EXPLANATION = re.compile(
    r"\bDUCKIEDRONE_NAME\b\s*(?:(?:is|means|represents|stands for|refers to|denotes"
    r"|should be replaced with|must be replaced with)\s+|[:=(]\s*)"
    r"[^.!?;\n]{0,100}?\b(?:name|hostname)\b"
    r"|\b(?:replace|substitute)\s+DUCKIEDRONE_NAME\s+with\s+"
    r"[^.!?;\n]{0,100}?\b(?:name|hostname)\b",
    re.IGNORECASE,
)
CONCEPT_ALIASES = {
    "PX4": ("PX4",),
    "ROS 2": (
        "ROS 2", "Robot Operating System 2", "Robot Operating System (ROS) 2",
        "Robot Operating System 2 (ROS 2)",
    ),
    "DTPS": ("DTPS", "Duckietown Postal Service", "Duckietown Postal Service (DTPS)"),
    "MAVLink": ("MAVLink", "Micro Air Vehicle Link", "Micro Air Vehicle Link (MAVLink)"),
    "MAVROS2": ("MAVROS2", "MAVROS"),
    "PID": ("PID", "PID controller", "Proportional Integral Derivative (PID)"),
    "Docker Engine": ("Docker Engine",),
    "Docker Hub": ("Docker Hub",),
    "Debian": ("Debian",),
    "Fedora": ("Fedora",),
    "Ubuntu": ("Ubuntu",),
    "Zenoh": ("Zenoh",),
    "NuttX": ("NuttX",),
    "QGroundControl": ("QGroundControl",),
    "Gimbal lock": ("Gimbal lock",),
    "shebang": ("shebang",),
    "DHCP": ("DHCP",),
    "TCP": ("TCP",),
    "UDP": ("UDP",),
    "curl": ("curl",),
}
EXTERNAL_LINK = re.compile(
    r"(?<!!)\[(?P<label>[^\]\n]+)\]\((?P<url>https?://[^\s)]+)\)"
    r"|<a\b[^>]*href=[\"']https?://[^\"']+[\"'][^>]*>(?P<html>.*?)</a>",
    re.DOTALL,
)
PROSE_WORDING_RULES = {
    "introduce examples with 'such as' or 'for example'": re.compile(
        r"\(\s*like\b|\b(?:commands?|tools?|programs?|languages?|libraries|services|things)\s+like\b"
        r"|,\s+like\s+(?:our|the)\s+(?:\w+\s+)?example\b"
        r"|\b(?:output|results?)\s+like\s+this\b",
        re.IGNORECASE,
    ),
    "replace informal wording with direct instructional prose": re.compile(
        r"\b(?:gonna|wanna|gotta|kinda|sorta)\b"
        r"|\b(?:check\s+out|a\s+bunch\s+of|pretty\s+much|you\s+guys|and\s+stuff)\b",
        re.IGNORECASE,
    ),
    "remove accidentally repeated words": re.compile(
        r"\b(?P<word>the|a|an|is|are|of|to|with|and)\s+(?P=word)\b",
        re.IGNORECASE,
    ),
    "replace prose dash punctuation with a comma, colon, parentheses or a sentence": re.compile(
        r"(?<=[^\s|])[ \t]+-{1,2}[ \t]+(?=[^\s|])|[\u2013\u2014]",
    ),
}


def cell_source(cell: dict[str, Any]) -> str:
    source = cell["source"]
    return "".join(source) if isinstance(source, list) else source


def assert_markdown_ends_with_one_newline(source: str) -> None:
    assert source.endswith("\n"), "Markdown needs a final newline"
    assert not source.endswith("\n\n"), "Markdown needs exactly one final newline"
    assert not source.endswith((" \n", "\t\n")), "Markdown must not end with trailing whitespace"


def assert_numbered_notebook_references(source: str) -> None:
    assert UNLINKED_NOTEBOOK_REFERENCE_PATTERN.search(source) is None, (
        "Link each numbered notebook reference individually"
    )


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
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.feed(source)

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.elements.append((tag, dict(attrs)))


def anchors(source: str) -> set[str]:
    text = without_code(source)
    headings = re.findall(r"^#{1,6} (.+)$", text, re.MULTILINE)
    return {heading_fragment(h) for h in headings} | {
        value
        for _, attrs in Markup(text).elements
        if (value := attrs.get("id")) is not None
    }


def links(source: str) -> list[str]:
    text = without_code(source)
    result = re.findall(r"!?\[[^\]\n]*\]\(([^\s)]+)\)", text)
    for tag, attrs in Markup(text).elements:
        attr = "src" if tag == "img" else "href"
        value = attrs.get(attr)
        if tag in {"a", "img"} and value is not None:
            result.append(value)
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


def assert_figure_arrow_spacing(source: str) -> None:
    for pre in re.finditer(r"<pre\b[^>]*>(.*?)</pre>", source, re.DOTALL):
        rows = pre[1].splitlines()
        for index, row in enumerate(rows[:-1]):
            label = re.fullmatch(r"(?P<indent> +)\| +\S.*", row)
            if label and rows[index + 1] == label["indent"] + "v":
                assert index > 0 and rows[index - 1] == label["indent"] + "|", (
                    "Separate an arrow-action label from the preceding node with a connector row"
                )


def assert_presentation(notebook: dict[str, Any]) -> None:
    """Styles must share the lesson cell with the material they format."""
    lesson = cell_source(notebook["cells"][1])
    for cell in (notebook["cells"][0], notebook["cells"][-1]):
        assert "<style" not in cell_source(cell)
    styles = re.findall(r"<style>(.*?)</style>", lesson, re.DOTALL)
    has_media = bool(
        re.search(r"<(?:table|figure|img)\b|!\[|^\|.*\|$", lesson, re.MULTILINE)
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
    text = without_code(lesson)
    elements = Markup(text).elements
    ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
    assert len(ids) == len(set(ids)), "Duplicate HTML IDs"
    figures = [
        match.span()
        for match in re.finditer(r"<figure\b[^>]*>.*?</figure>", text, re.DOTALL)
    ]
    for image in re.finditer(r"<img\b|!\[", text):
        assert any(start <= image.start() < end for start, end in figures), (
            "Images need a numbered, captioned figure"
        )
    for kind, caption_tag in [("table", "caption"), ("figure", "figcaption")]:
        for match in re.finditer(
            rf"<{kind}\b([^>]*)>(.*?)</{kind}>", lesson, re.DOTALL
        ):
            attrs = dict(Markup(f"<{kind}{match[1]}>").elements[0][1])
            classes = attrs.get("class") or ""
            identifier = attrs.get("id") or ""
            assert f"lx-{kind}" in classes.split()
            assert re.fullmatch(rf"{kind}-[1-9]\d*", identifier)
            caption = re.search(
                rf"<{caption_tag}[^>]*>(.*?)</{caption_tag}>",
                match[2],
                re.DOTALL,
            )
            assert caption
            number = identifier.split("-")[1]
            assert caption[1].strip().startswith(f"{kind.title()} {number}:")
            reference = f"[{kind.title()} {number}](#{identifier})"
            introduction = lesson[:match.start()].rstrip().rsplit("\n\n", 1)[-1]
            assert reference in introduction, (
                f"{reference}: media needs a linked introductory sentence"
            )
            assert introduction.endswith((".", "!", "?")), (
                f"{reference}: the introduction must end as a sentence, not with a colon"
            )
            if kind == "figure":
                assert_figure_arrow_spacing(match[0])


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
            assert_markdown_ends_with_one_newline(cell_source(c))
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
    assert "TODO" not in source
    assert "# Learning Experience (LX): Docker on the Duckiedrone\n" in source
    assert "`Software: ente`; `Hardware: DD24-B`" in source
    assert re.findall(r"^## .+$", source, re.MULTILINE) == [
        "## Intended learning outcomes",
        "## Run this LX",
        "## Notebooks",
        "## Prerequisites",
        "## Further reading",
        "## For LX authors",
    ]
    assert_local_links(source, path)
    section = source.split("## Notebooks\n", 1)[1].split("\n## ", 1)[0]
    assert "| # | Notebook | What you will learn or do |\n| --- | --- | --- |" in section
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
    prerequisites = source.split("## Prerequisites\n", 1)[1].split("\n## ", 1)[0]
    assert re.findall(r"^### .+$", prerequisites, re.MULTILINE) == [
        "### Choose the terminal and daemon",
        "### Robot and project activities",
        "### Interactive checkpoints",
    ]
    assert "`dts code editor`" in prerequisites
    assert "Jupyter/IPython" in prerequisites
    assert "`ipywidgets`" in prerequisites
    assert "python3 -m pytest tests/" in source


def test_numbered_notebook_references_are_individually_linked() -> None:
    assert_numbered_notebook_references((ROOT / "README.md").read_text())
    for name in REQUIRED_NOTEBOOKS:
        assert_numbered_notebook_references(markdown_source(load_notebook(name)))


@pytest.mark.parametrize(
    "source",
    [
        "See [Notebook 2](./2-lesson.ipynb).",
        "Read [Notebook 1](./1-lesson.ipynb) and [Notebook 2](./2-lesson.ipynb).",
        "Work through the notebooks in order.",
    ],
)
def test_numbered_notebook_references_accept_direct_links(source: str) -> None:
    assert_numbered_notebook_references(source)


@pytest.mark.parametrize(
    "source",
    [
        "See Notebook 2.",
        "Read Notebooks 1-4.",
        "__Notebook 9:__ inspect the deployment.",
        "Read Notebooks [1-4](./1-lesson.ipynb).",
    ],
)
def test_numbered_notebook_references_reject_unlinked_and_grouped_numbers(source: str) -> None:
    with pytest.raises(AssertionError, match="Link each numbered notebook reference"):
        assert_numbered_notebook_references(source)


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


def test_platform_example_is_output_not_command() -> None:
    notebook = load_notebook("3-docker-clients-registries-and-platforms.ipynb")
    source = cell_source(notebook["cells"][1])
    assert "```shell\nlinux/arm64\n```" in source
    assert "```bash\nlinux/arm64\n```" not in source


def test_workspace_architecture_is_captioned() -> None:
    notebook = load_notebook("12-development-containers-and-duckietown-workspaces.ipynb")
    source = cell_source(notebook["cells"][1])
    figures = re.findall(r"<figure\b[^>]*>.*?</figure>", source, re.DOTALL)
    assert any("outer Docker daemon" in figure for figure in figures)


@pytest.mark.parametrize("source", ["A sentence.\n", "First paragraph.\n\nLast paragraph.\n"])
def test_markdown_final_newline_accepts_complete_cells(source: str) -> None:
    assert_markdown_ends_with_one_newline(source)


@pytest.mark.parametrize("source", ["A sentence.", "A sentence.\n\n", "A sentence. \n", "A sentence.\t\n"])
def test_markdown_final_newline_rejects_missing_extra_and_whitespace(source: str) -> None:
    with pytest.raises(AssertionError, match="Markdown"):
        assert_markdown_ends_with_one_newline(source)


def test_markdown_lists_are_spaced() -> None:
    """Keep rendered prose lists readable without changing literal examples."""
    documents = [cell_source(cell) for name in REQUIRED_NOTEBOOKS
                 for cell in load_notebook(name)["cells"] if cell["cell_type"] == "markdown"]
    documents.append((ROOT / "README.md").read_text())
    for document in documents:
        lines = prose_without_literals(document).splitlines()
        has_tight_list = any(
            LIST_ITEM.match(line) and LIST_ITEM.match(next_line)
            for line, next_line in pairwise(lines)
        )
        assert not has_tight_list


@pytest.mark.parametrize(
    "diagram",
    [
        "    Source\n      |\n      | Action\n      v\n    Target\n",
        "    Source\n      |\n      v\n    Target\n",
        "    Source\n      +-> Target\n      |     A node annotation\n",
        "    +------+\n    | Node |\n    +------+\n",
    ],
)
def test_figure_arrow_spacing_accepts_separated_labels_and_other_diagrams(diagram: str) -> None:
    assert_figure_arrow_spacing(f"<pre>\n{diagram}</pre>")


@pytest.mark.parametrize(
    "diagram",
    [
        "    Source\n      | Action\n      v\n    Target\n",
        "    Source\n    |\n      | Action\n      v\n    Target\n",
    ],
)
def test_figure_arrow_spacing_rejects_labels_touching_nodes(diagram: str) -> None:
    with pytest.raises(AssertionError, match="Separate an arrow-action label"):
        assert_figure_arrow_spacing(f"<pre>\n{diagram}</pre>")


@pytest.mark.parametrize(
    "mutation",
    [
        "logo-width",
        "missing-summary",
        "style-in-logo",
        "missing-style",
        "duplicate-id",
        "image-outside-figure",
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
        style_match = re.search(r"<style>.*?</style>", source, re.DOTALL)
        assert style_match is not None
        style = style_match[0]
        notebook["cells"][1]["source"] = source.replace(style, "")
        if mutation == "style-in-logo":
            notebook["cells"][0]["source"] = (
                cell_source(notebook["cells"][0]) + style
            )
    elif mutation == "duplicate-id":
        notebook["cells"][1]["source"] = cell_source(
            notebook["cells"][1]
        ).replace('id="figure-2"', 'id="figure-1"')
    else:
        notebook["cells"][1]["source"] = (
            cell_source(notebook["cells"][1])
            + '\n<img src="../assets/images/VScode-contexts.jpg" alt="Docker contexts">\n'
        )
    with pytest.raises(AssertionError):
        assert_notebook_layout_and_style(notebook)


@pytest.mark.parametrize(
    ("introduction", "error"),
    [
        ("The comparison follows.", "linked introductory sentence"),
        ("See [Figure 1](#figure-2).", "linked introductory sentence"),
        ("See [Figure 1](#figure-1):", "sentence, not with a colon"),
    ],
)
def test_media_introductions_reject_missing_links_and_colons(
    introduction: str, error: str,
) -> None:
    notebook = load_notebook("1-introduction-to-docker.ipynb")
    source = cell_source(notebook["cells"][1])
    figure = re.search(r'<figure\b[^>]*\bid="figure-1"[^>]*>', source)
    assert figure is not None
    paragraph_start = source.rfind("\n\n", 0, figure.start())
    earlier = source[:paragraph_start].rstrip()
    paragraph_start = earlier.rfind("\n\n") + len("\n\n")
    notebook["cells"][1]["source"] = (
        source[:paragraph_start] + introduction + "\n\n" + source[figure.start():]
    )
    with pytest.raises(AssertionError, match=error):
        assert_presentation(notebook)


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


def reference_sections(source: str) -> list[tuple[int, int]]:
    """Locate further-reading sections through the next peer or higher heading."""
    prose = EDITORIAL_LITERAL_PATTERN.sub(
        lambda match: re.sub(r"[^\n]", " ", match.group(0)), source,
    )
    headings = list(re.finditer(r"^[ \t]*(#{1,6})[ \t]+([^\n]+)", prose, re.MULTILINE))
    sections = []
    for number, heading in enumerate(headings):
        if not re.match(
            r"(?:further reading|references?|sources?|additional resources?|external links|bibliography)\b",
            heading[2],
            re.IGNORECASE,
        ):
            continue
        end = next(
            (following.start() for following in headings[number + 1:] if len(following[1]) <= len(heading[1])),
            len(source),
        )
        sections.append((heading.start(), end))
    return sections


def mask_editorial_literal(match: re.Match[str]) -> str:
    """Retain a placeholder token without changing offsets or paragraph boundaries."""
    literal = match.group(0)
    masked = re.sub(r"[^\n]", " ", literal)
    if (
        literal.startswith(("`", "<code"))
        and not literal.startswith("```")
        and "DUCKIEDRONE_NAME" in literal
    ):
        position = literal.index("DUCKIEDRONE_NAME")
        end = position + len("DUCKIEDRONE_NAME")
        masked = masked[:position] + "DUCKIEDRONE_NAME" + masked[end:]
    return masked


def editorial_prose(source: str, *, exclude_references: bool = False) -> str:
    """Retain prose and placeholder tokens while excluding executable examples."""
    if exclude_references:
        for start, end in reversed(reference_sections(source)):
            source = source[:start] + re.sub(r"[^\n]", " ", source[start:end]) + source[end:]
    source = EDITORIAL_LITERAL_PATTERN.sub(mask_editorial_literal, source)
    source = re.sub(r"__|\*\*|(?<!\w)[*_]|[*_](?!\w)", "", source)
    return unescape(re.sub(r"^[ \t]*#+[^\n]*", "", source, flags=re.MULTILINE))


def assert_duckiedrone_name_explained_once(documents: list[tuple[str, str]]) -> None:
    """Use the standard introduction once, in the placeholder's first paragraph."""
    first_use = None
    definition = None
    for context, source in documents:
        prose = editorial_prose(source)
        for number, (raw, paragraph) in enumerate(zip(source.split("\n\n"), prose.split("\n\n"), strict=True)):
            if "DUCKIEDRONE_NAME" in raw and first_use is None:
                first_use = (context, number)
            for _match in NAME_EXPLANATION.finditer(paragraph):
                assert definition is None, f"{context}: repeated DUCKIEDRONE_NAME explanation; first at {definition}"
                assert first_use == (context, number), f"{context}: explain DUCKIEDRONE_NAME in its first-use paragraph ({first_use})"
                literal_spans = [literal.span() for literal in EDITORIAL_LITERAL_PATTERN.finditer(raw)]
                introductions = re.finditer(re.escape(NAME_INTRODUCTION), raw)
                assert any(
                    not any(start <= introduction.start() < end for start, end in literal_spans)
                    for introduction in introductions
                ), (
                    f"{context}: introduce DUCKIEDRONE_NAME using {NAME_INTRODUCTION!r}"
                )
                definition = (context, number)
    assert first_use is None or definition is not None, f"{first_use}: explain DUCKIEDRONE_NAME at its first use"


def concept_label(label: str) -> str:
    """Normalize emphasis and HTML without conflating reference titles with concepts."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>|[`*_]", "", unescape(label))).strip()


def explanatory_links(source: str) -> list[tuple[int, str]]:
    """Find term links outside literals, retaining their paragraph positions."""
    literals = [match.span() for match in EDITORIAL_LITERAL_PATTERN.finditer(source)]
    literals.extend(reference_sections(source))
    links = []
    for match in EXTERNAL_LINK.finditer(source):
        if any(start <= match.start() and end >= match.end() for start, end in literals):
            continue
        label = match.group("label") or match.group("html")
        if "`" not in label:
            links.append((source[:match.start()].count("\n\n"), concept_label(label)))
    return links


def explanatory_concepts(document_links: list[list[tuple[int, str]]]) -> dict[str, tuple[str, ...]]:
    """Recognize aliases and newly introduced single-term concept labels."""
    aliases_by_concept = dict(CONCEPT_ALIASES)
    for links in document_links:
        for _number, label in links:
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9.+-]*", label) and label.casefold() not in {
                "source", "here", "documentation", "reference", "overview", "guide",
            }:
                aliases_by_concept.setdefault(label, (label,))
    return aliases_by_concept


def assert_explanatory_concept_links(documents: list[tuple[str, str]]) -> None:
    """Link a concept once at first use, allowing later reference citations."""
    document_links = [explanatory_links(source) for _context, source in documents]
    aliases_by_concept = explanatory_concepts(document_links)
    first_use: dict[str, tuple[str, int]] = {}
    linked: dict[str, tuple[str, int]] = {}
    for (context, source), links in zip(documents, document_links, strict=True):
        prose = editorial_prose(source, exclude_references=True)
        for number, paragraph in enumerate(prose.split("\n\n")):
            for concept, aliases in aliases_by_concept.items():
                for alias in aliases:
                    if re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", paragraph, re.IGNORECASE):
                        first_use.setdefault(concept, (context, number))
                        break
            for link_number, label in links:
                if link_number != number:
                    continue
                linked_concept = next(
                    (name for name, aliases in aliases_by_concept.items() if label.casefold() in {alias.casefold() for alias in aliases}),
                    None,
                )
                if linked_concept is None:
                    continue
                assert linked_concept not in linked, f"{context}: repeated explanatory link for {linked_concept}; first at {linked.get(linked_concept)}"
                assert first_use.get(linked_concept) == (context, number), f"{context}: link {linked_concept} at its first use ({first_use.get(linked_concept)})"
                linked[linked_concept] = (context, number)


@pytest.mark.parametrize(
    "documents",
    [
        [],
        [("1", "Run the following command" + NAME_INTRODUCTION + ":\n\n```bash\nssh duckie@DUCKIEDRONE_NAME.local\n```")],
        [("1", "Run `dts duckiebot update DUCKIEDRONE_NAME`" + NAME_INTRODUCTION + "."), ("2", "`ssh duckie@DUCKIEDRONE_NAME.local`")],
        [("1", "Use this topic" + NAME_INTRODUCTION + "."), ("2", "```bash\necho DUCKIEDRONE_NAME\n```")],
        [("1", "Inspect the following path" + NAME_INTRODUCTION + ".\n\n<code>ssh duckie@DUCKIEDRONE_NAME.local\n\n</code>")],
    ],
)
def test_duckiedrone_name_explanations_accept_first_use(documents: list[tuple[str, str]]) -> None:
    assert_duckiedrone_name_explained_once(documents)


@pytest.mark.parametrize(
    "documents",
    [
        [("1", "`ssh duckie@DUCKIEDRONE_NAME.local`")],
        [("1", "`ssh duckie@DUCKIEDRONE_NAME.local`\n\nDUCKIEDRONE_NAME is your hostname.")],
        [("2", "`ssh duckie@DUCKIEDRONE_NAME.local`"), ("10", "DUCKIEDRONE_NAME is your hostname.")],
        [("1", "DUCKIEDRONE_NAME is your hostname."), ("2", "Replace DUCKIEDRONE_NAME with your Duckiedrone's name.")],
        [("1", "DUCKIEDRONE_NAME is your hostname. DUCKIEDRONE_NAME means the Duckiedrone name.")],
        [("1", "DUCKIEDRONE_NAME: your Duckiedrone's hostname."), ("2", "DUCKIEDRONE_NAME should be replaced with your Duckiedrone's name.")],
        [("1", "Use this topic, where `DUCKIEDRONE_NAME` is your Duckiedrone's name.")],
        [("1", "Use this topic, where `DUCKIEDRONE_NAME` is the Duckiedrone's name.")],
        [("1", "Use this topic, where DUCKIEDRONE_NAME is the name of your Duckiedrone.")],
        [("1", "DUCKIEDRONE_NAME is your Duckiedrone's name. <code>" + NAME_INTRODUCTION + "</code>")],
        [("1", "Use this topic" + NAME_INTRODUCTION + "."), ("2", "Use this command" + NAME_INTRODUCTION + ".")],
        [("1", "`ssh duckie@DUCKIEDRONE_NAME.local`\n\nUse this topic" + NAME_INTRODUCTION + ".")],
    ],
)
def test_duckiedrone_name_explanations_reject_missing_late_and_repeated(documents: list[tuple[str, str]]) -> None:
    with pytest.raises(AssertionError, match="DUCKIEDRONE_NAME"):
        assert_duckiedrone_name_explained_once(documents)


@pytest.mark.parametrize(
    "documents",
    [
        [("1", "[__PX4__](https://px4.io/) is autopilot software."), ("2", "PX4 publishes messages. See the [PX4 parameter reference](https://docs.px4.io/main/en/advanced_config/parameter_reference.html).")],
        [("1", '[Robot Operating System 2](https://docs.ros.org/) uses topics.\n<a href="https://dtps.org/">DTPS</a> carries messages.'), ("2", "ROS 2 and Duckietown Postal Service exchange data.")],
        [("1", "[Notebook 2](./2-example.ipynb) and [Figure 1](#figure-1)."), ("2", "[Notebook 2](./2-example.ipynb)")],
        [("1", "```text\n[PX4](https://px4.io/)\n\n[PX4](https://docs.px4.io/)\n```"), ("2", "[PX4](https://px4.io/) controls flight.")],
        [("1", "PX4 is autopilot software.\n\n## Further reading\n\n[PX4](https://px4.io/)"), ("2", "## Further reading\n\n[PX4](https://docs.px4.io/)")],
    ],
)
def test_explanatory_links_accept_first_use_and_reference_citations(documents: list[tuple[str, str]]) -> None:
    assert_explanatory_concept_links(documents)


@pytest.mark.parametrize(
    "documents",
    [
        [("1", "PX4 is autopilot software."), ("2", "[PX4](https://px4.io/) controls flight.")],
        [("1", "[__PX4__](https://px4.io/) controls flight."), ("2", "[PX4](https://docs.px4.io/main/) receives messages.")],
        [("1", "[Robot Operating System 2](https://docs.ros.org/) uses topics."), ("2", "[ROS 2](https://ros.org/) uses nodes.")],
        [("1", "[DTPS](https://dtps.org/) carries messages."), ("2", '<a href="https://docs.dtps.org/">Duckietown Postal Service</a> carries messages.')],
        [("1", "[PX4](https://px4.io/) and [__PX4__](https://docs.px4.io/) control flight.")],
        [("1", "[GNSS](https://example.org/gnss/) provides positioning."), ("2", "[GNSS](https://example.org/positioning/) provides positioning.")],
        [("1", "PX4 is autopilot software.\n\n## Further reading\n\n[PX4](https://px4.io/)\n\n## Flight software\n\n[PX4](https://docs.px4.io/) controls flight.")],
        [("1", "[Robot Operating System 2 (__ROS 2__)](https://www.ros.org/) uses topics."), ("2", "[ROS 2](https://docs.ros.org/) uses nodes.")],
        [("1", "```markdown\n## Further reading\n```\n\n[PX4](https://px4.io/) controls flight.\n\n[PX4](https://docs.px4.io/) receives commands.")],
    ],
)
def test_explanatory_links_reject_late_and_repeated_definitions(documents: list[tuple[str, str]]) -> None:
    with pytest.raises(AssertionError, match=r"first use|repeated explanatory"):
        assert_explanatory_concept_links(documents)


def assert_linked_acronym_style(source: str, context: str = "Markdown") -> None:
    """Keep a linked expansion and its parenthesized acronym inside one link."""
    literals = [match.span() for match in EDITORIAL_LITERAL_PATTERN.finditer(source)]
    for link in EXTERNAL_LINK.finditer(source):
        if any(start <= link.start() and end >= link.end() for start, end in literals):
            continue
        suffix = re.match(r"[ \t]*(?:\n[ \t]*)?\(([^()\n]+)\)", source[link.end():])
        if suffix is None:
            continue
        acronym = concept_label(suffix[1])
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?: (?:\d+|Code))?", acronym) is None:
            continue
        if re.search(r"[A-Z].*[A-Z]", acronym) is None:
            continue
        message = f"{context}: include {acronym} inside the link with its full name"
        raise AssertionError(message)


@pytest.mark.parametrize(
    "source",
    [
        "[Robot Operating System 2 (__ROS 2__)](https://www.ros.org/) uses topics.",
        '<a href="https://dtps.org/">Duckietown Postal Service (DTPS)</a> carries messages.',
        "[Micro Air Vehicle Link (MAVLink)](https://mavlink.io/) carries telemetry.",
        "[Visual Studio Code (VS Code)](https://code.visualstudio.com/) is an editor.",
        "[PX4](https://px4.io/) (autopilot software) controls flight.",
        "```markdown\n[Robot Operating System 2](https://www.ros.org/) (ROS 2)\n```",
        "`[Duckietown Postal Service](https://dtps.org/) (DTPS)` is a literal example.",
    ],
)
def test_linked_acronym_style_accepts_complete_labels_and_literals(source: str) -> None:
    assert_linked_acronym_style(source)


@pytest.mark.parametrize(
    "source",
    [
        "[Robot Operating System 2](https://www.ros.org/) (__ROS 2__) uses topics.",
        '<a href="https://dtps.org/">Duckietown Postal Service</a> (DTPS) carries messages.',
        "[Micro Air Vehicle Link](https://mavlink.io/) (MAVLink) carries telemetry.",
        "[Visual Studio Code](https://code.visualstudio.com/) (VS Code) is an editor.",
        "[Multicast DNS](https://www.rfc-editor.org/rfc/rfc6762)\n(mDNS) resolves names.",
    ],
)
def test_linked_acronym_style_rejects_split_definitions(source: str) -> None:
    with pytest.raises(AssertionError, match="inside the link"):
        assert_linked_acronym_style(source)


def assert_duckiedrone_terminology(source: str, context: str = "Markdown") -> None:
    """Require Duckiedrone for this platform, retaining explicit generic references."""
    prose = EDITORIAL_LITERAL_PATTERN.sub(
        lambda match: (
            re.sub(r"<[^>]+>", "", match.group(0))
            if match.group(0).startswith("<pre")
            else re.sub(r"[^\n]", " ", match.group(0))
        ),
        source,
    )
    prose = re.sub(r"__|\*\*|(?<!\w)[*_]|[*_](?!\w)", "", prose)
    prose = re.sub(r"\brobot operating system(?:\s+2)?\b", "ROS", prose, flags=re.IGNORECASE)
    for paragraph in re.split(r"(?<=[.!?])\s+|\n\n", prose):
        if GENERIC_ROBOT_CONTEXT.search(paragraph):
            continue
        robot = ROBOT_WORD.search(paragraph)
        assert robot is None, (
            f"{context}: use Duckiedrone instead of {robot.group(0)!r} for "
            "this platform; make a genuinely generic robot reference explicit"
        )


@pytest.mark.parametrize(
    "source",
    [
        "Connect to your Duckiedrone. The DUCKIEDRONES share the network.",
        "Robot Operating System 2 (ROS 2) transports sensor data.",
        "__Robot Operating System 2__ transports sensor data.",
        "A generic robot may use different hardware.",
        "This applies to a Duckiedrone or any other robot.",
        "An IMU appears in devices from phones to robots.",
        "`robot/basics` and <code>ROBOT_NAME</code> are literal names.",
        "<code>robot</code> is a literal resource name.",
        "```bash\ndts duckiebot update ROBOT_NAME\n```\n",
        "[Architecture](https://example.org/robots/overview)",
        "<figure><pre>robot/basics -> driver</pre></figure>",
    ],
)
def test_duckiedrone_terminology_accepts_generic_and_literal_uses(source: str) -> None:
    """Keep generic examples, software names, paths, and commands unchanged."""
    assert_duckiedrone_terminology(source)


@pytest.mark.parametrize(
    "source",
    [
        "Connect to your robot.",
        "The Robot runs this service.",
        "Start the ROBOT before continuing.",
        "Inspect the robots.",
        "The ROBOTS are on this network.",
        "<table><tr><td>Robot resources</td></tr></table>",
        "<figure><pre>base station -> robot</pre></figure>",
        "A generic robot may use different hardware. Start your robot now.",
        "Connect to the __robot__.",
    ],
)
def test_duckiedrone_terminology_rejects_platform_robot_names(source: str) -> None:
    """Check capitalization, plural forms, table text, and diagram labels."""
    with pytest.raises(AssertionError, match="use Duckiedrone"):
        assert_duckiedrone_terminology(source)


def mask_instruction_literal(match: re.Match[str]) -> str:
    """Exclude literals without joining the prose on either side."""
    literal = match.group(0)
    masked = re.sub(r"[^\n]", " ", literal)
    if re.fullmatch(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^>]*)?\s*/?>", literal):
        return masked
    return "literal " + masked


def assert_clear_prose(source: str, context: str = "Markdown") -> None:
    """Apply concrete house-style checks, not an authorship detector."""
    source = EXTERNAL_LINK.sub(mask_instruction_literal, source)
    prose = EDITORIAL_LITERAL_PATTERN.sub(mask_instruction_literal, source)
    prose = re.sub(r"__|\*\*|(?<!\w)[*_]|[*_](?!\w)", "", prose)
    prose = unescape(prose)
    for message, pattern in PROSE_WORDING_RULES.items():
        match = pattern.search(prose)
        assert match is None, f"{context}: {message}: {match.group(0)!r}"
    depth = 0
    for token in re.finditer(r"[()]|\b(?:e\.g\.|i\.e\.)(?!\w)", prose, re.IGNORECASE):
        value = token.group(0)
        if value == "(":
            depth += 1
        elif value == ")":
            depth = max(0, depth - 1)
        else:
            assert depth, (
                f"{context}: spell out {value!r} outside parentheses; "
                "use 'for example', 'such as' or 'that is'"
            )


def assert_reference_presentation(source: str, context: str = "Markdown") -> None:
    """Integrate supporting links into prose, retaining reading-list entries."""
    visible = EDITORIAL_LITERAL_PATTERN.sub(mask_editorial_literal, source)
    references = reference_sections(source)
    quotes = {'"': '"', "'": "'", "\u201c": "\u201d", "\u2018": "\u2019"}
    for link in EXTERNAL_LINK.finditer(source):
        if not visible[link.start():link.end()].strip():
            continue
        prefix = source[:link.start()].rstrip()
        suffix = source[link.end():].lstrip()
        closing_quote = quotes.get(prefix[-1:])
        assert not (closing_quote and suffix.startswith(closing_quote)), (
            f"{context}: do not enclose a linked article title in quotation marks"
        )
        label = link.group("label") or link.group("html") or ""
        label = concept_label(label)
        visible_brackets = (
            label.startswith("[")
            or (prefix.endswith("[") and suffix.startswith(("]", "\\]")))
        )
        assert not visible_brackets, f"{context}: do not add visible square brackets around a reference link"
        if any(start <= link.start() < end for start, end in references):
            continue
        paragraph_start = source.rfind("\n\n", 0, link.start()) + len("\n\n")
        if paragraph_start == 1:
            paragraph_start = 0
        paragraph_end = source.find("\n\n", link.end())
        if paragraph_end < 0:
            paragraph_end = len(source)
        leading = source[paragraph_start:link.start()]
        trailing = source[link.end():paragraph_end]
        line_prefix = leading.rsplit("\n", 1)[-1]
        if re.fullmatch(r"[ \t]*(?:[-*+] |\d+[.)] )", line_prefix):
            continue
        trailing = EXTERNAL_LINK.sub("", trailing)
        trailing = re.sub(r"\b(?:and|or)\b|[\s.,;!?]", "", trailing)
        assert trailing or (
            leading.strip() and not leading.rstrip().endswith((".", "!", "?"))
        ), f"{context}: introduce a supporting reference with prose such as 'See ...'"


@pytest.mark.parametrize(
    "source",
    [
        "Containers look like real computers.",
        "An image is static, like an archive.",
        "This behaves like the preceding example.",
        "Use commands such as `docker ps`.",
        "Supported systems (e.g., Linux) share this behavior.",
        "Inspect its state (i.e., whether it is running).",
        "One case (including nested examples (e.g., Linux)) is sufficient.",
        "Read-write access uses a non-root account and a range of 0-10.",
        "Parameters:\n\n- First value.\n- Second value.",
        "| Quantity | Unit |\n| --- | --- |\n| Frame | - |",
        "<table><tr><td>Frame</td>\n<td>-</td></tr></table>",
        "Don't stop a service that isn't yours.",
        "Switch to `root` to inspect the file.",
        "The [Guide](https://example.org) is the reference.",
        "The [Sensors - Learning Experience](https://example.org/e.g.-guide) explains this.",
        "See <a href='https://example.org'>Representations - Part 1</a>.",
        "The YAML (YAML Ain't Markup Language) file records the settings.",
        "Read <strong>the</strong> file.",
        "```text\ncheck out commands like x - y, e.g., the the command\n```",
        "<pre>check out commands like x - y, i.e., the the command</pre>",
        "<code>check out commands like x - y, e.g., the the command</code>",
        "$x - y$ and $$x \\text{ i.e. } y$$ are mathematical literals.",
    ],
)
def test_clear_prose_accepts_comparisons_titles_and_literals(source: str) -> None:
    assert_clear_prose(source)


@pytest.mark.parametrize(
    ("source", "error"),
    [
        ("Use commands like `docker ps`.", "introduce examples"),
        ("Broad commands (like `docker system prune`) affect other work.", "introduce examples"),
        ("It is running, like our sleeper example.", "introduce examples"),
        ("It may produce output like this:", "introduce examples"),
        ("Use a local daemon, e.g., the base station's daemon.", "outside parentheses"),
        ("Check the state, i.e., whether it is running.", "outside parentheses"),
        ("Examples (e.g., Linux) differ, i.e., configurations vary.", "outside parentheses"),
        ("Check out the reference.", "informal wording"),
        ("We are gonna run a bunch of commands.", "informal wording"),
        ("You guys can pretty much inspect it.", "informal wording"),
        ("It records logs and stuff.", "informal wording"),
        ("Inspect the the file.", "repeated words"),
        ("Inspect the __the__ file.", "repeated words"),
        ("Inspect <strong>the the</strong> file.", "repeated words"),
        ("The image is ready - run it.", "dash punctuation"),
        ("The image is ready -- run it.", "dash punctuation"),
        ("The image is ready\u2014run it.", "dash punctuation"),
        ("The image is ready &mdash; run it.", "dash punctuation"),
        ("The image is ready &#8211; run it.", "dash punctuation"),
    ],
)
def test_clear_prose_rejects_example_shorthand_informal_wording_and_dashes(
    source: str, error: str,
) -> None:
    with pytest.raises(AssertionError, match=error):
        assert_clear_prose(source)


@pytest.mark.parametrize(
    "source",
    [
        "See [Docker's guide](https://example.org).",
        "See [the guide](https://example.org) and [the reference](https://example.net).",
        "The [Guide](https://example.org) explains this behavior.",
        "For details, see <a href='https://example.org'>the guide</a>.",
        "## Further reading\n\n[Guide](https://example.org).",
        "## References\n\n- [Guide](https://example.org).",
        "Consult these references:\n\n- [Guide](https://example.org).",
        '`"[Guide](https://example.org)"` is literal Markdown.',
        '<code>"[Guide](https://example.org)"</code>',
        '```markdown\nFact. "[Guide](https://example.org)"\n```',
        "```markdown\nFact. [[Guide](https://example.org)]\n```",
    ],
)
def test_reference_presentation_accepts_contextual_links_and_literals(source: str) -> None:
    assert_reference_presentation(source)


@pytest.mark.parametrize(
    ("source", "error"),
    [
        ("Containers share a kernel. [Guide](https://example.org)", "supporting reference"),
        ("Containers share a kernel. [Guide](https://example.org).", "supporting reference"),
        ("Fact. [Guide](https://example.org) and [Reference](https://example.net).", "supporting reference"),
        ("[Guide](https://example.org).", "supporting reference"),
        ('See "[Guide](https://example.org)".', "quotation marks"),
        ("See '[Guide](https://example.org)'.", "quotation marks"),
        ("See \u201c[Guide](https://example.org)\u201d.", "quotation marks"),
        ("See [[Guide](https://example.org)].", "visible square brackets"),
        ("See \\[[Guide](https://example.org)\\].", "visible square brackets"),
        ("See [ [Guide](https://example.org) ].", "visible square brackets"),
        ('See "<a href="https://example.org">Guide</a>".', "quotation marks"),
        ('## Further reading\n\n"[Guide](https://example.org)".', "quotation marks"),
        ('See <a href="https://example.org">[Guide]</a>.', "visible square brackets"),
        ('See <a href="https://example.org"> <strong>[Guide]</strong> </a>.', "visible square brackets"),
        ('See <a href="https://example.org">&#91;Guide&#93;</a>.', "visible square brackets"),
    ],
)
def test_reference_presentation_rejects_dangling_and_wrapped_titles(
    source: str, error: str,
) -> None:
    with pytest.raises(AssertionError, match=error):
        assert_reference_presentation(source)


def prose_without_literals(source: str) -> str:
    """Mask code and diagrams while preserving line boundaries and indentation."""
    return MARKDOWN_LITERAL_PATTERN.sub(
        lambda match: (
            match.group(0)
            if re.match(r"</?(?:ul|ol|li|p)\b", match.group(0))
            else re.sub(r"[^\n \t]", "x", match.group(0))
        ),
        source,
    )


def assert_list_introductions(source: str, context: str = "Markdown") -> None:
    """Require a colon-ended introduction to each Markdown or HTML list."""
    prose = prose_without_literals(source)
    lines = prose.splitlines()
    active_indents: set[int] = set()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        item = LIST_ITEM.match(line)
        indent = len(line) - len(line.lstrip())
        if item is None:
            if active_indents and indent <= min(active_indents):
                active_indents.clear()
            continue
        indent = len(item["indent"].expandtabs(4))
        if indent not in active_indents:
            prefix = "\n".join(lines[:index]).rstrip()
            introduction = prefix.rsplit("\n\n", 1)[-1]
            assert introduction.endswith(":") and not introduction.startswith("#"), (
                f"{context}, Markdown line {index + 1}: a list needs a leading "
                f"sentence ending in a colon before {line.strip()!r}"
            )
        active_indents = {level for level in active_indents if level <= indent}
        active_indents.add(indent)
    for html_list in re.finditer(r"<(?:ul|ol)\b[^>]*>", prose):
        prefix = prose[:html_list.start()].rstrip().rsplit("\n\n", 1)[-1]
        introduction = re.sub(r"<[^>]+>", "", prefix).rstrip()
        assert introduction.endswith(":"), (
            f"{context}: an HTML list needs a leading sentence ending in a colon"
        )


def assert_html_tables(source: str, context: str = "Markdown") -> None:
    """Reject Markdown tables outside literal code and HTML diagrams."""
    lines = prose_without_literals(source).splitlines()
    for index, line in enumerate(lines):
        if index and "|" in lines[index - 1]:
            assert not MARKDOWN_TABLE_SEPARATOR.fullmatch(line), (
                f"{context}, Markdown line {index + 1}: use an HTML table "
                "with a numbered caption and linked introduction"
            )


@pytest.mark.parametrize(
    "source",
    [
        "Consider these cases:\n\n- First.\n\n- Second.\n",
        "Consider these cases:\n\n1. First.\n\n2. Second.\n",
        "Consider these cases:\n\n1) First.\n\n2) Second.\n",
        "Consider these cases:\n\n- A case with two parts:\n  - One.\n  - Two.\n\n- Another case.\n",
        "Consider these cases:\n\n- First.\n  A continuation.\n\n- Second.\n",
        "```text\n- Not a prose list\n1. Not a prose list\n```\n",
        "<figure><pre>\n- Not a prose list\n</pre></figure>\n",
        "Cases:\n\n<ul><li>First.</li></ul>",
        "<p>Cases:</p>\n<ol><li>First.</li></ol>",
        "<code>&lt;ul&gt; is literal HTML syntax.</code>",
    ],
)
def test_list_introductions_accept_valid_lists_and_literals(source: str) -> None:
    """Accept introduced list groups, nested lists, and literal examples."""
    assert_list_introductions(source)


@pytest.mark.parametrize(
    "source",
    [
        "- No introduction.\n",
        "1. No introduction.\n",
        "Consider these cases.\n\n- A case.\n",
        "## Consider these cases:\n\n- A case.\n",
        "Cases:\n\n- First.\n\nNew paragraph.\n\n- Another list.\n",
        "Cases:\n\n- A case with two parts.\n  - No nested introduction.\n",
        "<ul><li>No introduction.</li></ul>",
        "Cases.\n\n<ol><li>First.</li></ol>",
    ],
)
def test_list_introductions_reject_missing_colons(source: str) -> None:
    """Catch a missing introduction even after another valid list."""
    with pytest.raises(AssertionError, match="leading sentence ending in a colon"):
        assert_list_introductions(source)


@pytest.mark.parametrize(
    "source",
    [
        "<table><tr><th>Item</th><th>Meaning</th></tr></table>",
        "```text\n| Item | Meaning |\n| --- | --- |\n```\n",
        "<pre>\n| Item | Meaning |\n| --- | --- |\n</pre>\n",
        "A literal `value | other` is not a table.\n\n---\n",
    ],
)
def test_html_tables_accept_html_and_literal_examples(source: str) -> None:
    """Allow HTML tables and table syntax used only as a code example."""
    assert_html_tables(source)


@pytest.mark.parametrize(
    "source",
    [
        "| Item | Meaning |\n| --- | --- |\n| A | B |\n",
        "Item | Meaning\n--- | ---\nA | B\n",
        "| Item | Meaning |\n| :--- | ---: |\n",
        "| Item |\n| --- |\n| A |\n",
    ],
)
def test_html_tables_reject_markdown_tables(source: str) -> None:
    """Catch pipe tables with optional outer pipes or column alignment."""
    with pytest.raises(AssertionError, match="use an HTML table"):
        assert_html_tables(source)


def assert_acronym_definitions(documents: list[tuple[str, str]]) -> None:
    """Define prose acronyms on first use, once across the notebook reading order."""
    seen: set[str] = set()
    for context, source in documents:
        prose = MARKDOWN_LITERAL_PATTERN.sub(
            lambda match: re.sub(r"[^\n]", " ", match.group(0)), source,
        )
        prose = re.sub(r"\[([^\]\n]+)\]\(\s*\)", r"\1", prose)
        prose = unescape(prose).replace("_", "")
        definitions: dict[str, list[re.Match[str]]] = {}
        for acronym, expansion in ACRONYM_EXPANSIONS.items():
            label = re.escape(acronym) + "s?"
            term = re.escape(expansion)
            term = term.replace(r"\ ", r"[-\s]+") + "s?"
            pattern = rf"\b(?:{term}\s*\({label}\)|{label}\s*\({term}\))"
            definitions[acronym] = list(re.finditer(pattern, prose, re.IGNORECASE))
        encountered: set[str] = set()
        for occurrence in ACRONYM_PATTERN.finditer(prose):
            acronym = occurrence.group(0).removesuffix("s")
            if acronym in PRODUCT_NAMES or acronym in encountered:
                continue
            assert acronym in ACRONYM_EXPANSIONS, (
                f"{context}: unknown prose acronym {acronym}; add its expansion "
                "to the glossary or identify a product name explicitly"
            )
            matches = definitions[acronym]
            if acronym in seen:
                assert not matches, f"{context}: expand {acronym} only once in the LX"
            else:
                assert len(matches) == 1, (
                    f"{context}: expand {acronym} once at its first notebook use"
                )
                definition = matches[0]
                assert definition.start() <= occurrence.start() < definition.end(), (
                    f"{context}: define {acronym} at its first use, not later"
                )
                seen.add(acronym)
            encountered.add(acronym)


@pytest.mark.parametrize(
    "documents",
    [
        [("Notebook 1", "A virtual machine (VM) runs software. The VM has a kernel.")],
        [("Notebook 1", "Virtual machine (VM)."), ("Notebook 2", "The VM runs software.")],
        [("Notebook 1", "Learning experiences (LXs) include this LX.")],
        [("Notebook 1", "CPU (central processing unit) instructions.")],
        [("Notebook 1", "An integrated development environment (IDE) hosts editor tools.")],
        [("Notebook 1", "A PEM (Privacy Enhanced Mail) file contains an encoded key.")],
        [("Notebook 1", "__application programming interface (API)__ requests.")],
        [("Notebook 1", "[Micro Air Vehicle Link (MAVLink)](https://example.org/CPU).")],
        [("Notebook 1", "<table><tr><td>Duckietown Postal Service (DTPS)</td></tr></table>")],
        [("Notebook 1", "A YAML (YAML Ain't Markup Language) file.")],
        [("Notebook 1", "The time-of-flight (__ToF__) sensor measures distance.")],
        [("Notebook 1", "```text\nCPU ID HTTP\n```\n`UID` and <code>API</code> are literals.")],
        [("Notebook 1", "The DD24 uses PX4 firmware.")],
    ],
)
def test_acronym_definitions_accept_first_use_and_literals(
    documents: list[tuple[str, str]],
) -> None:
    """Handle formatting, tables, plural forms, recursive acronyms, and code exclusions."""
    assert_acronym_definitions(documents)


@pytest.mark.parametrize(
    ("documents", "message"),
    [
        ([("Notebook 1", "A CPU runs instructions.")], "first notebook use"),
        ([("Notebook 1", "A CPU runs instructions. Central processing unit (CPU).")], "first use, not later"),
        ([("Notebook 1", "A virtual machine (VM). Another virtual machine (VM).")], "once at its first"),
        ([("Notebook 1", "Virtual machine (VM)."), ("Notebook 2", "Virtual machine (VM).")], "only once"),
        ([("Notebook 1", "<table><tr><td>DTPS messaging</td></tr></table>")], "first notebook use"),
        ([("Notebook 1", "A GPU runs instructions.")], "unknown prose acronym"),
        ([("Notebook 1", "Use an IDE to edit code.")], "first notebook use"),
        ([("Notebook 1", "Read the PEM file.")], "first notebook use"),
        ([("Notebook 1", "A ToF sensor.")], "first notebook use"),
    ],
)
def test_acronym_definitions_reject_missing_late_and_repeated_expansions(
    documents: list[tuple[str, str]], message: str,
) -> None:
    """Reject missing, late, repeated, and untracked acronym definitions."""
    with pytest.raises(AssertionError, match=message):
        assert_acronym_definitions(documents)


def asterisk_emphasis_matches(source: str) -> list[re.Match[str]]:
    """Find emphasis delimiters without treating literal code as prose."""
    prose = MARKDOWN_LITERAL_PATTERN.sub(
        lambda match: re.sub(r"[^\n]", "x", match.group(0)), source,
    )
    return list(ASTERISK_EMPHASIS_PATTERN.finditer(prose))


def assert_markdown_formatting(source: str, context: str = "Markdown") -> None:
    """Require underscore emphasis, ASCII typography, and ASCII figures."""
    assert not asterisk_emphasis_matches(source), (
        f"{context}: use _ for italic and __ for bold, not asterisk emphasis"
    )
    decoded_source = unescape(source)
    disallowed = NON_ASCII_STYLE_PATTERN.search(decoded_source)
    assert disallowed is None, (
        f"{context}: use ASCII instead of Unicode arrows, line graphics, "
        f"smart punctuation, decorative symbols, or invisible spacing "
        f"(U+{ord(disallowed.group(0)):04X})"
    )
    figures = re.finditer(r"<figure\b[^>]*>.*?</figure>", source, re.DOTALL)
    for figure in figures:
        figure_source = figure.group(0)
        entities = re.finditer(
            r"&(?:#(?:[xX][0-9a-fA-F]+|\d+)|[A-Za-z][A-Za-z0-9]*);?",
            figure_source,
        )
        for entity in entities:
            decoded_entity = unescape(entity.group(0))
            assert not decoded_entity.startswith(("<", ">")), (
                f"{context}: use literal > and < in figures, not HTML entities"
            )
        decoded_figure = unescape(figure_source)
        assert decoded_figure.isascii(), (
            f"{context}: figures must contain only ASCII characters"
        )


@pytest.mark.parametrize(
    "source",
    [
        "_italic_ and __bold__ and ___both___",
        "`*args` and `**kwargs` and `*.py`",
        "``literal `*text*` ``",
        "```python\nresult = value * factor\n# **literal**\n```\n",
        "~~~text\n*not emphasis*\n~~~~\n",
        r"\*literal\* and \*\*literal\*\*",
        "* list item\n\n***\n",
        "$a*b*c$ and $$x**2$$",
        "<figure><pre>*literal* <--> **literal**</pre></figure>",
        "<figure><pre>a > b < c &amp; d &#38; e &quot;quoted&quot;</pre></figure>",
        "Scientific prose: \u03b1 at 30\u00b0 is allowed outside figures.",
        "ASCII diagram: +---+ -> next <- previous <-> peer",
    ],
)
def test_markdown_formatting_accepts_literal_content(source: str) -> None:
    """Do not mistake code, equations, or literal asterisks for emphasis."""
    assert_markdown_formatting(source)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("*italic*", "asterisk emphasis"),
        ("**bold**", "asterisk emphasis"),
        ("***both***", "asterisk emphasis"),
        ("****nested bold****", "asterisk emphasis"),
        ("**bold `command` text**", "asterisk emphasis"),
        ("<figure><pre>a &gt; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &lt; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &GT; b &LT; c</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#62; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#60; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#x3c; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#x3e; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#X003C; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#00062; b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#62 b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &#x3c b</pre></figure>", "literal > and <"),
        ("<figure><pre>a &gt b</pre></figure>", "literal > and <"),
        ("<figure><pre>a \u03b1 b</pre></figure>", "ASCII"),
        ("<figure><pre>a &#8594; b</pre></figure>", "ASCII"),
        ("<figure><figcaption>\u201cCaption\u201d</figcaption></figure>", "ASCII"),
        ("images \u2192 layers", "ASCII"),
        ("```text\nclient \u2500\u2500> daemon\n```\n", "ASCII"),
        ("```text\n\u2514\u2500 file\n```\n", "ASCII"),
        ("a &rarr; b", "ASCII"),
        ("a &#x2192; b", "ASCII"),
        ("\u201csmart quotes\u201d", "ASCII"),
        ("Docker\u2019s daemon", "ASCII"),
        ("word\u2014word", "ASCII"),
        ("word\u2026", "ASCII"),
        ("\u2713 complete", "ASCII"),
        ("\U0001f680 ready", "ASCII"),
        ("hidden\u200bspace", "ASCII"),
        ("nonbreaking\u00a0space", "ASCII"),
    ],
)
def test_markdown_formatting_rejects_disallowed_forms(
    source: str, message: str,
) -> None:
    """Reject each requested formatting violation independently."""
    with pytest.raises(AssertionError, match=message):
        assert_markdown_formatting(source)


@pytest.mark.parametrize(
    "rule",
    [
        assert_linked_acronym_style,
        assert_duckiedrone_terminology,
        assert_clear_prose,
        assert_reference_presentation,
        assert_list_introductions,
        assert_html_tables,
        assert_markdown_formatting,
    ],
)
def test_notebook_prose_follows_editorial_style(
    rule: Callable[[str, str], None],
) -> None:
    for name in REQUIRED_NOTEBOOKS:
        notebook = load_notebook(name)
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                rule(cell_source(cell), f"{name}, Cell {number}")


@pytest.mark.parametrize(
    "rule",
    [
        assert_duckiedrone_name_explained_once,
        assert_explanatory_concept_links,
        assert_acronym_definitions,
    ],
)
def test_notebook_explanations_follow_reading_order(
    rule: Callable[[list[tuple[str, str]]], None],
) -> None:
    documents = []
    for name in REQUIRED_NOTEBOOKS:
        notebook = load_notebook(name)
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                documents.append((f"{name}, Cell {number}", cell_source(cell)))
    rule(documents)
