"""
AI service implementation using Google Gemini with the new google.genai package.
"""

import re
import time

import google.genai as genai
from google.genai.types import GenerateContentConfig

from ai_cli.config.cache import get_cache
from ai_cli.config.prompts import get_prompt
from ai_cli.config.settings import AIConfig
from ai_cli.core.exceptions import AIServiceError
from ai_cli.core.interfaces import AIServiceInterface
from ai_cli.core.models import GitDiff, PullRequest


class GeminiAIService(AIServiceInterface):
    """Google Gemini AI service implementation using the new google.genai package."""

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 5  # seconds

    def __init__(self, config: AIConfig):
        self.config = config
        self._models_cache: list[str] | None = None
        try:
            self.client = genai.Client(api_key=config.api_key)
        except Exception as e:
            raise AIServiceError(
                f"Failed to initialize Gemini AI service: {e}",
                user_message=(
                    "Failed to initialize the AI client. Check your AI_API_KEY "
                    "and try again."
                ),
            ) from e

    def _extract_retry_delay(self, error_message: str) -> float:
        """Extract retry delay from error message if available."""
        match = re.search(r"retry in (\d+\.?\d*)s", error_message, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return self.BASE_RETRY_DELAY

    def _generate_content(self, prompt: str, context: str) -> str:
        """Generate content using the AI model with retry logic."""
        full_prompt = f"{prompt}\n\nCONTEXT:\n{context}"
        cache = get_cache()
        cache_key: str | None = None
        if self.config.cache_enabled and cache.is_safe_for_cache(prompt, context):
            cache_key = cache.make_ai_cache_key(
                self.config.model_name,
                prompt,
                context,
                self.config.temperature,
                self.config.max_tokens,
            )
            cached = cache.get_ai_response(cache_key)
            if cached:
                return cached

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
                    raise AIServiceError(
                        "AI service returned empty response",
                        user_message=(
                            "The AI service returned an empty response. Try again "
                            "or adjust your prompt settings."
                        ),
                    )

                text_response = response.text.strip()
                if (
                    self.config.cache_enabled
                    and cache_key
                    and cache.is_safe_for_cache(text_response)
                ):
                    cache.set_ai_response(cache_key, text_response)
                return text_response

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
            f"Failed to generate AI content: {last_error}",
            user_message=(
                "Failed to generate AI content. Check your network connection "
                "or API credentials and try again."
            ),
        ) from last_error

    def generate_commit_message(self, diff: GitDiff) -> str:
        """Generate a commit message based on the diff."""
        prompt = get_prompt("commit_message")
        return self._generate_content(prompt, diff.content)

    def generate_pull_request(self, diff: GitDiff, commit_msg: str) -> PullRequest:
        """Generate a pull request title and description."""
        prompt = get_prompt("pull_request")
        context = f"Commit Message: {commit_msg}\n\nDiff:\n{diff.content}"
        ai_response = self._generate_content(prompt, context)

        return self._parse_pr_response(ai_response)

    def generate_text(self, prompt: str, context: str) -> str:
        """Generate a raw text response from a prompt and context."""
        return self._generate_content(prompt, context)

    @staticmethod
    def _parse_pr_response(ai_response: str) -> PullRequest:
        """Parse the AI response to extract title and body."""
        lines = ai_response.split("\n")
        title = ""
        body_lines: list[str] = []
        found_body = False

        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Body:"):
                found_body = True
            elif found_body:
                body_lines.append(line)

        if not title:
            title = lines[0].strip() if lines else ""
            remaining = lines[1:] if len(lines) > 1 else []
            if remaining and remaining[0].strip() == "":
                remaining = remaining[1:]
            body_lines = remaining

        body = "\n".join(body_lines).strip()

        return PullRequest(title=title, body=body)

    def get_available_models(self) -> list[str]:
        """Get a list of available AI models from the service."""
        if self._models_cache is not None:
            return list(self._models_cache)
        try:
            models = self.client.models.list()
            formatted_names = [model.name.split("models/")[-1] for model in models]

            self._models_cache = sorted(
                [
                    n
                    for n in formatted_names
                    if isinstance(n, str) and n.startswith("gemini-")
                ]
            )
            return list(self._models_cache)
        except Exception as e:
            raise AIServiceError(
                f"Failed to retrieve available models: {e}",
                user_message=(
                    "Failed to retrieve available AI models. Check your network "
                    "connection or API credentials and try again."
                ),
            ) from e
