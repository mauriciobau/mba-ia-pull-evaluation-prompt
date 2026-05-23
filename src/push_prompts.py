"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_FILE = (
    Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"
)
PROMPT_SLUG = "bug_to_user_story_v2"
REQUIRED_ENV_VARS = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
REQUIRED_FIELDS = [
    "description",
    "system_prompt",
    "user_prompt",
    "version",
    "tags",
    "techniques_applied",
]


def build_chat_prompt_template(prompt_data: dict) -> ChatPromptTemplate:
    """Cria um ChatPromptTemplate compativel com a entrada bug_report."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"].strip()),
            ("human", prompt_data["user_prompt"].strip()),
        ]
    )


def _metadata_readme(prompt_data: dict) -> str:
    techniques = prompt_data.get("techniques_applied", [])
    technique_lines = "\n".join(f"- {technique}" for technique in techniques)
    version = prompt_data.get("version", "")

    return (
        f"# {PROMPT_SLUG}\n\n"
        f"{prompt_data.get('description', '')}\n\n"
        f"Version: {version}\n\n"
        "Techniques applied:\n"
        f"{technique_lines}\n"
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        prompt_template = build_chat_prompt_template(prompt_data)
        tags = list(prompt_data.get("tags") or [])
        techniques = list(prompt_data.get("techniques_applied") or [])
        metadata_tags = tags + [f"technique:{technique}" for technique in techniques]

        print(f"Publicando prompt no LangSmith Hub: {prompt_name}")
        result = hub.push(
            prompt_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description=prompt_data.get("description", ""),
            readme=_metadata_readme(prompt_data),
            tags=metadata_tags,
        )
        print(f"Push concluido: {result}")
        return True
    except Exception as exc:
        error_text = str(exc).lower()
        if "nothing to commit" in error_text:
            print(f"Prompt '{prompt_name}' ja esta atualizado no LangSmith Hub.")
            return True

        print(f"Falha ao publicar prompt '{prompt_name}': {exc}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Prompt deve ser um objeto YAML na raiz."]

    for field in REQUIRED_FIELDS:
        if field not in prompt_data:
            errors.append(f"Campo obrigatorio faltando: {field}")

    for field in ("description", "system_prompt", "user_prompt", "version"):
        value = prompt_data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"Campo obrigatorio vazio ou invalido: {field}")

    user_prompt = prompt_data.get("user_prompt", "")
    if isinstance(user_prompt, str) and "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variavel {bug_report}")

    tags = prompt_data.get("tags", [])
    if not isinstance(tags, list) or not all(
        isinstance(tag, str) and tag.strip() for tag in tags
    ):
        errors.append("tags deve ser uma lista de textos nao vazios")

    techniques = prompt_data.get("techniques_applied", [])
    if not isinstance(techniques, list):
        errors.append("techniques_applied deve ser uma lista")
    elif (
        len(
            [
                technique
                for technique in techniques
                if isinstance(technique, str) and technique.strip()
            ]
        )
        < 2
    ):
        errors.append(
            f"Minimo de 2 tecnicas requeridas, encontradas: {len(techniques)}"
        )

    return len(errors) == 0, errors


def main() -> int:
    """Função principal"""
    print_section_header("LangSmith Prompt Push")

    if not PROMPT_FILE.exists():
        print(f"Arquivo de prompt nao encontrado: {PROMPT_FILE}")
        return 1

    prompt_data = load_yaml(str(PROMPT_FILE))
    if prompt_data is None:
        print("Push cancelado: nao foi possivel carregar o YAML do prompt.")
        return 1

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Push cancelado: prompt invalido.")
        for error in errors:
            print(f"   - {error}")
        return 1

    if not check_env_vars(REQUIRED_ENV_VARS):
        print("Push cancelado: credenciais ou namespace do LangSmith ausentes.")
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    prompt_name = f"{username}/{PROMPT_SLUG}"

    print(f"Arquivo: {PROMPT_FILE}")
    print(f"Destino: {prompt_name}")

    if not push_prompt_to_langsmith(prompt_name, prompt_data):
        return 1

    print("Push concluido com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
