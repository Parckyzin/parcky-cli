from .gemini import GeminiAIService


from ai_cli.config.settings import AIConfig
from ai_cli.core.common.enums import AvailableAiHosts


def get_ai_service(config: AIConfig):
    """Factory function to get the appropriate AI service based on configuration."""
    if config.model_host == AvailableAiHosts.GOOGLE:
        return GeminiAIService(config)
    else:
        raise ValueError(f"Unsupported AI host: {config.model_host}")
    
    
__all__ = ["get_ai_service"]