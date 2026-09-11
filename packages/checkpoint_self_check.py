"""Shared interactive checkpoint support for learning notebooks."""

import json
import os
import re
from html import escape
from pathlib import Path
from urllib.parse import unquote, urlsplit

import ipywidgets as widgets  # pyright: ignore[reportMissingTypeStubs]
from IPython import get_ipython
from IPython.display import display

RESPONSE_LAYOUT = widgets.Layout(
    width="fit-content",
    max_width="100%",
    margin="0 0 12px 0",
    flex="0 0 auto",
)
CHOICE_RESPONSE_LAYOUT = widgets.Layout(
    width="100%",
    max_width="100%",
    margin="0 0 12px 0",
    flex="0 0 auto",
)
CONTROL_LAYOUT = widgets.Layout(
    display="flex",
    flex_flow="row wrap",
    align_items="center",
    width="100%",
    margin="12px 0 0 0",
)
INLINE_CODE_PATTERN = re.compile(r"`([^`]*)`")
CHECKPOINT_WIDGET_STYLE = (
    "<style>"
    ".checkpoint-self-checks {"
    "background-color: var(--vscode-editor-background, var(--jp-layout-color0));"
    "box-shadow: 0 0 0 8px var(--vscode-editor-background, var(--jp-layout-color0));"
    "color: var(--vscode-editor-foreground, var(--vscode-foreground, var(--jp-ui-font-color0)));"
    "}"
    ".checkpoint-self-check .jupyter-widgets.widget-html,"
    ".checkpoint-self-check .jupyter-widgets.widget-html .widget-html-content {"
    "color: var(--vscode-editor-foreground, var(--vscode-foreground, var(--jp-ui-font-color0))) !important;"
    "}"
    ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p {"
    "line-height: 1.5;"
    "margin: 0 0 8px;"
    "}"
    ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p:last-child {"
    "margin-bottom: 0;"
    "}"
    ".checkpoint-self-check .jupyter-widgets.widget-textarea .widget-label,"
    ".checkpoint-self-check .checkpoint-choice-answer,"
    ".checkpoint-self-check .checkpoint-choice-answer label {"
    "color: var(--vscode-editor-foreground, var(--vscode-foreground, var(--jp-ui-font-color0))) !important;"
    "}"
    ".checkpoint-self-check .checkpoint-response .widget-label {"
    "font-weight: 700;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer .widget-label-basic {"
    "display: flex;"
    "align-items: flex-start;"
    "width: 100%;"
    "min-width: 0;"
    "min-height: 20px;"
    "overflow: visible;"
    "text-overflow: clip;"
    "white-space: normal;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer .widget-checkbox .widget-label {"
    "min-width: 0;"
    "overflow: visible;"
    "text-overflow: clip;"
    "white-space: normal;"
    "overflow-wrap: anywhere;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer input[type='checkbox'] {"
    "-webkit-appearance: none;"
    "appearance: none;"
    "box-sizing: border-box;"
    "width: 16px;"
    "height: 16px;"
    "margin: 0 8px 0 1px;"
    "flex: 0 0 16px;"
    "border: 2px solid var(--vscode-input-border, var(--jp-border-color1));"
    "border-radius: 50%;"
    "background-color: var(--vscode-input-background, var(--jp-input-background));"
    "cursor: pointer;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer input[type='checkbox']:checked {"
    "border-color: var(--vscode-button-background, var(--jp-brand-color1));"
    "background-color: var(--vscode-button-background, var(--jp-brand-color1));"
    "box-shadow: inset 0 0 0 4px var(--vscode-button-foreground, var(--jp-ui-inverse-font-color1));"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer input[type='checkbox']:focus-visible {"
    "outline: 2px solid var(--vscode-focusBorder, var(--jp-widgets-input-focus-border-color));"
    "outline-offset: 2px;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer input[type='checkbox']:disabled {"
    "border-color: var(--vscode-disabledForeground, var(--jp-ui-font-color2));"
    "background-color: var(--vscode-input-background, var(--jp-input-background));"
    "opacity: 1;"
    "cursor: default;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-answer input[type='checkbox']:disabled:checked {"
    "border-color: var(--vscode-disabledForeground, var(--jp-ui-font-color2));"
    "background-color: var(--vscode-disabledForeground, var(--jp-ui-font-color2));"
    "box-shadow: inset 0 0 0 4px var(--vscode-input-background, var(--jp-input-background));"
    "}"
    ".checkpoint-self-check .checkpoint-choice-result {"
    "display: inline-flex;"
    "align-items: center;"
    "justify-content: center;"
    "min-height: 20px;"
    "font-size: 20px;"
    "font-weight: 700;"
    "line-height: 1;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-result-correct {"
    "color: var(--vscode-testing-iconPassed, var(--vscode-terminal-ansiGreen, #73c991)) !important;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-result-incorrect {"
    "color: var(--vscode-testing-iconFailed, var(--vscode-terminal-ansiRed, #f14c4c)) !important;"
    "}"
    ".checkpoint-self-check .checkpoint-choice-feedback {"
    "display: flex;"
    "align-items: center;"
    "gap: 8px;"
    "}"
    ".checkpoint-self-check .checkpoint-answer.widget-textarea textarea {"
    "field-sizing: content;"
    "width: auto;"
    "max-width: 100%;"
    "height: auto;"
    "overflow-y: hidden;"
    "resize: none;"
    "border-radius: 4px;"
    "background-color: var(--vscode-input-background, var(--jp-input-background));"
    "color: var(--vscode-input-foreground, var(--jp-ui-font-color0));"
    "border-color: var(--vscode-input-border, var(--jp-border-color1));"
    "caret-color: var(--vscode-editorCursor-foreground, currentColor);"
    "}"
    ".checkpoint-self-check .checkpoint-answer.widget-textarea textarea::placeholder {"
    "color: var(--vscode-input-placeholderForeground, var(--jp-ui-font-color2));"
    "opacity: 1;"
    "}"
    ".checkpoint-self-check .checkpoint-answer.widget-textarea textarea:focus {"
    "border-color: var(--vscode-focusBorder, var(--jp-widgets-input-focus-border-color));"
    "outline-color: var(--vscode-focusBorder, var(--jp-widgets-input-focus-border-color));"
    "}"
    ".checkpoint-self-check button.checkpoint-control,"
    ".checkpoint-self-check .checkpoint-control button {"
    "border: 1px solid var(--vscode-button-border, transparent);"
    "border-radius: 4px;"
    "box-shadow: none;"
    "}"
    ".checkpoint-self-check button.checkpoint-primary-control,"
    ".checkpoint-self-check .checkpoint-primary-control button {"
    "background-color: var(--vscode-button-background, var(--jp-brand-color1)) !important;"
    "color: var(--vscode-button-foreground, var(--jp-ui-inverse-font-color1)) !important;"
    "}"
    ".checkpoint-self-check button.checkpoint-primary-control:not(:disabled):hover,"
    ".checkpoint-self-check .checkpoint-primary-control button:not(:disabled):hover {"
    "background-color: var(--vscode-button-hoverBackground, var(--jp-brand-color0)) !important;"
    "}"
    ".checkpoint-self-check button.checkpoint-secondary-control,"
    ".checkpoint-self-check .checkpoint-secondary-control button {"
    "background-color: var(--vscode-button-secondaryBackground, var(--jp-layout-color2)) !important;"
    "color: var(--vscode-button-secondaryForeground, var(--jp-ui-font-color1)) !important;"
    "}"
    ".checkpoint-self-check button.checkpoint-secondary-control:not(:disabled):hover,"
    ".checkpoint-self-check .checkpoint-secondary-control button:not(:disabled):hover {"
    "background-color: var(--vscode-button-secondaryHoverBackground, var(--jp-layout-color3)) !important;"
    "}"
    ".checkpoint-self-check button.checkpoint-control:disabled,"
    ".checkpoint-self-check .checkpoint-control button:disabled {"
    "background-color: var(--vscode-button-secondaryBackground, var(--jp-layout-color2)) !important;"
    "color: var(--vscode-disabledForeground, var(--jp-ui-font-color2)) !important;"
    "cursor: default;"
    "opacity: 1;"
    "pointer-events: none;"
    "}"
    ".checkpoint-self-check a {"
    "color: var(--vscode-textLink-foreground, var(--jp-brand-color1));"
    "}"
    ".checkpoint-self-check a:hover {"
    "color: var(--vscode-textLink-activeForeground, var(--jp-brand-color0));"
    "}"
    "</style>"
)


class CheckpointDataError(Exception):
    pass


def find_checkpoint_data_path(checkpoint_data_relative_path: Path) -> Path:
    search_roots = []
    repository_path = os.environ.get("DT_REPO_PATH")
    if repository_path:
        search_roots.append(Path(repository_path))

    working_directory = Path.cwd().resolve()
    search_roots.append(working_directory)
    search_roots.extend(working_directory.parents)

    for search_root in search_roots:
        checkpoint_data_path = search_root / checkpoint_data_relative_path
        if checkpoint_data_path.is_file():
            return checkpoint_data_path

    raise CheckpointDataError("The checkpoint data is unavailable.")


def load_checkpoint_data(
    checkpoint_data_relative_path: Path,
) -> dict[str, object]:
    checkpoint_data_path = find_checkpoint_data_path(
        checkpoint_data_relative_path
    )
    try:
        with checkpoint_data_path.open(
            encoding="utf-8"
        ) as checkpoint_data_file:
            checkpoint_data = json.load(checkpoint_data_file)
    except (OSError, json.JSONDecodeError) as error:
        raise CheckpointDataError(
            "The checkpoint data could not be read."
        ) from error

    if not isinstance(checkpoint_data, dict):
        raise CheckpointDataError("The checkpoint data is invalid.")

    return checkpoint_data


def parse_checkpoint_choices(
    checkpoint: dict[str, object],
) -> tuple[tuple[str, ...], str] | None:
    choices = checkpoint.get("choices")
    if choices is None:
        if "correct_choice" in checkpoint:
            raise CheckpointDataError(
                "The checkpoint correct choice is invalid."
            )
        return None
    if not isinstance(choices, list) or len(choices) < 2:
        raise CheckpointDataError("The checkpoint choices are invalid.")

    choice_labels = []
    for choice in choices:
        if not isinstance(choice, str) or not choice.strip():
            raise CheckpointDataError("The checkpoint choices are invalid.")
        choice_labels.append(choice)
    if len(set(choice_labels)) != len(choice_labels):
        raise CheckpointDataError("The checkpoint choices are invalid.")

    correct_choice = checkpoint.get("correct_choice")
    if (
        not isinstance(correct_choice, str)
        or correct_choice not in choice_labels
    ):
        raise CheckpointDataError("The checkpoint correct choice is invalid.")

    return tuple(choice_labels), correct_choice


def load_checkpoint_definitions(
    checkpoint_data_relative_path: Path,
) -> list[tuple[str, str, tuple[str, ...] | None]]:
    checkpoint_data = load_checkpoint_data(checkpoint_data_relative_path)
    checkpoints = checkpoint_data.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        raise CheckpointDataError("The checkpoint data is incomplete.")

    definitions = []
    checkpoint_ids = set()
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            raise CheckpointDataError("The checkpoint definition is invalid.")

        checkpoint_id = checkpoint.get("id")
        question = checkpoint.get("question")
        if (
            not isinstance(checkpoint_id, str)
            or not checkpoint_id
            or not isinstance(question, str)
            or not question
        ):
            raise CheckpointDataError(
                "The checkpoint definition is incomplete."
            )
        if checkpoint_id in checkpoint_ids:
            raise CheckpointDataError(
                "The checkpoint data has duplicate identifiers."
            )

        parsed_choices = parse_checkpoint_choices(checkpoint)
        checkpoint_choices = (
            None if parsed_choices is None else parsed_choices[0]
        )

        checkpoint_ids.add(checkpoint_id)
        definitions.append((question, checkpoint_id, checkpoint_choices))

    return definitions


def load_checkpoint_record(
    checkpoint_data_relative_path: Path,
    checkpoint_id: str,
) -> dict[str, object]:
    checkpoint_data = load_checkpoint_data(checkpoint_data_relative_path)
    checkpoints = checkpoint_data.get("checkpoints")
    if not isinstance(checkpoints, list):
        raise CheckpointDataError("The requested model answer is unavailable.")

    matching_checkpoint = None
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, dict):
            raise CheckpointDataError("The checkpoint definition is invalid.")
        if checkpoint.get("id") == checkpoint_id:
            if matching_checkpoint is not None:
                raise CheckpointDataError(
                    "The checkpoint data has duplicate identifiers."
                )
            matching_checkpoint = checkpoint

    if matching_checkpoint is None:
        raise CheckpointDataError("The requested model answer is unavailable.")

    return matching_checkpoint


def load_model_answer(
    checkpoint_data_relative_path: Path,
    checkpoint_id: str,
) -> tuple[str, list[dict[str, str]]]:
    matching_checkpoint = load_checkpoint_record(
        checkpoint_data_relative_path,
        checkpoint_id,
    )
    model_answer = matching_checkpoint.get("model_answer")
    evidence = matching_checkpoint.get("evidence")
    if (
        not isinstance(model_answer, str)
        or not model_answer
        or not isinstance(evidence, list)
    ):
        raise CheckpointDataError("The requested model answer is incomplete.")

    return model_answer, evidence


def load_correct_choice(
    checkpoint_data_relative_path: Path,
    checkpoint_id: str,
) -> str:
    matching_checkpoint = load_checkpoint_record(
        checkpoint_data_relative_path,
        checkpoint_id,
    )
    parsed_choices = parse_checkpoint_choices(matching_checkpoint)
    if parsed_choices is None:
        raise CheckpointDataError(
            "The requested correct choice is unavailable."
        )

    return parsed_choices[1]


def render_inline_code(text: str) -> str:
    rendered_parts = []
    text_position = 0
    for inline_code_match in INLINE_CODE_PATTERN.finditer(text):
        rendered_parts.append(
            escape(text[text_position:inline_code_match.start()])
        )
        rendered_parts.append(
            f"<code>{escape(inline_code_match.group(1))}</code>"
        )
        text_position = inline_code_match.end()
    rendered_parts.append(escape(text[text_position:]))
    return "".join(rendered_parts)


def render_model_answer(
    model_answer: str,
    evidence: list[dict[str, str]],
    heading: str = "Model answer",
) -> str:
    evidence_links = []
    for evidence_item in evidence:
        label = evidence_item.get("label")
        anchor = evidence_item.get("anchor")
        if (
            not isinstance(label, str)
            or not label
            or not isinstance(anchor, str)
            or not anchor.startswith("#")
        ):
            raise CheckpointDataError(
                "The model-answer evidence link is invalid."
            )
        evidence_links.append(
            f"<a href='{escape(anchor, quote=True)}'>{escape(label)}</a>",
        )

    if not evidence_links:
        raise CheckpointDataError("The model answer has no evidence links.")

    return (
        f"<p><strong>{escape(heading)}:</strong> {render_inline_code(model_answer)}</p>"
        f"<p><strong>Source sections above:</strong> {' and '.join(evidence_links)}.</p>"
    )


def render_choice_result(is_correct: bool, correct_choice: str) -> str:
    if is_correct:
        result_class = "checkpoint-choice-result-correct"
        outcome = "Correct"
        symbol = "&#10003;"
    else:
        result_class = "checkpoint-choice-result-incorrect"
        outcome = "Incorrect"
        symbol = "&#10007;"

    return (
        "<div class='checkpoint-choice-feedback' "
        "role='status' aria-live='polite' aria-atomic='true'>"
        f"<span class='checkpoint-choice-result {result_class}'>"
        f"<span role='img' aria-label='{outcome}' title='{outcome}'>{symbol}</span>"
        "</span>"
        "<span class='checkpoint-correct-choice'>"
        f"<strong>Correct answer:</strong> {render_inline_code(correct_choice)}"
        "</span>"
        "</div>"
    )


def render_status(message: str, *, emphasized: bool = False) -> str:
    escaped_message = escape(message)
    content = f"<em>{escaped_message}</em>" if emphasized else escaped_message
    return (
        "<div role='status' aria-live='polite' aria-atomic='true'>"
        f"<p>{content}</p>"
        "</div>"
    )


def get_checkpoint_name_from_notebook_context() -> str:
    shell = get_ipython()
    kernel = getattr(shell, "kernel", None)
    get_parent = getattr(kernel, "get_parent", None)
    if not callable(get_parent):
        raise CheckpointDataError("The calling notebook is unavailable.")

    parent_message = get_parent()
    metadata = parent_message.get("metadata")
    if not isinstance(metadata, dict):
        raise CheckpointDataError("The calling notebook is unavailable.")

    cell_id = metadata.get("cellId")
    if not isinstance(cell_id, str):
        raise CheckpointDataError("The calling notebook is unavailable.")

    notebook_path = Path(unquote(urlsplit(cell_id).path))
    notebook_number, separator, checkpoint_name = notebook_path.stem.partition(
        "-"
    )
    if (
        notebook_path.suffix != ".ipynb"
        or not notebook_number.isdigit()
        or not separator
        or not checkpoint_name
    ):
        raise CheckpointDataError("The calling notebook is unavailable.")

    return checkpoint_name


class CheckpointSelfCheck:
    def __init__(
        self,
        question_number: int,
        question: str,
        checkpoint_id: str,
        checkpoint_data_relative_path: Path,
        question_count: int | None = None,
        choices: tuple[str, ...] | None = None,
    ) -> None:
        self.checkpoint_id = checkpoint_id
        self.checkpoint_data_relative_path = checkpoint_data_relative_path
        self.is_multiple_choice = choices is not None
        self.text_answer: widgets.Textarea | None = None
        self.choice_options: tuple[widgets.Checkbox, ...] = ()
        self.choice_values: tuple[str, ...] = ()
        self._syncing_choice_selection = False
        question_heading = f"Question {question_number}"
        if question_count is not None:
            question_heading += f" of {question_count}"
        self.question = widgets.HTML(
            value=(
                f"<h3>{question_heading}</h3>"
                f"<p>{render_inline_code(question)}</p>"
            ),
        )
        if choices is None:
            self.answer = widgets.Textarea(
                placeholder="Write your answer here.",
                description="Your answer:",
                rows=1,
                layout=RESPONSE_LAYOUT,
                style={"description_width": "initial"},
            )
            self.answer.add_class("checkpoint-answer")
            self.text_answer = self.answer
        else:
            self.choice_values = choices
            choice_options = []
            for choice in choices:
                choice_option = widgets.Checkbox(
                    value=False,
                    description=choice.replace("`", ""),
                    indent=False,
                    layout=widgets.Layout(width="100%", margin="0"),
                    style={"description_width": "initial"},
                )
                if "description_allow_html" in choice_option.traits():
                    choice_option.description = render_inline_code(choice)
                    choice_option.set_trait(
                        name="description_allow_html",
                        value=True,
                    )
                choice_options.append(choice_option)
            self.choice_options = tuple(choice_options)
            choice_label = widgets.HTML(
                value="<strong>Your answer:</strong>",
                layout=widgets.Layout(margin="0"),
            )
            choice_label.add_class("checkpoint-choice-label")
            self.answer = widgets.VBox(
                [choice_label, *self.choice_options],
                layout=CHOICE_RESPONSE_LAYOUT,
            )
            self.answer.add_class("checkpoint-choice-answer")
        self.answer.add_class("checkpoint-response")
        self.reveal_button = widgets.Button(
            description="Reveal answer",
            icon="eye",
            disabled=True,
            tooltip="Reveal the answer after writing or selecting a response.",
            layout=widgets.Layout(
                width="140px",
                min_width="140px",
                margin="0 8px 8px 0",
            ),
        )
        self.retry_button = widgets.Button(
            description="Try again",
            icon="refresh",
            disabled=True,
            tooltip="Clear this response and try this question again.",
            layout=widgets.Layout(display="none", margin="0 8px 8px 0"),
        )
        for control_button in (self.reveal_button, self.retry_button):
            control_button.add_class("checkpoint-control")
        self.reveal_button.add_class("checkpoint-primary-control")
        self.retry_button.add_class("checkpoint-secondary-control")
        self.status = widgets.HTML(
            value="",
            layout=widgets.Layout(display="none"),
        )
        self.choice_result = widgets.HTML(
            value="",
            layout=widgets.Layout(display="none", margin="0 0 12px 0"),
        )
        self.model_answer = widgets.HTML(
            value="",
            layout=widgets.Layout(display="none", width="100%"),
        )
        self.model_answer.add_class("checkpoint-model-answer")
        self.controls = widgets.HBox(
            [
                self.reveal_button,
                self.retry_button,
            ],
            layout=CONTROL_LAYOUT,
        )
        self.widget = widgets.VBox(
            [
                self.question,
                self.answer,
                self.choice_result,
                self.controls,
                self.status,
                self.model_answer,
            ],
            layout=widgets.Layout(
                width="calc(100% - 24px)",
                margin="0 12px 24px",
            ),
        )
        self.widget.add_class("checkpoint-self-check")
        if self.is_multiple_choice:
            for choice_option in self.choice_options:
                choice_option.observe(
                    self.update_choice_selection, names="value"
                )
        else:
            assert self.text_answer is not None
            self.text_answer.observe(
                self.update_reveal_availability, names="value"
            )
        self.reveal_button.on_click(self.reveal_answer)
        self.retry_button.on_click(self.retry_answer)

    def get_response_value(self) -> str:
        if self.is_multiple_choice:
            for choice_value, choice_option in zip(
                self.choice_values,
                self.choice_options,
                strict=True,
            ):
                if choice_option.value:
                    return choice_value
            return ""

        assert self.text_answer is not None
        return self.text_answer.value

    def get_answer_heading(self) -> str:
        return "Explanation" if self.is_multiple_choice else "Model answer"

    def response_is_disabled(self) -> bool:
        if self.is_multiple_choice:
            return all(
                choice_option.disabled for choice_option in self.choice_options
            )

        assert self.text_answer is not None
        return self.text_answer.disabled

    def set_response_disabled(self, disabled: bool) -> None:
        if self.is_multiple_choice:
            for choice_option in self.choice_options:
                choice_option.disabled = disabled
            return

        assert self.text_answer is not None
        self.text_answer.disabled = disabled

    def update_choice_selection(self, change: dict[str, object]) -> None:
        if self._syncing_choice_selection:
            return

        selected_choice = change.get("owner")
        if change.get("new") is True and isinstance(
            selected_choice, widgets.Checkbox
        ):
            self._syncing_choice_selection = True
            try:
                for choice_option in self.choice_options:
                    if choice_option is not selected_choice:
                        choice_option.value = False
            finally:
                self._syncing_choice_selection = False
        self.update_reveal_availability(None)

    def update_reveal_availability(
        self,
        change: dict[str, object] | None,
    ) -> None:
        del change
        has_response = bool(self.get_response_value().strip())
        self.reveal_button.disabled = (
            self.response_is_disabled() or not has_response
        )

    def retry_answer(self, button: widgets.Button) -> None:
        if button.disabled:
            return
        self.set_response_disabled(False)
        if self.is_multiple_choice:
            self._syncing_choice_selection = True
            try:
                for choice_option in self.choice_options:
                    choice_option.value = False
            finally:
                self._syncing_choice_selection = False
        else:
            assert self.text_answer is not None
            self.text_answer.value = ""
        self.reveal_button.disabled = True
        self.reveal_button.layout.display = ""
        button.disabled = True
        button.layout.display = "none"
        self.model_answer.value = ""
        self.model_answer.layout.display = "none"
        self.choice_result.value = ""
        self.choice_result.layout.display = "none"
        self.status.value = ""
        self.status.layout.display = "none"
        self.update_reveal_availability(None)

    def reveal_answer(self, button: widgets.Button) -> None:
        if button.disabled:
            return
        answer_heading = self.get_answer_heading()
        try:
            model_answer, evidence = load_model_answer(
                self.checkpoint_data_relative_path,
                self.checkpoint_id,
            )
            self.model_answer.value = render_model_answer(
                model_answer,
                evidence,
                answer_heading,
            )
            if self.is_multiple_choice:
                correct_choice = load_correct_choice(
                    self.checkpoint_data_relative_path,
                    self.checkpoint_id,
                )
                self.choice_result.value = render_choice_result(
                    self.get_response_value() == correct_choice,
                    correct_choice,
                )
        except CheckpointDataError:
            self.model_answer.value = ""
            self.model_answer.layout.display = "none"
            self.choice_result.value = ""
            self.choice_result.layout.display = "none"
            self.status.layout.display = ""
            self.status.value = render_status(
                f"{answer_heading} unavailable. Check the checkpoint data and try again.",
            )
            return
        self.set_response_disabled(True)
        self.reveal_button.disabled = True
        self.reveal_button.layout.display = "none"
        self.retry_button.disabled = False
        self.retry_button.layout.display = ""
        self.status.value = ""
        self.status.layout.display = "none"
        if self.is_multiple_choice:
            self.choice_result.layout.display = ""
        self.model_answer.layout.display = ""


def display_checkpoint_self_checks(
    checkpoint_name: str | None = None,
) -> None:
    try:
        if checkpoint_name is None:
            checkpoint_name = get_checkpoint_name_from_notebook_context()
        checkpoint_data_relative_path = (
            Path("checkpoint_data") / f"{checkpoint_name}.json"
        )
        checkpoints = load_checkpoint_definitions(
            checkpoint_data_relative_path
        )
    except CheckpointDataError:
        display(
            widgets.HTML(
                render_status(
                    "Checkpoint unavailable. The checkpoint data is not available in this LX checkout.",
                ),
            ),
        )
        return

    self_checks = []
    question_count = len(checkpoints)
    for question_number, (question, checkpoint_id, choices) in enumerate(
        checkpoints,
        start=1,
    ):
        self_check = CheckpointSelfCheck(
            question_number,
            question,
            checkpoint_id,
            checkpoint_data_relative_path,
            question_count=question_count,
            choices=choices,
        )
        self_checks.append(self_check)

    control_style = widgets.HTML(
        value=CHECKPOINT_WIDGET_STYLE,
        layout=widgets.Layout(display="none"),
    )
    check_widgets = [control_style]
    check_widgets.extend(self_check.widget for self_check in self_checks)
    checkpoint_widgets = widgets.VBox(
        check_widgets, layout=widgets.Layout(width="100%")
    )
    checkpoint_widgets.add_class("checkpoint-self-checks")
    display(checkpoint_widgets)
