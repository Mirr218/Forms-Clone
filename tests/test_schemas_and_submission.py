from app.schemas.form import FormCreate, FormUpdate, QuestionCreate


def test_question_create_does_not_require_form_id() -> None:
    question = QuestionCreate(
        question_type="text",
        text="Your name",
        is_required=True,
        position=1,
    )
    assert question.question_type == "text"


def test_form_update_can_include_questions() -> None:
    payload = FormUpdate(
        title="Updated title",
        questions=[
            QuestionCreate(
                question_type="radio",
                text="Pick one",
                options=["A", "B"],
                position=1,
            )
        ],
    )
    assert payload.questions is not None
    assert len(payload.questions) == 1


def test_form_create_questions_default_empty_list() -> None:
    payload = FormCreate(title="My form", description=None)
    assert payload.questions == []
