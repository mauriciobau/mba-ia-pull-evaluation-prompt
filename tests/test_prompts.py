"""Testes automatizados para validacao de prompts."""
import pytest
import yaml
import sys
from pathlib import Path
from typing import Any

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
REQUIRED_FIELDS = {
    "description",
    "system_prompt",
    "user_prompt",
    "version",
    "tags",
    "techniques_applied",
}


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def flatten_values(value: Any) -> str:
    """Serializa valores aninhados para buscas simples de conteudo."""
    if isinstance(value, dict):
        return "\n".join(flatten_values(item) for item in value.values())
    if isinstance(value, list):
        return "\n".join(flatten_values(item) for item in value)
    return str(value)


class TestPrompts:
    @pytest.fixture(scope="class")
    def prompt_data(self):
        """Carrega o prompt otimizado v2."""
        prompt_data = load_prompts(str(PROMPT_PATH))
        assert isinstance(prompt_data, dict), "O YAML v2 deve ser um dicionario na raiz."
        missing_fields = REQUIRED_FIELDS - set(prompt_data)
        assert not missing_fields, f"Campos raiz obrigatorios ausentes: {sorted(missing_fields)}"

        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura basica do prompt invalida: {errors}"
        return prompt_data

    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo raiz 'system_prompt' ausente."
        system_prompt = prompt_data["system_prompt"]
        assert isinstance(system_prompt, str), "Campo 'system_prompt' deve ser texto."
        assert system_prompt.strip(), "Campo 'system_prompt' nao pode estar vazio."

    def test_prompt_has_role_definition(self, prompt_data):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_data.get("system_prompt", "").lower()
        role_markers = ("product manager", "product owner")
        assert any(marker in system_prompt for marker in role_markers), (
            "O system_prompt deve definir uma persona de Product Manager ou Product Owner."
        )

    def test_prompt_mentions_format(self, prompt_data):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt_text = prompt_data.get("system_prompt", "").lower()
        format_markers = (
            "markdown",
            "user story",
            "como [persona]",
            "eu quero",
            "para que",
        )
        assert any(marker in prompt_text for marker in format_markers), (
            "O system_prompt deve exigir Markdown ou formato padrao de user story."
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt_text = prompt_data.get("system_prompt", "").lower()
        assert "example input:" in prompt_text, (
            "O system_prompt deve conter marcador de exemplo de entrada."
        )
        assert "example output:" in prompt_text, (
            "O system_prompt deve conter marcador de exemplo de saida."
        )

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        prompt_text = flatten_values(prompt_data)
        assert "[TODO]" not in prompt_text, "O YAML do prompt ainda contem marcador [TODO]."
        assert "TODO" not in prompt_text, "O YAML do prompt ainda contem marcador TODO."

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert isinstance(techniques, list), (
            "Campo raiz 'techniques_applied' deve ser uma lista."
        )
        assert len(techniques) >= 2, (
            "Campo 'techniques_applied' deve listar pelo menos duas tecnicas."
        )
        normalized = {technique.lower() for technique in techniques}
        assert "few-shot learning" in normalized, (
            "Campo 'techniques_applied' deve incluir Few-shot Learning."
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
