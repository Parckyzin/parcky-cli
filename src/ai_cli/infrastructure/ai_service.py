"""
AI service implementation using Google Gemini with the new google.genai package.
"""

import re
import time

import google.genai as genai
from google.genai.types import GenerateContentConfig

from ..config.settings import AIConfig
from ..core.exceptions import AIServiceError
from ..core.interfaces import AIServiceInterface
from ..core.models import GitDiff, PullRequest


class GeminiAIService(AIServiceInterface):
    """Google Gemini AI service implementation using the new google.genai package."""

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 5  # seconds

    def __init__(self, config: AIConfig):
        self.config = config
        try:
            self.client = genai.Client(api_key=config.api_key)
        except Exception as e:
            raise AIServiceError(f"Failed to initialize Gemini AI service: {e}") from e

    def _extract_retry_delay(self, error_message: str) -> float:
        """Extract retry delay from error message if available."""
        match = re.search(r"retry in (\d+\.?\d*)s", error_message, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return self.BASE_RETRY_DELAY

    def _generate_content(self, prompt: str, context: str) -> str:
        """Generate content using the AI model with retry logic."""
        full_prompt = f"{prompt}\n\nCONTEXT:\n{context}"

        # Configure generation parameters
        config = GenerateContentConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
            system_instruction=self.config.system_instruction,
        )

        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.config.model_name, contents=full_prompt, config=config
                )

                if not response.text:
                    raise AIServiceError("AI service returned empty response")

                return response.text.strip()

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Check if it's a rate limit error (429)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    retry_delay = self._extract_retry_delay(error_str)
                    if attempt < self.MAX_RETRIES - 1:
                        print(
                            f"⏳ Rate limit hit. Waiting {retry_delay:.1f}s before retry ({attempt + 1}/{self.MAX_RETRIES})..."
                        )
                        time.sleep(retry_delay)
                        continue

                # For non-rate-limit errors, don't retry
                break

        raise AIServiceError(
            f"Failed to generate AI content: {last_error}"
        ) from last_error

    def generate_commit_message(self, diff: GitDiff) -> str:
        """Generate a commit message based on the diff."""
        prompt = """
        Gere uma mensagem de commit seguindo o padrão 'Conventional Commits'.
        Formato: <type>(<scope>): <subject>

        Tipos válidos: feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert

        Exemplos:
        - feat(auth): add login validation
        - fix(api): resolve user session timeout
        - docs: update installation guide
        - refactor(database): optimize query performance

        Regras:
        1. Use inglês para a mensagem
        2. Mantenha o subject conciso (máximo 50 caracteres)
        3. Use imperativo ("add" não "added")
        4. Não use ponto final no subject
        5. Se for mudança pequena/trivial, use tipo apropriado como "fix" ou "chore"

        Apenas retorne a mensagem, sem aspas ou explicações extras.
        """

        return self._generate_content(prompt, diff.content)

    def generate_pull_request(self, diff: GitDiff, commit_msg: str) -> PullRequest:
        """Generate a pull request title and description."""
        prompt = """
        Crie um título e uma descrição para um Pull Request baseados nas alterações.
        O formato deve ser Markdown.

        Estrutura obrigatória:
        Title: [Sugestão de título curto e claro]
        Body:
        ## O que foi feito
        - Liste as principais mudanças de forma clara e objetiva
        - Use tópicos para facilitar a leitura

        ## Por que foi feito
        - Explique a motivação técnica ou de negócio
        - Mencione problemas resolvidos se aplicável

        ## Como testar
        - Forneça passos claros para validar as mudanças
        - Inclua comandos específicos se necessário

        Regras:
        1. Título deve ser conciso e descritivo
        2. Use português para o corpo
        3. Seja específico nos passos de teste
        4. Mantenha formatação Markdown limpa
        """

        context = f"Commit Message: {commit_msg}\n\nDiff:\n{diff.content}"
        ai_response = self._generate_content(prompt, context)

        return self._parse_pr_response(ai_response)

    def _parse_pr_response(self, ai_response: str) -> PullRequest:
        """Parse the AI response to extract title and body."""
        lines = ai_response.split("\n")

        title = ""
        body_lines = []
        found_body = False

        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Body:"):
                found_body = True
            elif found_body:
                body_lines.append(line)

        if not title:
            # Fallback: use first line as title
            title = lines[0].strip()
            body_lines = lines[1:]

        body = "\n".join(body_lines).strip()

        return PullRequest(title=title, body=body)
