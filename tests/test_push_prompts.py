"""Unit tests for the LangSmith prompt push script."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


def valid_prompt_data():
    return {
        "description": "Optimized prompt",
        "system_prompt": "You are a Product Manager.",
        "user_prompt": "{bug_report}",
        "version": "v2",
        "tags": ["bug-analysis", "user-story"],
        "techniques_applied": ["Few-shot Learning", "Role Prompting"],
    }


def test_validate_prompt_empty_returns_missing_field_errors():
    import push_prompts

    is_valid, errors = push_prompts.validate_prompt({})

    assert is_valid is False
    assert "Campo obrigatorio faltando: description" in errors
    assert "Campo obrigatorio faltando: system_prompt" in errors
    assert "Campo obrigatorio faltando: user_prompt" in errors


def test_validate_prompt_rejects_blank_system_prompt():
    import push_prompts

    prompt_data = valid_prompt_data()
    prompt_data["system_prompt"] = "   "

    is_valid, errors = push_prompts.validate_prompt(prompt_data)

    assert is_valid is False
    assert "Campo obrigatorio vazio ou invalido: system_prompt" in errors


def test_validate_prompt_rejects_fewer_than_two_techniques():
    import push_prompts

    prompt_data = valid_prompt_data()
    prompt_data["techniques_applied"] = ["Few-shot Learning"]

    is_valid, errors = push_prompts.validate_prompt(prompt_data)

    assert is_valid is False
    assert "Minimo de 2 tecnicas requeridas, encontradas: 1" in errors


def test_valid_v2_yaml_passes_validate_prompt():
    import push_prompts
    from utils import load_yaml

    prompt_data = load_yaml(str(PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"))

    is_valid, errors = push_prompts.validate_prompt(prompt_data)

    assert is_valid is True
    assert errors == []


def test_build_chat_prompt_template_preserves_bug_report_input_variable():
    import push_prompts

    template = push_prompts.build_chat_prompt_template(valid_prompt_data())

    assert template.input_variables == ["bug_report"]
    assert len(template.messages) == 2
    assert template.messages[0].prompt.template == "You are a Product Manager."
    assert template.messages[1].prompt.template == "{bug_report}"


def test_push_prompt_to_langsmith_builds_template_and_metadata(monkeypatch):
    import push_prompts

    pushed = {}

    def fake_push(repo_full_name, object, **kwargs):
        pushed["repo_full_name"] = repo_full_name
        pushed["object"] = object
        pushed["kwargs"] = kwargs
        return "https://smith.langchain.com/prompts/user/bug_to_user_story_v2"

    monkeypatch.setattr(push_prompts.hub, "push", fake_push)

    assert (
        push_prompts.push_prompt_to_langsmith(
            "user/bug_to_user_story_v2",
            valid_prompt_data(),
        )
        is True
    )
    assert pushed["repo_full_name"] == "user/bug_to_user_story_v2"
    assert pushed["object"].input_variables == ["bug_report"]
    assert pushed["kwargs"]["new_repo_is_public"] is True
    assert pushed["kwargs"]["new_repo_description"] == "Optimized prompt"
    assert "technique:Few-shot Learning" in pushed["kwargs"]["tags"]


def test_push_prompt_to_langsmith_returns_false_on_push_error(monkeypatch):
    import push_prompts

    def fail_push(*args, **kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(push_prompts.hub, "push", fail_push)

    assert (
        push_prompts.push_prompt_to_langsmith(
            "user/bug_to_user_story_v2",
            valid_prompt_data(),
        )
        is False
    )


def test_push_prompt_to_langsmith_treats_noop_commit_as_success(monkeypatch):
    import push_prompts

    def fail_push(*args, **kwargs):
        raise RuntimeError("409 Conflict: Nothing to commit")

    monkeypatch.setattr(push_prompts.hub, "push", fail_push)

    assert push_prompts.push_prompt_to_langsmith(
        "user/bug_to_user_story_v2",
        valid_prompt_data(),
    ) is True


def test_main_returns_non_zero_when_username_missing(monkeypatch, capsys):
    import push_prompts

    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("USERNAME_LANGSMITH_HUB", raising=False)
    monkeypatch.setattr(
        push_prompts,
        "push_prompt_to_langsmith",
        lambda *args, **kwargs: pytest.fail("push should not run without username"),
    )

    exit_code = push_prompts.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "USERNAME_LANGSMITH_HUB" in captured.out
    assert "Push cancelado" in captured.out


def test_main_returns_zero_when_push_succeeds(monkeypatch, capsys):
    import push_prompts

    pushed = {}
    monkeypatch.setattr(push_prompts, "check_env_vars", lambda required: True)
    monkeypatch.setenv("USERNAME_LANGSMITH_HUB", "user")

    def fake_push(prompt_name, prompt_data):
        pushed["prompt_name"] = prompt_name
        pushed["prompt_data"] = prompt_data
        return True

    monkeypatch.setattr(push_prompts, "push_prompt_to_langsmith", fake_push)

    assert push_prompts.main() == 0
    assert pushed["prompt_name"] == "user/bug_to_user_story_v2"
    assert "Push concluido com sucesso." in capsys.readouterr().out


def test_main_returns_non_zero_when_prompt_validation_fails(monkeypatch, tmp_path):
    import push_prompts

    prompt_file = tmp_path / "invalid.yml"
    prompt_file.write_text("system_prompt: ''\n", encoding="utf-8")

    monkeypatch.setattr(push_prompts, "PROMPT_FILE", prompt_file)
    monkeypatch.setattr(
        push_prompts,
        "push_prompt_to_langsmith",
        lambda *args, **kwargs: pytest.fail("push should not run with invalid prompt"),
    )

    assert push_prompts.main() == 1
