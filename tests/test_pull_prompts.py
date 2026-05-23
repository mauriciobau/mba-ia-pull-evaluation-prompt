"""Unit tests for the LangSmith prompt pull script."""
import importlib
import sys
from pathlib import Path

import pytest
import yaml
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


def test_import_does_not_pull_from_langsmith(monkeypatch):
    """Importing the module must not execute a LangSmith network pull."""
    import langchain.hub

    def fail_pull(*args, **kwargs):
        raise AssertionError("hub.pull must not run during import")

    monkeypatch.setattr(langchain.hub, "pull", fail_pull)
    sys.modules.pop("pull_prompts", None)

    module = importlib.import_module("pull_prompts")

    assert module.SOURCE_PROMPT == "leonanluppi/bug_to_user_story_v1"


def test_main_returns_non_zero_when_langsmith_api_key_missing(monkeypatch, capsys):
    import pull_prompts

    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.setattr(
        pull_prompts,
        "pull_prompts_from_langsmith",
        lambda: pytest.fail("pull should not run without credentials"),
    )

    exit_code = pull_prompts.main()

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "LANGSMITH_API_KEY" in captured.out
    assert "Pull cancelado" in captured.out


def test_serialize_prompt_returns_yaml_safe_dictionary():
    import pull_prompts

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Transforme bugs em user stories."),
            ("human", "{bug_report}"),
        ]
    )

    prompt_data = pull_prompts.serialize_prompt(prompt)
    reloaded = yaml.safe_load(yaml.safe_dump(prompt_data, sort_keys=False))
    saved_prompt = reloaded["bug_to_user_story_v1"]

    assert saved_prompt["source"] == pull_prompts.SOURCE_PROMPT
    assert saved_prompt["system_prompt"] == "Transforme bugs em user stories."
    assert saved_prompt["user_prompt"] == "{bug_report}"
    assert saved_prompt["input_variables"] == ["bug_report"]
    assert saved_prompt["messages"] == [
        {"role": "system", "template": "Transforme bugs em user stories."},
        {"role": "user", "template": "{bug_report}"},
    ]


def test_serialize_prompt_supports_plain_prompt_template():
    import pull_prompts

    prompt = PromptTemplate.from_template("Bug: {bug_report}")

    prompt_data = pull_prompts.serialize_prompt(prompt)
    saved_prompt = prompt_data["bug_to_user_story_v1"]

    assert saved_prompt["system_prompt"] == ""
    assert saved_prompt["user_prompt"] == "Bug: {bug_report}"
    assert saved_prompt["messages"] == []


def test_serialization_helpers_cover_fallback_shapes():
    import pull_prompts

    class DictOnly:
        def dict(self):
            return {"path": Path("prompts/example.yml")}

    class AssistantMessage:
        template = "assistant text"

    class UnknownMessage:
        type = "custom"
        content = "content text"

    assert pull_prompts._as_serializable(Path("prompts/example.yml")) == "prompts/example.yml"
    assert pull_prompts._as_serializable(DictOnly()) == {"path": "prompts/example.yml"}
    assert pull_prompts._message_role(AssistantMessage()) == "assistant"
    assert pull_prompts._message_template(AssistantMessage()) == "assistant text"
    assert pull_prompts._message_role(UnknownMessage()) == "custom"
    assert pull_prompts._message_template(UnknownMessage()) == "content text"


def test_pull_prompts_from_langsmith_saves_serialized_prompt(monkeypatch):
    import pull_prompts

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Sistema"),
            ("human", "{bug_report}"),
        ]
    )
    saved = {}

    monkeypatch.setattr(pull_prompts.hub, "pull", lambda prompt_name: prompt)

    def fake_save_yaml(data, file_path):
        saved["data"] = data
        saved["file_path"] = file_path
        return True

    monkeypatch.setattr(pull_prompts, "save_yaml", fake_save_yaml)

    assert pull_prompts.pull_prompts_from_langsmith() is True
    assert saved["file_path"].endswith("prompts/bug_to_user_story_v1.yml")
    assert saved["data"]["bug_to_user_story_v1"]["user_prompt"] == "{bug_report}"


def test_pull_prompts_from_langsmith_returns_false_when_save_fails(monkeypatch):
    import pull_prompts

    prompt = PromptTemplate.from_template("Bug: {bug_report}")
    monkeypatch.setattr(pull_prompts.hub, "pull", lambda prompt_name: prompt)
    monkeypatch.setattr(pull_prompts, "save_yaml", lambda data, file_path: False)

    assert pull_prompts.pull_prompts_from_langsmith() is False


def test_pull_prompts_from_langsmith_returns_false_on_pull_error(monkeypatch):
    import pull_prompts

    def fail_pull(prompt_name):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(pull_prompts.hub, "pull", fail_pull)

    assert pull_prompts.pull_prompts_from_langsmith() is False


def test_main_returns_zero_when_pull_succeeds(monkeypatch, capsys):
    import pull_prompts

    monkeypatch.setattr(pull_prompts, "check_env_vars", lambda required: True)
    monkeypatch.setattr(pull_prompts, "pull_prompts_from_langsmith", lambda: True)

    assert pull_prompts.main() == 0
    assert "Pull concluido com sucesso." in capsys.readouterr().out


def test_main_returns_non_zero_when_pull_fails(monkeypatch):
    import pull_prompts

    monkeypatch.setattr(pull_prompts, "check_env_vars", lambda required: True)
    monkeypatch.setattr(pull_prompts, "pull_prompts_from_langsmith", lambda: False)

    assert pull_prompts.main() == 1
