"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"
REQUIRED_ENV_VARS = ["LANGSMITH_API_KEY"]


def _as_serializable(value):
    """Converte objetos LangChain/Pydantic para tipos seguros para YAML."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _as_serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_as_serializable(item) for item in value]
    if hasattr(value, "model_dump"):
        return _as_serializable(value.model_dump())
    if hasattr(value, "dict"):
        return _as_serializable(value.dict())
    return str(value)


def _message_role(message) -> str:
    class_name = message.__class__.__name__.lower()
    if "system" in class_name:
        return "system"
    if "human" in class_name or "user" in class_name:
        return "user"
    if "ai" in class_name or "assistant" in class_name:
        return "assistant"
    return getattr(message, "type", "unknown")


def _message_template(message) -> str:
    prompt = getattr(message, "prompt", None)
    if prompt is not None:
        template = getattr(prompt, "template", None)
        if template is not None:
            return str(template)

    template = getattr(message, "template", None)
    if template is not None:
        return str(template)

    content = getattr(message, "content", None)
    if content is not None:
        return str(content)

    return str(message)


def serialize_prompt(prompt) -> dict:
    """
    Serializa um prompt LangChain em uma estrutura YAML local estavel.

    Args:
        prompt: Objeto retornado por langchain.hub.pull().

    Returns:
        Dicionario pronto para save_yaml().
    """
    input_variables = list(getattr(prompt, "input_variables", []) or [])
    raw_messages = getattr(prompt, "messages", None) or []
    messages = [
        {
            "role": _message_role(message),
            "template": _message_template(message),
        }
        for message in raw_messages
    ]

    system_prompt = next(
        (message["template"] for message in messages if message["role"] == "system"),
        "",
    )
    user_prompt = next(
        (message["template"] for message in messages if message["role"] == "user"),
        "",
    )

    if not messages:
        user_prompt = str(getattr(prompt, "template", "") or "")

    return {
        "bug_to_user_story_v1": {
            "description": "Prompt inicial de baixa qualidade puxado do LangSmith Prompt Hub.",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "source": SOURCE_PROMPT,
            "input_variables": input_variables,
            "messages": messages,
            "serialized": _as_serializable(
                prompt.to_json() if hasattr(prompt, "to_json") else prompt
            ),
        }
    }


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt v1 no LangSmith Prompt Hub e salva em YAML local.

    Returns:
        True se sucesso, False caso contrario.
    """
    print_section_header("Pull do prompt inicial")
    print(f"Origem: {SOURCE_PROMPT}")
    print(f"Destino: {OUTPUT_FILE}")

    try:
        prompt = hub.pull(SOURCE_PROMPT)
        prompt_data = serialize_prompt(prompt)
        if not save_yaml(prompt_data, str(OUTPUT_FILE)):
            print("Falha ao salvar o prompt localmente.")
            return False
    except Exception as exc:
        print(f"Falha ao puxar prompt '{SOURCE_PROMPT}' do LangSmith: {exc}")
        return False

    print(f"Prompt salvo com sucesso em {OUTPUT_FILE}")
    return True


def main() -> int:
    """Função principal"""
    print_section_header("LangSmith Prompt Pull")

    if not check_env_vars(REQUIRED_ENV_VARS):
        print("Pull cancelado: credenciais do LangSmith ausentes.")
        return 1

    if not pull_prompts_from_langsmith():
        return 1

    print("Pull concluido com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
