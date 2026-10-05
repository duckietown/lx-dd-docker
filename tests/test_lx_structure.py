"""Sanity tests for the Docker learning experience.

Run from the LX root with:

    python3 -m pytest tests/

These tests validate learner material without requiring a Docker daemon, so they
can run inside the editor container or on a plain Python host.
"""

import ast
import json
import re
from collections.abc import Callable
from html import unescape
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
EXERCISE_DIR = ROOT / "packages" / "docker_exercises"
README_PATH = ROOT / "README.md"
README_EXERCISE_TOPIC = "Docker"
CHECKPOINT_DATA_DIR = ROOT / "checkpoint_data"
CHECKPOINT_SELF_CHECK_PATH = ROOT / "packages" / "checkpoint_self_check.py"
checkpoint_self_check = import_module("packages.checkpoint_self_check")
LIST_ITEM = re.compile(r"^(?P<indent>[ \t]*)(?:[-*+] |\d+[.)] )")
MARKDOWN_TABLE_SEPARATOR = re.compile(
    r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$"
)
VSCODE_HEADING_PUNCTUATION = "[]!/'\"#$%&()*+,./:;<=>?@\\^{}|~`"
UNLINKED_NOTEBOOK_REFERENCE_PATTERN = re.compile(
    r"(?<!\[)\bNotebooks?\s+\[?\d+",
    re.IGNORECASE,
)
LINUX_NETWORKING_NOTEBOOK_TITLE = (
    "Linux and Networking on the Duckiedrone"
)
LINUX_NETWORKING_LX_URL = "https://github.com/duckietown/lx-dd-linux-and-networking"
UNLINKED_CROSS_LX_REFERENCE_PATTERN = re.compile(
    r"\bnetworking LX\b",
    re.IGNORECASE,
)
REQUIRED_NOTEBOOKS = {
    "1-introduction-to-docker.ipynb": "# Introduction to Docker",
    "2-docker-containers-images-and-safe-local-practice.ipynb": "# Docker Containers, Images, and Safe Local Practice",
    "3-docker-clients-registries-and-platforms.ipynb": "# Docker Clients, Registries, and Platforms",
    "4-docker-security-and-duckiedrone-boundaries.ipynb": "# Docker Security and Duckiedrone Boundaries",
    "5-run-and-inspect-containers.ipynb": "# Run and Inspect Containers",
    "6-build-and-test-a-local-image.ipynb": "# Build and Test a Local Image",
    "7-docker-volumes-bind-mounts-and-cleanup.ipynb": "# Docker Volumes, Bind Mounts, and Cleanup",
    "8-duckiedrone-docker-hosts-and-stacks.ipynb": "# Duckiedrone Docker Hosts and Stacks",
    "9-duckiedrone-data-paths.ipynb": "# Duckiedrone Data Paths",
    "10-duckiedrone-deployment-boundaries.ipynb": "# Duckiedrone Deployment Boundaries",
    "11-docker-contexts-and-local-targets.ipynb": "# Docker Contexts and Local Targets",
    "12-remote-duckiedrone-docker-contexts.ipynb": "# Remote Duckiedrone Docker Contexts",
    "13-dts-devel-build-and-run.ipynb": "# `dts devel` Build and Run",
    "14-dts-code-workbenches.ipynb": "# `dts code` Workbenches",
    "15-virtual-duckiedrone-connections.ipynb": "# Virtual Duckiedrone Connections",
    "16-development-containers-and-duckietown-workspaces.ipynb": "# Development Containers and Duckietown Workspaces",
}
INTERACTIVE_CHECKPOINT_NOTEBOOKS = set(REQUIRED_NOTEBOOKS)
TRY_IT_HEADING_PATTERN = re.compile(r"^### Try it(?:[: ].*)?$", re.MULTILINE)
SECTION_HEADING_PATTERN = re.compile(r"^#{2,3} .+$", re.MULTILINE)
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
CHECKPOINT_TAIL = (
    "## Checkpoint\n\n"
    "Run the self-check in the next cell. Write or select a response before revealing the answer.\n"
)
PRESENTATION_STYLE = re.compile(
    r"<style>\n"
    r"\.lx-table \{\n"
    r"\s+margin: 1\.5em auto;\n"
    r"\s+text-align: left;\n"
    r"\}\n\n"
    r"\.lx-table caption \{\n"
    r"\s+caption-side: top;\n"
    r"\s+font-size: 0\.9em;\n"
    r"\s+margin-bottom: 0\.6em;\n"
    r"\s+text-align: center;\n"
    r"\}\n\n"
    r"\.lx-figure \{\n"
    r"\s+margin: 1\.5em auto;\n"
    r"\s+text-align: center;\n"
    r"\}\n\n"
    r"\.lx-figure figcaption \{\n"
    r"\s+font-size: 0\.9em;\n"
    r"\s+margin-top: 0\.6em;\n"
    r"\s+text-align: center;\n"
    r"\}\n\n"
    r"table \{\n"
    r"\s+margin: 0 auto 1\.5em;\n"
    r"\}\n\n"
    r"p:has\(> a\[id\^='table-'\]\) \{\n"
    r"\s+margin: 0;\n"
    r"\}\n\n"
    r"p:has\(> a\[id\^='table-'\]\) \+ p,\n"
    r"a\[id\^='table-'\] \+ p \{\n"
    r"\s+font-size: 0\.9em;\n"
    r"\s+margin: 1\.5em 0 0\.6em;\n"
    r"\s+text-align: center;\n"
    r"\}\n\n"
    r"p\.lx-figure \{\n"
    r"\s+margin: 1\.5em auto 0;\n"
    r"\}\n\n"
    r"p\.lx-figure \+ p \{\n"
    r"\s+font-size: 0\.9em;\n"
    r"\s+margin: 0\.6em 0 1\.5em;\n"
    r"\s+text-align: center;\n"
    r"\}\n</style>"
)
TABLE_PATTERN = re.compile(r"<table\b(?P<attrs>[^>]*)>.*?</table>", re.DOTALL)
FIGURE_PATTERN = re.compile(r"<figure\b(?P<attrs>[^>]*)>.*?</figure>", re.DOTALL)
CAPTION_PATTERN = re.compile(r"<(?:caption|figcaption)\b(?P<attrs>[^>]*)>")
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
    "IP": "Internet Protocol",
    "LX": "learning experience",
    "MAVLink": "Micro Air Vehicle Link",
    "OS": "operating system",
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


def test_notebook_linked_acronyms_include_the_acronym() -> None:
    for path in NOTEBOOK_DIR.glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                assert_linked_acronym_style(cell_source(cell), f"{path.name}, Cell {number}")


@pytest.mark.parametrize("rule", [assert_duckiedrone_name_explained_once, assert_explanatory_concept_links])
def test_notebook_explanations_follow_reading_order(rule: Callable[[list[tuple[str, str]]], None]) -> None:
    documents = []
    paths = sorted(NOTEBOOK_DIR.glob("*.ipynb"), key=lambda path: int(path.name.partition("-")[0]))
    for path in paths:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                documents.append((f"{path.name}, Cell {number}", cell_source(cell)))
    rule(documents)


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


def test_notebooks_use_duckiedrone_terminology() -> None:
    """Check every notebook Markdown cell without including the README."""
    for notebook_path in NOTEBOOK_DIR.glob("*.ipynb"):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                assert_duckiedrone_terminology(
                    cell_source(cell), f"{notebook_path.name}, Cell {number}",
                )


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


@pytest.mark.parametrize("rule", [assert_clear_prose, assert_reference_presentation])
def test_notebook_prose_follows_editorial_style(rule: Callable[[str, str], None]) -> None:
    """Check notebook prose without applying new editorial rules to the README."""
    for path in NOTEBOOK_DIR.glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                rule(cell_source(cell), f"{path.name}, Cell {number}")


def cell_source(cell: dict[str, Any]) -> str:
    """Return a cell source regardless of its valid notebook representation."""
    source = cell["source"]
    if isinstance(source, list):
        return "".join(
            line if line.endswith("\n") else f"{line}\n"
            for line in source
        )
    return source


def assert_media_introductions(source: str, context: str = "Markdown") -> None:
    """Require a linked introductory sentence immediately before each media item."""
    for label, pattern in (("Table", TABLE_PATTERN), ("Figure", FIGURE_PATTERN)):
        for media in pattern.finditer(source):
            identifier = re.search(r'\bid="([^"]+)"', media["attrs"])
            assert identifier is not None, f"{context}: {label} needs an anchor"
            anchor = identifier[1]
            numbered_anchor = re.fullmatch(rf"{label.lower()}-([1-9]\d*)", anchor)
            assert numbered_anchor is not None, (
                f"{context}: {label} needs a positive {label.lower()}-N anchor"
            )
            number = numbered_anchor[1]
            caption_tag = "caption" if label == "Table" else "figcaption"
            caption = re.search(
                rf"<{caption_tag}\b[^>]*>(.*?)</{caption_tag}>",
                media.group(0),
                re.DOTALL,
            )
            assert caption is not None, f"{context}: {label} needs a numbered {caption_tag}"
            caption_text = concept_label(caption[1])
            assert re.match(rf"{label}\s+{number}\s*:", caption_text), (
                f"{context}: {caption_tag} must start with '{label} {number}:'"
            )
            reference = f"[{label} {number}](#{anchor})"
            introduction = source[:media.start()].rstrip().rsplit("\n\n", 1)[-1]
            assert reference in introduction, (
                f"{context}: the leading sentence must link to {reference}"
            )
            assert introduction.endswith((".", "!", "?")), (
                f"{context}: the introduction to {reference} must end as a "
                "sentence, not with a colon"
            )


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


@pytest.mark.parametrize("notebook_name", REQUIRED_NOTEBOOKS)
def test_notebook_lists_have_colon_introductions(notebook_name: str) -> None:
    """Apply the list-introduction rule to every Markdown cell."""
    notebook = json.loads((NOTEBOOK_DIR / notebook_name).read_text(encoding="utf-8"))
    for number, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] == "markdown":
            assert_list_introductions(cell_source(cell), f"{notebook_name}, Cell {number}")


@pytest.mark.parametrize("notebook_name", REQUIRED_NOTEBOOKS)
def test_notebook_tables_are_html(notebook_name: str) -> None:
    """Apply the HTML-table rule to every Markdown cell."""
    notebook = json.loads((NOTEBOOK_DIR / notebook_name).read_text(encoding="utf-8"))
    for number, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] == "markdown":
            assert_html_tables(cell_source(cell), f"{notebook_name}, Cell {number}")


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
        ([("Notebook 1", "A ToF sensor.")], "first notebook use"),
    ],
)
def test_acronym_definitions_reject_missing_late_and_repeated_expansions(
    documents: list[tuple[str, str]], message: str,
) -> None:
    """Reject missing, late, repeated, and untracked acronym definitions."""
    with pytest.raises(AssertionError, match=message):
        assert_acronym_definitions(documents)


def test_notebook_acronyms_are_defined_once_in_reading_order() -> None:
    """Ignore README definitions and read notebooks in numeric, not lexical, order."""
    notebook_paths = sorted(
        NOTEBOOK_DIR.glob("*.ipynb"),
        key=lambda path: int(path.name.partition("-")[0]),
    )
    documents = []
    for notebook_path in notebook_paths:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                documents.append((f"{notebook_path.name}, Cell {number}", cell_source(cell)))
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


def test_notebook_markdown_formatting() -> None:
    """Apply the formatting contract to every notebook Markdown cell."""
    for notebook_path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        for number, cell in enumerate(notebook["cells"], start=1):
            if cell["cell_type"] == "markdown":
                source = cell_source(cell)
                context = f"{notebook_path.name}, Cell {number}"
                assert_markdown_formatting(source, context)


def lesson_markdown_cell(notebook: dict[str, Any]) -> dict[str, Any]:
    """Require a standalone logo, lesson Markdown, and self-check code."""
    cells = notebook["cells"]
    cell_types = [cell["cell_type"] for cell in cells]
    assert cell_types == ["markdown", "markdown", "code"]
    logo_source = cell_source(cells[0])
    assert 'src="../assets/images/dtlogo.png"' in logo_source
    assert re.fullmatch(
        r"\s*<p[^>]*>\s*<a[^>]*>\s*<img[^>]*>\s*</a>\s*</p>\s*",
        logo_source,
    )
    return cells[-2]


@pytest.mark.parametrize("source_is_list", [False, True])
def test_lesson_markdown_cell_accepts_logo_layouts(
    *, source_is_list: bool,
) -> None:
    """Read the lesson with either valid logo-source representation."""
    logo_source = (
        '<p align="center">\n'
        '<a href="https://duckietown.com">'
        '<img src="../assets/images/dtlogo.png"></a>\n'
        '</p>\n'
    )
    logo: dict[str, str | list[str]] = {
        "cell_type": "markdown",
        "source": logo_source,
    }
    if source_is_list:
        logo["source"] = logo_source.splitlines(keepends=True)
    lesson = {"cell_type": "markdown", "source": "# Lesson\n"}
    code = {"cell_type": "code", "source": "self_check()\n"}
    cells = [logo, lesson, code]
    assert lesson_markdown_cell({"cells": cells}) is lesson


@pytest.mark.parametrize(
    "cell_types",
    [
        ["markdown"],
        ["markdown", "code"],
        ["code", "markdown"],
        ["markdown", "markdown", "markdown"],
        ["markdown", "markdown", "markdown", "code"],
    ],
)
def test_lesson_markdown_cell_rejects_invalid_cell_order(
    cell_types: list[str],
) -> None:
    """Do not accept missing code or extra lesson cells as a logo layout."""
    cells = [{"cell_type": cell_type} for cell_type in cell_types]
    with pytest.raises(AssertionError):
        lesson_markdown_cell({"cells": cells})


def test_lesson_markdown_cell_rejects_content_in_logo_cell() -> None:
    """Keep a separate logo cell distinct from the lesson."""
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": (
                    '<p><a href="https://duckietown.com">'
                    '<img src="../assets/images/dtlogo.png"></a></p>\n'
                    '# Hidden lesson\n'
                ),
            },
            {"cell_type": "markdown", "source": "# Lesson\n"},
            {"cell_type": "code", "source": "self_check()\n"},
        ],
    }
    with pytest.raises(AssertionError):
        lesson_markdown_cell(notebook)


def assert_markdown_ends_with_one_newline(cell: dict[str, Any]) -> None:
    """Require Markdown cell source to end without blank or space-only tails."""
    source = cell["source"]
    text = "".join(source) if isinstance(source, list) else source
    assert text.endswith("\n")
    assert not text.endswith("\n\n")
    assert not text.endswith(" \n")


def assert_try_it_sections(source: str) -> None:
    """Require each activity to stay inside a parent section with its result."""
    activity_headings = list(TRY_IT_HEADING_PATTERN.finditer(source))
    if not activity_headings:
        return

    section_headings = list(SECTION_HEADING_PATTERN.finditer(source))
    checkpoint_index = source.index("## Checkpoint")
    for index, activity_heading in enumerate(activity_headings):
        assert activity_heading.start() < checkpoint_index
        parent_headings = [
            heading
            for heading in section_headings
            if heading.start() < activity_heading.start()
            and not TRY_IT_HEADING_PATTERN.fullmatch(heading.group(0))
        ]
        assert parent_headings
        next_heading_start = next(
            (
                heading.start()
                for heading in section_headings
                if heading.start() > activity_heading.start()
            ),
            checkpoint_index,
        )
        activity_end = min(
            next_heading_start,
            (
                activity_headings[index + 1].start()
                if index + 1 < len(activity_headings)
                else checkpoint_index
            ),
        )
        activity_source = source[activity_heading.end() : activity_end]
        assert "<details>" in activity_source
        assert "</details>" in activity_source


def assert_final_checkpoint_tail(notebook: dict[str, Any]) -> None:
    """Require the standard final Further reading and checkpoint structure."""
    final_markdown = notebook["cells"][-2]
    assert final_markdown["cell_type"] == "markdown"
    source = cell_source(final_markdown)
    checkpoint_index = source.rfind("## Checkpoint\n")
    assert checkpoint_index >= 0
    assert source[checkpoint_index:] == CHECKPOINT_TAIL
    headings = re.findall(r"(?m)^## .+$", source[:checkpoint_index])
    assert headings[-1] == "## Further reading"


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
    markdown_cell = lesson_markdown_cell(notebook)
    markdown_source = cell_source(markdown_cell)
    code_source = cell_source(notebook["cells"][-1])
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
        markdown_cell = lesson_markdown_cell(notebook)

        for cell in notebook["cells"]:
            assert isinstance(cell["metadata"], dict)
            assert isinstance(cell["id"], str)
            assert cell["id"]
            assert cell["id"] == cell["metadata"]["id"]
            expected_language = (
                "markdown" if cell["cell_type"] == "markdown" else "python"
            )
            assert cell["metadata"]["language"] == expected_language
            if cell["cell_type"] == "markdown":
                assert_markdown_ends_with_one_newline(cell)

        assert markdown_cell["cell_type"] == "markdown"
        assert markdown_cell["metadata"]["language"] == "markdown"
        source = cell_source(markdown_cell)
        expected_heading = REQUIRED_NOTEBOOKS.get(notebook_path.name, "#")
        assert 'src="../assets/images/dtlogo.png"' not in source

        markdown_headings = [
            line for line in source.splitlines() if line.startswith("# ")
        ]
        assert markdown_headings[0] == expected_heading
        assert_try_it_sections(source)

        if notebook_path.name in INTERACTIVE_CHECKPOINT_NOTEBOOKS:
            code_cell = notebook["cells"][-1]
            assert code_cell["cell_type"] == "code"
            assert code_cell["metadata"]["language"] == "python"
            assert_final_checkpoint_tail(notebook)


@pytest.mark.parametrize("kind", ["figure", "table"])
@pytest.mark.parametrize("number", ["1", "23"])
@pytest.mark.parametrize("caption_label", ["{label} {number}", "<strong>{label} {number}</strong>"])
def test_media_introductions_accept_linked_sentences(
    kind: str, number: str, caption_label: str,
) -> None:
    """Accept matching numbered anchors, captions, and direct introductions."""
    label = kind.capitalize()
    caption_tag = "caption" if kind == "table" else "figcaption"
    caption_label = caption_label.format(label=label, number=number)
    source = (
        f"The comparison appears in [{label} {number}](#{kind}-{number}).\n\n"
        f'<{kind} id="{kind}-{number}">'
        f"<{caption_tag}>{caption_label}: Comparison.</{caption_tag}></{kind}>"
    )
    assert_media_introductions(source)


@pytest.mark.parametrize("kind", ["figure", "table"])
@pytest.mark.parametrize(
    ("introduction", "error"),
    [
        ("The comparison follows.", "leading sentence must link"),
        ("See [{label} 1](#{kind}-2).", "leading sentence must link"),
        ("See [{label} 1](#{kind}-1):", "sentence, not with a colon"),
    ],
)
def test_media_introductions_reject_missing_links_and_colons(
    kind: str, introduction: str, error: str,
) -> None:
    """Reject unlinked introductions, wrong targets, and colon-only lead-ins."""
    label = kind.capitalize()
    caption_tag = "caption" if kind == "table" else "figcaption"
    introduction = introduction.format(label=label, kind=kind)
    source = (
        f'{introduction}\n\n<{kind} id="{kind}-1">'
        f"<{caption_tag}>{label} 1: Comparison.</{caption_tag}></{kind}>"
    )
    with pytest.raises(AssertionError, match=error):
        assert_media_introductions(source)


@pytest.mark.parametrize("kind", ["figure", "table"])
@pytest.mark.parametrize("anchor", ["foo", "{kind}-foo", "{kind}-0", "{kind}-01", "other-1"])
def test_media_introductions_reject_invalid_numbered_anchors(kind: str, anchor: str) -> None:
    label = kind.capitalize()
    anchor = anchor.format(kind=kind)
    number = anchor.rsplit("-", 1)[-1]
    source = f'See [{label} {number}](#{anchor}).\n\n<{kind} id="{anchor}"></{kind}>'
    with pytest.raises(AssertionError, match=r"positive .* anchor"):
        assert_media_introductions(source)


@pytest.mark.parametrize("kind", ["figure", "table"])
@pytest.mark.parametrize(
    ("caption", "error"),
    [
        ("", "needs a numbered"),
        ("<wrong>Wrong caption element.</wrong>", "needs a numbered"),
        ("<{caption_tag}></{caption_tag}>", "must start with"),
        ("<{caption_tag}>A comparison.</{caption_tag}>", "must start with"),
        ("<{caption_tag}>{label} 2: Comparison.</{caption_tag}>", "must start with"),
        ("<{caption_tag}>Other 1: Comparison.</{caption_tag}>", "must start with"),
    ],
)
def test_media_introductions_reject_missing_and_mismatched_captions(
    kind: str, caption: str, error: str,
) -> None:
    label = kind.capitalize()
    caption_tag = "caption" if kind == "table" else "figcaption"
    caption = caption.format(caption_tag=caption_tag, label=label)
    source = f'See [{label} 1](#{kind}-1).\n\n<{kind} id="{kind}-1">{caption}</{kind}>'
    with pytest.raises(AssertionError, match=error):
        assert_media_introductions(source)


def test_introduction_illustrations_are_figures() -> None:
    """Present the introductory diagrams and image-reference examples as figures."""
    notebook_path = NOTEBOOK_DIR / "1-introduction-to-docker.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    source = cell_source(lesson_markdown_cell(notebook))
    figures = [figure.group(0) for figure in FIGURE_PATTERN.finditer(source)]
    for illustration in (
        "build an image",
        "[namespace/]repository[:tag]",
        "duckietown/dt-core:ente-arm64v8",
    ):
        assert any(illustration in figure for figure in figures), illustration
    assert any("Docker client" in figure and "Docker daemon" in figure for figure in figures)


@pytest.mark.parametrize(
    "illustration",
    ["packages/docker_exercises/", "127.0.0.1 : 8088 : 8080"],
)
def test_build_illustrations_are_figures(illustration: str) -> None:
    """Keep the exercise file tree and port-publishing breakdown in figures."""
    notebook_path = NOTEBOOK_DIR / "6-build-and-test-a-local-image.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    markdown_cell = lesson_markdown_cell(notebook)
    source = cell_source(markdown_cell)
    figures = [figure.group(0) for figure in FIGURE_PATTERN.finditer(source)]
    assert any(illustration in figure for figure in figures), illustration


def test_tables_and_figures_use_shared_presentation_style() -> None:
    """Keep table and figure layout on the canonical shared CSS contract."""
    styled_notebooks = 0
    table_count = 0
    figure_count = 0

    for notebook_path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        markdown_cell = lesson_markdown_cell(notebook)
        source = cell_source(markdown_cell)
        tables = TABLE_PATTERN.findall(source)
        figures = FIGURE_PATTERN.findall(source)

        if tables or figures:
            styled_notebooks += 1
            assert PRESENTATION_STYLE.search(source)
        else:
            assert "<style>" not in source

        assert_media_introductions(source, str(notebook_path))
        for attributes in tables:
            assert 'class="lx-table"' in attributes
        for attributes in figures:
            assert 'class="lx-figure"' in attributes
        for attributes in CAPTION_PATTERN.findall(source):
            assert "style=" not in attributes

        table_count += len(tables)
        figure_count += len(figures)

    assert styled_notebooks == 11
    assert table_count == 14
    assert figure_count == 16


def test_numbered_notebook_references_are_individually_linked() -> None:
    """Keep numbered course references direct and individually actionable."""
    readme_source = README_PATH.read_text(encoding="utf-8")
    learner_sources = {README_PATH: readme_source}

    for notebook_name in REQUIRED_NOTEBOOKS:
        notebook_path = NOTEBOOK_DIR / notebook_name
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        markdown_cell = lesson_markdown_cell(notebook)
        markdown_source = cell_source(markdown_cell)
        learner_sources[notebook_path] = markdown_source

        notebook_number = notebook_name.partition("-")[0]
        expected_link = f"[Notebook {notebook_number}](./notebooks/{notebook_name})"
        assert expected_link in readme_source

    for learner_path, learner_source in learner_sources.items():
        assert (
            UNLINKED_NOTEBOOK_REFERENCE_PATTERN.search(learner_source) is None
        ), learner_path


def test_cross_lx_references_use_clear_linked_titles() -> None:
    """Keep external LX links clear and introductions concise."""
    notebook_path = NOTEBOOK_DIR / "4-docker-security-and-duckiedrone-boundaries.ipynb"
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    markdown_cell = lesson_markdown_cell(notebook)
    markdown_source = cell_source(markdown_cell)
    expected_link = (
        f"[{LINUX_NETWORKING_NOTEBOOK_TITLE}]"
        f"({LINUX_NETWORKING_LX_URL})"
    )

    assert expected_link in markdown_source
    assert UNLINKED_CROSS_LX_REFERENCE_PATTERN.search(markdown_source) is None


def test_checkpoint_data_matches_interactive_notebooks() -> None:
    """Keep every interactive Docker notebook paired with one sidecar."""
    expected_paths = {
        checkpoint_data_path(notebook_name)
        for notebook_name in INTERACTIVE_CHECKPOINT_NOTEBOOKS
    }
    assert set(CHECKPOINT_DATA_DIR.glob("*.json")) == expected_paths

    for notebook_name in INTERACTIVE_CHECKPOINT_NOTEBOOKS:
        assert_reveal_self_check(notebook_name)


def test_remote_context_cleanup_follows_all_queries() -> None:
    """Keep the remote context available until its last inspection command."""
    notebook_path = NOTEBOOK_DIR / "12-remote-duckiedrone-docker-contexts.ipynb"
    notebook_source = notebook_path.read_text(encoding="utf-8")
    notebook = json.loads(notebook_source)
    markdown_cell = lesson_markdown_cell(notebook)
    source = cell_source(markdown_cell)
    context_name = "duckiedrone-DUCKIEDRONE_NAME"

    creation_index = source.index(f"docker context create {context_name}")
    first_query_index = source.index(f"docker --context {context_name}")
    last_query_index = source.rindex(f"docker --context {context_name}")
    cleanup_index = source.index(f"docker context rm {context_name}")

    assert creation_index < first_query_index
    assert last_query_index < cleanup_index


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
    assert "<a href='#source'>Source</a>" in self_check.model_answer.value


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
    assert re.search(
        r"^# Learning Experience \(LX\): .+ on the Duckiedrone$",
        readme,
        re.MULTILINE,
    )
    assert "`Software: ente`; `Hardware: DD24-B`" in readme
    assert re.findall(r"^## .+$", readme, re.MULTILINE) == [
        "## Intended learning outcomes",
        "## Run this LX",
        "## Notebooks",
        "## Prerequisites",
        f"## Complete the {README_EXERCISE_TOPIC} exercise",
        "## Further reading",
        "## For LX authors",
    ]

    notebook_section = readme.split("## Notebooks\n", 1)[1].split("\n## ", 1)[0]
    assert "| # | Notebook | Description |\n| --- | --- | --- |" in notebook_section
    notebook_rows = re.findall(r"^\| \d+ \|.*\|$", notebook_section, re.MULTILINE)
    assert len(notebook_rows) == len(REQUIRED_NOTEBOOKS)
    for number, (notebook_name, row) in enumerate(
        zip(REQUIRED_NOTEBOOKS, notebook_rows, strict=True), start=1
    ):
        expected_prefix = (
            f"| {number} | [Notebook {number}](./notebooks/{notebook_name}) | "
        )
        assert row.startswith(expected_prefix)
        assert len(row.split("|")) == 5
        assert row.removeprefix(expected_prefix).strip(" |")

    prerequisite_section = readme.split("## Prerequisites\n", 1)[1].split(
        "\n## ", 1
    )[0]
    prerequisite_headings = re.findall(
        r"^### .+$", prerequisite_section, re.MULTILINE
    )
    assert len(prerequisite_headings) == 4
    assert prerequisite_headings[0] == "### Choose the terminal"
    assert prerequisite_headings[1] == (
        f"### {README_EXERCISE_TOPIC} foundations and local practice"
    )
    assert prerequisite_headings[-1] == "### Duckiedrone access"
    assert "python3 -m pytest tests/" in readme
    assert (
        "Interactive checkpoints require the notebook metadata supplied by "
        "`dts code editor` and a compatible Jupyter/IPython kernel with "
        "`ipywidgets` available"
        in readme
    )
