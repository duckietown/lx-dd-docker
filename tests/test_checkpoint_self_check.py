"""Shared behavior tests for interactive notebook checkpoints."""

from importlib import import_module
from pathlib import Path
from unittest.mock import patch

import pytest

checkpoint_self_check = import_module("packages.checkpoint_self_check")
CHECKPOINT_DATA_PATH = Path("checkpoint_data/checkpoint.json")
CHECKPOINT_EVIDENCE = [{"label": "Source", "anchor": "#source"}]
CHECKPOINT_CHOICES = ("First option", "Second option")


def create_checkpoint_self_check(
    *,
    choices: tuple[str, ...] | None = None,
    question_count: int | None = None,
    question: str = "Question",
) -> checkpoint_self_check.CheckpointSelfCheck:
    """Create a checkpoint with fixture-independent values."""
    return checkpoint_self_check.CheckpointSelfCheck(
        question_number=1,
        question=question,
        checkpoint_id="checkpoint",
        checkpoint_data_relative_path=CHECKPOINT_DATA_PATH,
        question_count=question_count,
        choices=choices,
    )


def test_checkpoint_name_is_derived_from_notebook_context() -> None:
    """Keep the no-argument notebook call free of an embedded checkpoint name."""

    class Kernel:
        def get_parent(self) -> dict[str, object]:
            return {
                "metadata": {
                    "cellId": (
                        "vscode-notebook-cell://dev-container/workspace/notebooks/"
                        "2-checkpoint-topic.ipynb#checkpoint"
                    ),
                },
            }

    class Shell:
        kernel = Kernel()

    with patch.object(
        checkpoint_self_check,
        "get_ipython",
        return_value=Shell(),
    ):
        checkpoint_name = (
            checkpoint_self_check.get_checkpoint_name_from_notebook_context()
        )

    assert checkpoint_name == "checkpoint-topic"


def test_checkpoint_display_contains_only_explicit_output() -> None:
    """Keep notebook output limited to the explicitly displayed widgets."""
    checkpoint_definitions = [
        ("First question", "first", None),
        ("Second question", "second", CHECKPOINT_CHOICES),
    ]
    with (
        patch.object(
            checkpoint_self_check,
            "load_checkpoint_definitions",
            return_value=checkpoint_definitions,
        ),
        patch.object(checkpoint_self_check, "display") as display,
    ):
        result = checkpoint_self_check.display_checkpoint_self_checks(
            "checkpoint-topic",
        )

    assert result is None
    display.assert_called_once()
    displayed_widget = display.call_args.args[0]
    displayed_state = displayed_widget.get_state()
    assert "checkpoint-self-checks" in displayed_state["_dom_classes"]
    control_style = displayed_widget.children[0]
    assert control_style.value == checkpoint_self_check.CHECKPOINT_WIDGET_STYLE
    assert control_style.layout.display == "none"
    first_checkpoint = displayed_widget.children[1]
    first_question = first_checkpoint.children[0]
    assert "Question 1 of 2" in first_question.value
    choice_checkpoint = displayed_widget.children[2]
    choice_response = choice_checkpoint.children[1]
    assert isinstance(choice_response, checkpoint_self_check.widgets.VBox)


def test_checkpoint_initialization_error_is_announced() -> None:
    """Keep unavailable checkpoint data visible to assistive technology."""
    with (
        patch.object(
            checkpoint_self_check,
            "load_checkpoint_definitions",
            side_effect=checkpoint_self_check.CheckpointDataError(
                "The checkpoint data could not be read.",
            ),
        ),
        patch.object(checkpoint_self_check, "display") as display,
    ):
        result = checkpoint_self_check.display_checkpoint_self_checks(
            "checkpoint-topic",
        )

    assert result is None
    display.assert_called_once()
    error_message = display.call_args.args[0]
    assert "Checkpoint unavailable." in error_message.value
    assert "role='status'" in error_message.value
    assert "aria-live='polite'" in error_message.value


def test_checkpoint_definitions_reject_invalid_multiple_choice_options() -> None:
    """Reject incomplete, blank, or duplicate multiple-choice options."""
    invalid_choice_sets: tuple[list[str], ...] = (
        [],
        ["First option"],
        ["", "Second option"],
        ["First option", "First option"],
    )
    for invalid_choices in invalid_choice_sets:
        checkpoint_data = {
            "checkpoints": [
                {
                    "id": "checkpoint",
                    "question": "Question",
                    "choices": invalid_choices,
                },
            ],
        }
        with patch.object(
            checkpoint_self_check,
            "load_checkpoint_data",
            return_value=checkpoint_data,
        ), pytest.raises(
            checkpoint_self_check.CheckpointDataError,
        ) as error:
            checkpoint_self_check.load_checkpoint_definitions(
                CHECKPOINT_DATA_PATH,
            )

        assert str(error.value) == "The checkpoint choices are invalid."


def test_checkpoint_definitions_reject_invalid_correct_choices() -> None:
    """Require each multiple-choice checkpoint to name one listed answer."""
    invalid_checkpoints: tuple[dict[str, object], ...] = (
        {
            "id": "checkpoint",
            "question": "Question",
            "choices": list(CHECKPOINT_CHOICES),
        },
        {
            "id": "checkpoint",
            "question": "Question",
            "choices": list(CHECKPOINT_CHOICES),
            "correct_choice": "",
        },
        {
            "id": "checkpoint",
            "question": "Question",
            "choices": list(CHECKPOINT_CHOICES),
            "correct_choice": "Other option",
        },
    )
    for invalid_checkpoint in invalid_checkpoints:
        checkpoint_data: dict[str, object] = {
            "checkpoints": [invalid_checkpoint],
        }
        with patch.object(
            checkpoint_self_check,
            "load_checkpoint_data",
            return_value=checkpoint_data,
        ), pytest.raises(
            checkpoint_self_check.CheckpointDataError,
        ) as error:
            checkpoint_self_check.load_checkpoint_definitions(
                CHECKPOINT_DATA_PATH,
            )

        assert str(error.value) == "The checkpoint correct choice is invalid."


def test_text_checkpoint_initial_state_is_accessible_and_compact() -> None:
    """Keep the initial response and control layout stable and accessible."""
    self_check = create_checkpoint_self_check(question_count=4)

    assert "Question 1 of 4" in self_check.question.value
    assert self_check.reveal_button.description == "Reveal answer"
    assert self_check.reveal_button.layout.width == "140px"
    assert self_check.reveal_button.layout.min_width == "140px"
    assert self_check.reveal_button.disabled
    assert self_check.controls.children == (
        self_check.reveal_button,
        self_check.retry_button,
    )
    assert self_check.answer.description == "Your answer:"
    assert self_check.answer.rows == 1
    assert self_check.answer.layout.width == "fit-content"
    assert self_check.answer.layout.max_width == "100%"
    assert self_check.answer.layout.margin == "0 0 12px 0"
    assert self_check.widget.layout.width == "calc(100% - 24px)"
    assert self_check.widget.layout.margin == "0 12px 24px"
    assert "checkpoint-answer" in self_check.answer.get_state()["_dom_classes"]
    assert "checkpoint-self-check" in self_check.widget.get_state()["_dom_classes"]
    assert (
        "checkpoint-model-answer"
        in self_check.model_answer.get_state()["_dom_classes"]
    )
    assert self_check.status.value == ""
    assert self_check.status.layout.display == "none"
    assert self_check.retry_button.disabled
    assert self_check.retry_button.layout.display == "none"

    rendered_status = checkpoint_self_check.render_status("Status")
    assert "role='status'" in rendered_status
    assert "aria-live='polite'" in rendered_status
    assert "aria-atomic='true'" in rendered_status
    for required_style in (
        "field-sizing: content",
        "max-width: 100%",
        "overflow-y: hidden",
        "resize: none",
        "border-radius: 4px",
        "button.checkpoint-control",
        "cursor: default",
        "pointer-events: none",
        (
            ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p {"
            "line-height: 1.5;"
            "margin: 0 0 8px;"
            "}"
        ),
        (
            ".checkpoint-self-check .checkpoint-model-answer .widget-html-content p:last-child {"
            "margin-bottom: 0;"
            "}"
        ),
    ):
        assert required_style in checkpoint_self_check.CHECKPOINT_WIDGET_STYLE


def test_multiple_choice_labels_wrap_within_the_output() -> None:
    """Keep long choice labels visible in narrow notebook outputs."""
    self_check = create_checkpoint_self_check(choices=CHECKPOINT_CHOICES)

    assert self_check.answer.layout.width == "100%"
    assert self_check.answer.layout.max_width == "100%"
    assert all(
        choice_option.layout.width == "100%"
        for choice_option in self_check.choice_options
    )
    for required_style in (
        (
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
        ),
        (
            ".checkpoint-self-check .checkpoint-choice-answer .widget-checkbox .widget-label {"
            "min-width: 0;"
            "overflow: visible;"
            "text-overflow: clip;"
            "white-space: normal;"
            "overflow-wrap: anywhere;"
            "}"
        ),
    ):
        assert required_style in checkpoint_self_check.CHECKPOINT_WIDGET_STYLE


def test_inline_code_is_rendered_safely() -> None:
    """Render paired code markers without allowing arbitrary HTML."""
    rendered_inline_code = checkpoint_self_check.render_inline_code(
        "Run `pwd` before <script>.",
    )

    assert rendered_inline_code == (
        "Run <code>pwd</code> before &lt;script&gt;."
    )
    assert checkpoint_self_check.render_inline_code("Unmatched `code") == (
        "Unmatched `code"
    )


def test_multiple_choice_inline_code_preserves_the_raw_choice_value() -> None:
    """Keep formatted choice labels comparable with their stored answer."""
    choices = ("Run `pwd`.", "Run `ls`.")
    self_check = create_checkpoint_self_check(
        question="Run `pwd`.",
        choices=choices,
    )
    first_choice = self_check.choice_options[0]

    assert "Run <code>pwd</code>." in self_check.question.value
    assert "`" not in first_choice.description
    if "description_allow_html" in first_choice.traits():
        assert first_choice.get_state()["description_allow_html"]
        assert first_choice.description == "Run <code>pwd</code>."
    else:
        assert first_choice.description == "Run pwd."

    first_choice.value = True
    assert self_check.get_response_value() == "Run `pwd`."
    rendered_choice_result = checkpoint_self_check.render_choice_result(
        is_correct=True,
        correct_choice="Run `pwd`.",
    )
    assert (
        "<strong>Correct answer:</strong> Run <code>pwd</code>."
        in rendered_choice_result
    )


def test_multiple_choice_checkpoint_requires_selection_and_resets() -> None:
    """Require one choice, allow replacement, and clear it on retry."""
    self_check = create_checkpoint_self_check(choices=CHECKPOINT_CHOICES)

    assert isinstance(self_check.answer, checkpoint_self_check.widgets.VBox)
    assert "checkpoint-choice-answer" in self_check.answer.get_state()[
        "_dom_classes"
    ]
    assert len(self_check.choice_options) == 2
    assert not any(
        choice_option.value for choice_option in self_check.choice_options
    )
    assert self_check.reveal_button.disabled

    first_option, second_option = self_check.choice_options
    second_option.value = True
    assert self_check.get_response_value() == "Second option"
    assert not self_check.reveal_button.disabled
    second_option.value = False
    assert self_check.get_response_value() == ""
    assert self_check.reveal_button.disabled

    first_option.value = True
    second_option.value = True
    assert not first_option.value
    assert second_option.value
    assert self_check.get_response_value() == "Second option"

    with (
        patch.object(
            checkpoint_self_check,
            "load_model_answer",
            return_value=("Answer", CHECKPOINT_EVIDENCE),
        ),
        patch.object(
            checkpoint_self_check,
            "load_correct_choice",
            return_value="Second option",
        ),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert self_check.choice_result.layout.display == ""
    assert "checkpoint-choice-result-correct" in self_check.choice_result.value
    assert "aria-label='Correct'" in self_check.choice_result.value
    assert "&#10003;" in self_check.choice_result.value
    assert (
        "<strong>Correct answer:</strong> Second option"
        in self_check.choice_result.value
    )
    assert "<strong>Explanation:</strong> Answer" in self_check.model_answer.value
    assert all(
        choice_option.disabled for choice_option in self_check.choice_options
    )

    self_check.retry_answer(self_check.retry_button)
    assert not any(
        choice_option.value for choice_option in self_check.choice_options
    )
    assert all(
        not choice_option.disabled for choice_option in self_check.choice_options
    )
    assert self_check.reveal_button.disabled
    assert self_check.reveal_button.layout.display == ""
    assert self_check.choice_result.value == ""
    assert self_check.choice_result.layout.display == "none"
    assert self_check.status.value == ""
    assert self_check.status.layout.display == "none"


def test_multiple_choice_checkpoint_reports_incorrect_selection() -> None:
    """Show an incorrect outcome next to a locked choice response."""
    self_check = create_checkpoint_self_check(choices=CHECKPOINT_CHOICES)
    self_check.choice_options[0].value = True

    with (
        patch.object(
            checkpoint_self_check,
            "load_model_answer",
            return_value=("Answer", CHECKPOINT_EVIDENCE),
        ),
        patch.object(
            checkpoint_self_check,
            "load_correct_choice",
            return_value="Second option",
        ),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert self_check.choice_result.layout.display == ""
    assert "checkpoint-choice-result-incorrect" in self_check.choice_result.value
    assert "aria-label='Incorrect'" in self_check.choice_result.value
    assert "&#10007;" in self_check.choice_result.value
    assert (
        "<strong>Correct answer:</strong> Second option"
        in self_check.choice_result.value
    )
    assert "<strong>Explanation:</strong> Answer" in self_check.model_answer.value


def test_checkpoint_reveal_is_gated_and_locks_after_reveal() -> None:
    """Keep reveal unavailable without a response and lock it after reveal."""
    self_check = create_checkpoint_self_check()

    self_check.reveal_answer(self_check.reveal_button)
    assert not self_check.answer.disabled
    assert self_check.model_answer.value == ""

    self_check.answer.value = " "
    assert self_check.reveal_button.disabled
    self_check.answer.value = "Response"
    assert not self_check.reveal_button.disabled

    with patch.object(
        checkpoint_self_check,
        "load_model_answer",
        return_value=("Answer", CHECKPOINT_EVIDENCE),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert self_check.answer.disabled
    assert self_check.reveal_button.disabled
    assert self_check.reveal_button.layout.display == "none"
    assert not self_check.retry_button.disabled
    assert self_check.retry_button.layout.display == ""
    assert self_check.status.value == ""
    assert self_check.status.layout.display == "none"

    self_check.retry_answer(self_check.retry_button)
    assert self_check.answer.value == ""
    assert not self_check.answer.disabled
    assert self_check.reveal_button.disabled
    assert self_check.reveal_button.layout.display == ""
    assert self_check.retry_button.disabled
    assert self_check.retry_button.layout.display == "none"
    assert self_check.model_answer.value == ""
    assert self_check.model_answer.layout.display == "none"


def test_checkpoint_model_answer_failure_remains_retryable() -> None:
    """Keep unavailable or corrupt model-answer data recoverable."""
    self_check = create_checkpoint_self_check()
    self_check.answer.value = "Response"

    with patch.object(
        checkpoint_self_check,
        "load_model_answer",
        side_effect=checkpoint_self_check.CheckpointDataError(
            "The checkpoint data could not be read.",
        ),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert not self_check.answer.disabled
    assert not self_check.reveal_button.disabled
    assert self_check.reveal_button.layout.display is None
    assert self_check.retry_button.disabled
    assert self_check.retry_button.layout.display == "none"
    assert self_check.model_answer.value == ""
    assert self_check.model_answer.layout.display == "none"
    assert "Model answer unavailable." in self_check.status.value
    assert "role='status'" in self_check.status.value

    with patch.object(
        checkpoint_self_check,
        "load_model_answer",
        return_value=("Answer", CHECKPOINT_EVIDENCE),
    ):
        self_check.reveal_answer(self_check.reveal_button)

    assert self_check.answer.disabled
    assert self_check.reveal_button.disabled
    assert self_check.reveal_button.layout.display == "none"
    assert not self_check.retry_button.disabled
    assert self_check.model_answer.layout.display == ""
    assert "<strong>Model answer:</strong> Answer" in self_check.model_answer.value


def test_model_answer_links_to_source_sections() -> None:
    """Keep source links usable without adding visible source highlights."""
    rendered_answer = checkpoint_self_check.render_model_answer(
        "Answer with `pwd`",
        CHECKPOINT_EVIDENCE,
    )

    assert "<strong>Model answer:</strong> Answer with <code>pwd</code>" in (
        rendered_answer
    )
    assert (
        "<strong>Source sections above:</strong> "
        "<a href='#source' onclick='event.preventDefault()'>Source</a>."
    ) in rendered_answer
    assert "target=" not in rendered_answer
