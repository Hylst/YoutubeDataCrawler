#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Integration Module - YouTube Data Analyzer

Module d'intégration pour les modèles de langage (LLM)
Supporte OpenAI, Anthropic, Google Gemini et DeepSeek

Auteur: Geoffroy Streit
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import requests
except ImportError:
    requests = None

from utils.error_handler import handle_errors, YouTubeAnalyzerError
from utils.config_manager import ConfigManager


class LLMProvider(Enum):
    """Enumération des fournisseurs LLM supportés."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class LLMResponse:
    """Classe pour encapsuler les réponses des LLM."""
    content: str
    provider: LLMProvider
    model: str
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMIntegration:
    """
    Classe principale pour l'intégration des modèles de langage.
    
    Gère les appels vers différents fournisseurs LLM avec une interface unifiée.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialise l'intégration LLM.
        
        Args:
            config_manager: Gestionnaire de configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config()
        
        # Configuration par défaut avec DeepSeek v3
        self.default_provider = LLMProvider.DEEPSEEK
        self.default_model = "deepseek-chat"
        
        # Initialisation des clients
        self._init_clients()
    
    def _init_clients(self):
        """
        Initialise les clients pour chaque fournisseur LLM.
        """
        self.clients = {}
        
        # Client OpenAI
        if openai and self.config and hasattr(self.config.llm, 'openai_api_key') and self.config.llm.openai_api_key:
            try:
                self.clients[LLMProvider.OPENAI] = openai.OpenAI(
                    api_key=str(self.config.llm.openai_api_key.get_secret_value())
                )
                self.logger.info("Client OpenAI initialisé")
            except Exception as e:
                self.logger.warning(f"Erreur initialisation OpenAI: {e}")
        
        # Client Anthropic
        if anthropic and self.config and hasattr(self.config.llm, 'anthropic_api_key') and self.config.llm.anthropic_api_key:
            try:
                self.clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(
                    api_key=str(self.config.llm.anthropic_api_key.get_secret_value())
                )
                self.logger.info("Client Anthropic initialisé")
            except Exception as e:
                self.logger.warning(f"Erreur initialisation Anthropic: {e}")
        
        # Client Google Gemini
        if genai and self.config and hasattr(self.config.llm, 'google_api_key') and self.config.llm.google_api_key:
            try:
                genai.configure(api_key=str(self.config.llm.google_api_key.get_secret_value()))
                self.clients[LLMProvider.GOOGLE] = genai
                self.logger.info("Client Google Gemini initialisé")
            except Exception as e:
                self.logger.warning(f"Erreur initialisation Google: {e}")
        
        # Client DeepSeek (via API REST) - using direct config access
        if requests and self.config and hasattr(self.config, 'deepseek_api_key') and self.config.deepseek_api_key:
            try:
                self.clients[LLMProvider.DEEPSEEK] = {
                    'api_key': str(self.config.deepseek_api_key.get_secret_value()),
                    'base_url': 'https://api.deepseek.com/v1'
                }
                self.logger.info("Client DeepSeek initialisé")
            except Exception as e:
                self.logger.warning(f"Erreur initialisation DeepSeek: {e}")
    
    @handle_errors
    def generate_text(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère du texte avec le LLM spécifié.
        
        Args:
            prompt: Prompt d'entrée
            provider: Fournisseur LLM (par défaut: DeepSeek)
            model: Modèle spécifique
            max_tokens: Nombre maximum de tokens
            temperature: Température de génération
            **kwargs: Arguments supplémentaires
            
        Returns:
            LLMResponse: Réponse du LLM
        """
        provider = provider or self.default_provider
        
        if provider not in self.clients:
            raise YouTubeAnalyzerError(
                f"Fournisseur {provider.value} non disponible",
                "llm_integration"
            )
        
        try:
            if provider == LLMProvider.DEEPSEEK:
                return self._generate_deepseek(prompt, model, max_tokens, temperature, **kwargs)
            elif provider == LLMProvider.OPENAI:
                return self._generate_openai(prompt, model, max_tokens, temperature, **kwargs)
            elif provider == LLMProvider.ANTHROPIC:
                return self._generate_anthropic(prompt, model, max_tokens, temperature, **kwargs)
            elif provider == LLMProvider.GOOGLE:
                return self._generate_google(prompt, model, max_tokens, temperature, **kwargs)
            else:
                raise YouTubeAnalyzerError(
                    f"Fournisseur {provider.value} non supporté",
                    "llm_integration"
                )
        except Exception as e:
            self.logger.error(f"Erreur génération {provider.value}: {e}")
            raise
    
    def _generate_deepseek(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère du texte avec DeepSeek v3.
        """
        model = model or "deepseek-chat"
        client_config = self.clients[LLMProvider.DEEPSEEK]
        
        headers = {
            "Authorization": f"Bearer {client_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        response = requests.post(
            f"{client_config['base_url']}/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        tokens_used = result.get('usage', {}).get('total_tokens')
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.DEEPSEEK,
            model=model,
            tokens_used=tokens_used
        )
    
    def _generate_openai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère du texte avec OpenAI.
        """
        model = model or "gpt-3.5-turbo"
        client = self.clients[LLMProvider.OPENAI]
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        content = response.choices[0].message.content
        tokens_used = response.usage.total_tokens if response.usage else None
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.OPENAI,
            model=model,
            tokens_used=tokens_used
        )
    
    def _generate_anthropic(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère du texte avec Anthropic Claude.
        """
        model = model or "claude-3-sonnet-20240229"
        client = self.clients[LLMProvider.ANTHROPIC]
        
        response = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        content = response.content[0].text
        tokens_used = response.usage.output_tokens + response.usage.input_tokens
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.ANTHROPIC,
            model=model,
            tokens_used=tokens_used
        )
    
    def _generate_google(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """
        Génère du texte avec Google Gemini.
        """
        model = model or "gemini-pro"
        
        generation_config = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }
        
        model_instance = genai.GenerativeModel(model)
        response = model_instance.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        content = response.text
        tokens_used = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
        
        return LLMResponse(
            content=content,
            provider=LLMProvider.GOOGLE,
            model=model,
            tokens_used=tokens_used
        )
    
    def get_available_providers(self) -> List[LLMProvider]:
        """
        Retourne la liste des fournisseurs disponibles.
        
        Returns:
            List[LLMProvider]: Liste des fournisseurs configurés
        """
        return list(self.clients.keys())
    
    def get_provider_models(self, provider: LLMProvider) -> List[str]:
        """
        Retourne la liste des modèles disponibles pour un fournisseur.
        
        Args:
            provider: Fournisseur LLM
            
        Returns:
            List[str]: Liste des modèles disponibles
        """
        models_map = {
            LLMProvider.DEEPSEEK: ["deepseek-chat", "deepseek-coder"],
            LLMProvider.OPENAI: ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
            LLMProvider.ANTHROPIC: ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            LLMProvider.GOOGLE: ["gemini-pro", "gemini-pro-vision"]
        }
        
        return models_map.get(provider, [])
    
    def set_default_provider(self, provider: LLMProvider, model: Optional[str] = None):
        """
        Définit le fournisseur et modèle par défaut.
        
        Args:
            provider: Fournisseur LLM
            model: Modèle spécifique (optionnel)
        """
        if provider not in self.clients:
            raise YouTubeAnalyzerError(
                f"Fournisseur {provider.value} non disponible",
                "llm_integration"
            )
        
        self.default_provider = provider
        if model:
            self.default_model = model
        
        self.logger.info(f"Fournisseur par défaut: {provider.value}, Modèle: {self.default_model}")


# Instance globale pour faciliter l'utilisation
_llm_integration = None


def get_llm_integration() -> LLMIntegration:
    """
    Retourne l'instance globale de LLMIntegration.
    
    Returns:
        LLMIntegration: Instance du gestionnaire LLM
    """
    global _llm_integration
    if _llm_integration is None:
        _llm_integration = LLMIntegration()
    return _llm_integration


def generate_text(
    prompt: str,
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMResponse:
    """
    Fonction utilitaire pour générer du texte rapidement.
    
    Args:
        prompt: Prompt d'entrée
        provider: Fournisseur LLM
        model: Modèle spécifique
        **kwargs: Arguments supplémentaires
        
    Returns:
        LLMResponse: Réponse du LLM
    """
    llm = get_llm_integration()
    return llm.generate_text(prompt, provider, model, **kwargs)