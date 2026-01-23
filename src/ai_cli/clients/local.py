from ai_cli.config.settings import AIConfig
from ai_cli.core.exceptions import AIServiceError
from ai_cli.core.interfaces import AIServiceInterface
from ai_cli.core.models import GitDiff, PullRequest


class LocalAIService(AIServiceInterface):
    """Stub local AI client."""

    def __init__(self, config: AIConfig):
        self.config = config

    def generate_commit_message(self, _diff: GitDiff) -> str:
        raise AIServiceError(
            "Local AI provider not implemented.",
            user_message="Local AI provider is not implemented yet.",
        )

    def generate_pull_request(self, _diff: GitDiff, _commit_msg: str) -> PullRequest:
        raise AIServiceError(
            "Local AI provider not implemented.",
            user_message="Local AI provider is not implemented yet.",
        )

    def generate_text(self, _prompt: str, _context: str) -> str:
        raise AIServiceError(
            "Local AI provider not implemented.",
            user_message="Local AI provider is not implemented yet.",
        )

    def get_available_models(self) -> list[str]:
        raise AIServiceError(
            "Local AI provider not implemented.",
            user_message="Local AI provider is not implemented yet.",
        )
