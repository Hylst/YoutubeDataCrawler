# -*- coding: utf-8 -*-
"""
Configuration Manager

Robust configuration management system using pydantic for validation and type safety.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class YouTubeAPIConfig(BaseSettings):
    """
    YouTube API configuration settings.
    """
    api_key: SecretStr = Field(..., description="YouTube Data API v3 key")
    request_delay: float = Field(1.0, description="Delay between API requests (seconds)")
    max_retries: int = Field(3, description="Maximum number of API request retries")
    timeout: int = Field(30, description="API request timeout (seconds)")
    
    model_config = SettingsConfigDict(
        env_prefix="YOUTUBE_",
        case_sensitive=False
    )

class LLMConfig(BaseSettings):
    """
    Large Language Model configuration settings.
    """
    # API Keys
    openai_api_key: Optional[SecretStr] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[SecretStr] = Field(None, description="Anthropic API key")
    google_api_key: Optional[SecretStr] = Field(None, description="Google API key")
    deepseek_api_key: Optional[SecretStr] = Field(None, description="DeepSeek API key")
    openrouter_api_key: Optional[SecretStr] = Field(None, description="OpenRouter API key")
    x_ai_api_key: Optional[SecretStr] = Field(None, description="X.AI API key")
    
    # Default settings
    default_provider: str = Field("OpenAI", description="Default LLM provider")
    default_model: str = Field("gpt-4o", description="Default LLM model")
    
    # Model configurations
    openai_models: List[str] = Field(["gpt-4o", "gpt-4-turbo"], description="Available OpenAI models")
    anthropic_models: List[str] = Field(["claude-3-5-sonnet", "claude-3-opus"], description="Available Anthropic models")
    google_models: List[str] = Field(["gemini-2.5-pro", "gemini-2.5-flash"], description="Available Google models")
    deepseek_models: List[str] = Field(["deepseek-v3", "r1"], description="Available DeepSeek models")
    openrouter_models: List[str] = Field(["DeepSeek/R1-0528", "Google/Gemini-2.0-Flash-Experimental"], description="Available OpenRouter models")
    x_ai_models: List[str] = Field(["grok-3-beta", "grok-3-mini-beta"], description="Available X.AI models")
    
    # Request settings
    max_tokens: int = Field(2000, description="Maximum tokens per request")
    temperature: float = Field(0.7, description="Temperature for text generation")
    timeout: int = Field(60, description="LLM request timeout (seconds)")
    max_retries: int = Field(3, description="Maximum number of LLM request retries")
    
    @validator('default_provider')
    def validate_provider(cls, v):
        valid_providers = ['OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'OpenRouter', 'X.AI']
        if v not in valid_providers:
            raise ValueError(f'Provider must be one of: {valid_providers}')
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )

class ImageGenConfig(BaseSettings):
    """
    Image generation configuration settings.
    """
    # API Keys
    huggingface_api_key: Optional[SecretStr] = Field(None, description="HuggingFace API key")
    openai_image_api_key: Optional[SecretStr] = Field(None, description="OpenAI DALL-E API key")
    
    # Default settings
    default_provider: str = Field("HuggingFace", description="Default image generation provider")
    default_model: str = Field("black-forest-labs/FLUX.1-schnell", description="Default image generation model")
    
    # Model configurations
    huggingface_models: List[str] = Field(
        ["black-forest-labs/FLUX.1-schnell", "evalstate/flux1_schnell"],
        description="Available HuggingFace models"
    )
    
    # Image settings
    default_width: int = Field(1024, description="Default image width")
    default_height: int = Field(1024, description="Default image height")
    quality: str = Field("standard", description="Image quality (standard/hd)")
    
    # Request settings
    timeout: int = Field(120, description="Image generation timeout (seconds)")
    max_retries: int = Field(2, description="Maximum number of image generation retries")
    
    @validator('default_provider')
    def validate_provider(cls, v):
        valid_providers = ['HuggingFace', 'OpenAI', 'Midjourney']
        if v not in valid_providers:
            raise ValueError(f'Provider must be one of: {valid_providers}')
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )

class VoiceConfig(BaseSettings):
    """
    Voice recognition configuration settings.
    """
    # Recognition settings
    energy_threshold: int = Field(300, description="Energy threshold for voice detection")
    dynamic_energy_threshold: bool = Field(True, description="Enable dynamic energy threshold")
    pause_threshold: float = Field(0.8, description="Pause threshold (seconds)")
    timeout: float = Field(5.0, description="Listening timeout (seconds)")
    phrase_timeout: float = Field(0.3, description="Phrase timeout (seconds)")
    
    # Audio settings
    sample_rate: int = Field(16000, description="Audio sample rate")
    chunk_size: int = Field(1024, description="Audio chunk size")
    
    model_config = SettingsConfigDict(
        env_prefix="VOICE_",
        case_sensitive=False
    )

class DatabaseConfig(BaseSettings):
    """
    Database configuration settings.
    """
    path: str = Field("data/youtube_analyzer.db", description="Database file path")
    backup_interval: int = Field(24, description="Backup interval (hours)")
    max_backups: int = Field(7, description="Maximum number of backups to keep")
    
    # Connection settings
    timeout: int = Field(30, description="Database connection timeout (seconds)")
    check_same_thread: bool = Field(False, description="SQLite check_same_thread setting")
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=False
    )

class UIConfig(BaseSettings):
    """
    User interface configuration settings.
    """
    # Default interface
    default_interface: str = Field("PyQt6", description="Default UI interface")
    
    # PyQt6 settings
    window_width: int = Field(1200, description="Default window width")
    window_height: int = Field(800, description="Default window height")
    theme: str = Field("light", description="UI theme (light/dark)")
    
    # Streamlit settings
    streamlit_port: int = Field(8501, description="Streamlit server port")
    streamlit_host: str = Field("localhost", description="Streamlit server host")
    
    @validator('default_interface')
    def validate_interface(cls, v):
        valid_interfaces = ['PyQt6', 'Streamlit', 'CLI']
        if v not in valid_interfaces:
            raise ValueError(f'Interface must be one of: {valid_interfaces}')
        return v
    
    @validator('theme')
    def validate_theme(cls, v):
        valid_themes = ['light', 'dark']
        if v not in valid_themes:
            raise ValueError(f'Theme must be one of: {valid_themes}')
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="UI_",
        case_sensitive=False
    )

class LoggingConfig(BaseSettings):
    """
    Logging configuration settings.
    """
    level: str = Field("INFO", description="Logging level")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: str = Field("data/logs/youtube_analyzer.log", description="Log file path")
    max_file_size: int = Field(10485760, description="Maximum log file size (bytes)")
    backup_count: int = Field(5, description="Number of log file backups")
    
    @validator('level')
    def validate_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Level must be one of: {valid_levels}')
        return v.upper()
    
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        case_sensitive=False
    )

class AppConfig(BaseSettings):
    """
    Main application configuration that combines all sub-configurations.
    """
    # Application metadata
    app_name: str = Field("YouTube Data Analyzer", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug: bool = Field(False, description="Debug mode")
    
    # Sub-configurations
    youtube: YouTubeAPIConfig = Field(default_factory=YouTubeAPIConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    image_gen: ImageGenConfig = Field(default_factory=ImageGenConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

class ConfigManager:
    """
    Configuration manager for the YouTube Data Analyzer application.
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            env_file (Optional[Path]): Path to the .env file
        """
        self.env_file = env_file or Path(".env")
        self.config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """
        Load configuration from environment and .env file.
        """
        try:
            # Load .env file if it exists
            if self.env_file.exists():
                load_dotenv(self.env_file)
                logger.info(f"Loaded configuration from {self.env_file}")
            else:
                logger.warning(f"Configuration file {self.env_file} not found")
            
            # Initialize configuration
            self.config = AppConfig()
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    def get_config(self) -> AppConfig:
        """
        Get the application configuration.
        
        Returns:
            AppConfig: The application configuration
        """
        if self.config is None:
            raise RuntimeError("Configuration not loaded")
        return self.config
    
    def validate_config(self) -> Dict[str, Any]:
        """
        Validate the current configuration and return validation results.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        if self.config is None:
            return {"valid": False, "errors": ["Configuration not loaded"]}
        
        errors = []
        warnings = []
        
        # Check YouTube API key
        if not self.config.youtube.api_key:
            errors.append("YouTube API key is required")
        
        # Check at least one LLM provider
        llm_providers = [
            self.config.llm.openai_api_key,
            self.config.llm.anthropic_api_key,
            self.config.llm.google_api_key,
            self.config.llm.deepseek_api_key,
            self.config.llm.openrouter_api_key,
            self.config.llm.x_ai_api_key
        ]
        
        if not any(key for key in llm_providers if key):
            warnings.append("No LLM API keys configured - AI features will be unavailable")
        
        # Check image generation providers
        if not self.config.image_gen.huggingface_api_key and not self.config.image_gen.openai_image_api_key:
            warnings.append("No image generation API keys configured - thumbnail generation will be unavailable")
        
        # Check database path
        db_path = Path(self.config.database.path)
        if not db_path.parent.exists():
            warnings.append(f"Database directory does not exist: {db_path.parent}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_config_summary(self) -> str:
        """
        Generate a summary of the current configuration.
        
        Returns:
            str: Configuration summary
        """
        if self.config is None:
            return "Configuration not loaded"
        
        validation = self.validate_config()
        
        summary = []
        summary.append("=" * 60)
        summary.append(f"CONFIGURATION SUMMARY - {self.config.app_name} v{self.config.version}")
        summary.append("=" * 60)
        
        # Validation status
        if validation["valid"]:
            summary.append("✅ Configuration is valid")
        else:
            summary.append("❌ Configuration has errors")
        
        # API Keys status
        summary.append("\nAPI KEYS:")
        summary.append("-" * 10)
        summary.append(f"YouTube API: {'✓' if self.config.youtube.api_key else '✗'}")
        summary.append(f"OpenAI: {'✓' if self.config.llm.openai_api_key else '○'}")
        summary.append(f"Anthropic: {'✓' if self.config.llm.anthropic_api_key else '○'}")
        summary.append(f"Google: {'✓' if self.config.llm.google_api_key else '○'}")
        summary.append(f"DeepSeek: {'✓' if self.config.llm.deepseek_api_key else '○'}")
        summary.append(f"OpenRouter: {'✓' if self.config.llm.openrouter_api_key else '○'}")
        summary.append(f"X.AI: {'✓' if self.config.llm.x_ai_api_key else '○'}")
        summary.append(f"HuggingFace: {'✓' if self.config.image_gen.huggingface_api_key else '○'}")
        
        # Settings
        summary.append("\nSETTINGS:")
        summary.append("-" * 10)
        summary.append(f"Default LLM: {self.config.llm.default_provider} ({self.config.llm.default_model})")
        summary.append(f"Default Image Gen: {self.config.image_gen.default_provider}")
        summary.append(f"Default UI: {self.config.ui.default_interface}")
        summary.append(f"Database: {self.config.database.path}")
        summary.append(f"Log Level: {self.config.logging.level}")
        
        # Errors and warnings
        if validation["errors"]:
            summary.append("\n❌ ERRORS:")
            for error in validation["errors"]:
                summary.append(f"  • {error}")
        
        if validation["warnings"]:
            summary.append("\n⚠️  WARNINGS:")
            for warning in validation["warnings"]:
                summary.append(f"  • {warning}")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def reload_config(self) -> None:
        """
        Reload the configuration from the .env file.
        """
        logger.info("Reloading configuration...")
        self._load_config()

# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        ConfigManager: The configuration manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> AppConfig:
    """
    Get the application configuration.
    
    Returns:
        AppConfig: The application configuration
    """
    return get_config_manager().get_config()