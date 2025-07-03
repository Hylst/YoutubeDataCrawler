#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'interface avec les APIs LLM

Ce module gère les interactions avec différents fournisseurs d'IA
pour la génération de titres, descriptions et tags YouTube.
"""

import json
import logging
import requests
from typing import Dict, List, Optional, Union
from abc import ABC, abstractmethod

# Configuration du logging
logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """
    Classe de base abstraite pour tous les fournisseurs LLM.
    """
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialise le fournisseur LLM.
        
        Args:
            api_key (str): Clé API du fournisseur
            model (str): Nom du modèle à utiliser
        """
        self.api_key = api_key
        self.model = model
        self.base_url = self._get_base_url()
    
    @abstractmethod
    def _get_base_url(self) -> str:
        """
        Retourne l'URL de base de l'API.
        """
        pass
    
    @abstractmethod
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        """
        Formate la requête selon le format du fournisseur.
        """
        pass
    
    @abstractmethod
    def _extract_response(self, response: Dict) -> str:
        """
        Extrait le texte généré de la réponse.
        """
        pass
    
    def generate_content(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Génère du contenu à partir d'un prompt.
        
        Args:
            prompt (str): Prompt d'entrée
            **kwargs: Arguments supplémentaires
        
        Returns:
            str: Contenu généré ou None si erreur
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = self._format_request(prompt, **kwargs)
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = self._extract_response(response.json())
                logger.info(f"Contenu généré avec succès par {self.__class__.__name__}")
                return result
            else:
                logger.error(f"Erreur API {self.__class__.__name__}: {response.status_code} - {response.text}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête {self.__class__.__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la génération de contenu {self.__class__.__name__}: {str(e)}")
            return None


class OpenAIProvider(BaseLLMProvider):
    """
    Fournisseur pour l'API OpenAI (GPT).
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get('max_tokens', 500),
            "temperature": kwargs.get('temperature', 0.7)
        }
    
    def _extract_response(self, response: Dict) -> str:
        return response['choices'][0]['message']['content'].strip()


class ClaudeProvider(BaseLLMProvider):
    """
    Fournisseur pour l'API Anthropic Claude.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return "https://api.anthropic.com/v1/messages"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "model": self.model,
            "max_tokens": kwargs.get('max_tokens', 500),
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    
    def _extract_response(self, response: Dict) -> str:
        return response['content'][0]['text'].strip()


class GeminiProvider(BaseLLMProvider):
    """
    Fournisseur pour l'API Google Gemini.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": kwargs.get('max_tokens', 500),
                "temperature": kwargs.get('temperature', 0.7)
            }
        }
    
    def _extract_response(self, response: Dict) -> str:
        return response['candidates'][0]['content']['parts'][0]['text'].strip()
    
    def generate_content(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Génère du contenu avec Gemini (utilise un format d'URL différent).
        """
        try:
            url = f"{self.base_url}?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            
            data = self._format_request(prompt, **kwargs)
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = self._extract_response(response.json())
                logger.info("Contenu généré avec succès par Gemini")
                return result
            else:
                logger.error(f"Erreur API Gemini: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de contenu Gemini: {str(e)}")
            return None


class DeepSeekProvider(BaseLLMProvider):
    """
    Fournisseur pour l'API DeepSeek.
    """
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return "https://api.deepseek.com/v1/chat/completions"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kwargs.get('max_tokens', 500),
            "temperature": kwargs.get('temperature', 0.7)
        }
    
    def _extract_response(self, response: Dict) -> str:
        return response['choices'][0]['message']['content'].strip()


class LLMManager:
    """
    Gestionnaire principal pour les interactions avec les LLMs.
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire LLM.
        """
        self.providers = {}
        self.default_provider = None
    
    def add_provider(self, name: str, provider: BaseLLMProvider, is_default: bool = False):
        """
        Ajoute un fournisseur LLM.
        
        Args:
            name (str): Nom du fournisseur
            provider (BaseLLMProvider): Instance du fournisseur
            is_default (bool): Si ce fournisseur est le défaut
        """
        self.providers[name] = provider
        if is_default or not self.default_provider:
            self.default_provider = name
        logger.info(f"Fournisseur LLM ajouté: {name}")
    
    def generate_youtube_title(self, content: str, provider_name: str = None) -> Optional[str]:
        """
        Génère un titre YouTube optimisé.
        
        Args:
            content (str): Contenu source (description, transcript, etc.)
            provider_name (str): Nom du fournisseur à utiliser
        
        Returns:
            str: Titre généré ou None si erreur
        """
        prompt = f"""
        Génère un titre YouTube accrocheur et optimisé SEO basé sur le contenu suivant.
        Le titre doit:
        - Faire entre 50-60 caractères
        - Être accrocheur et inciter au clic
        - Contenir des mots-clés pertinents
        - Éviter le clickbait trompeur
        
        Contenu source:
        {content}
        
        Titre YouTube optimisé:
        """
        
        return self._generate_content(prompt, provider_name)
    
    def generate_youtube_description(self, content: str, provider_name: str = None, length: str = "medium") -> Optional[str]:
        """
        Génère une description YouTube.
        
        Args:
            content (str): Contenu source
            provider_name (str): Nom du fournisseur à utiliser
            length (str): Longueur souhaitée ("short", "medium", "long")
        
        Returns:
            str: Description générée ou None si erreur
        """
        length_instructions = {
            "short": "2-3 phrases courtes",
            "medium": "1-2 paragraphes (100-200 mots)",
            "long": "3-4 paragraphes détaillés (300-500 mots)"
        }
        
        prompt = f"""
        Génère une description YouTube engageante basée sur le contenu suivant.
        La description doit:
        - Faire {length_instructions.get(length, length_instructions['medium'])}
        - Être informative et engageante
        - Inclure des mots-clés pertinents
        - Inciter à l'interaction (like, commentaire, abonnement)
        
        Contenu source:
        {content}
        
        Description YouTube:
        """
        
        return self._generate_content(prompt, provider_name)
    
    def generate_youtube_tags(self, content: str, provider_name: str = None) -> Optional[List[str]]:
        """
        Génère des tags YouTube.
        
        Args:
            content (str): Contenu source
            provider_name (str): Nom du fournisseur à utiliser
        
        Returns:
            list: Liste de tags ou None si erreur
        """
        prompt = f"""
        Génère une liste de 10-15 tags YouTube pertinents basés sur le contenu suivant.
        Les tags doivent:
        - Être pertinents au contenu
        - Inclure des mots-clés populaires
        - Varier entre tags généraux et spécifiques
        - Être séparés par des virgules
        
        Contenu source:
        {content}
        
        Tags YouTube (séparés par des virgules):
        """
        
        result = self._generate_content(prompt, provider_name)
        if result:
            # Conversion en liste de tags
            tags = [tag.strip() for tag in result.split(',')]
            return [tag for tag in tags if tag]  # Supprime les tags vides
        return None
    
    def _generate_content(self, prompt: str, provider_name: str = None) -> Optional[str]:
        """
        Génère du contenu en utilisant le fournisseur spécifié.
        
        Args:
            prompt (str): Prompt d'entrée
            provider_name (str): Nom du fournisseur à utiliser
        
        Returns:
            str: Contenu généré ou None si erreur
        """
        provider_name = provider_name or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            logger.error(f"Fournisseur LLM non trouvé: {provider_name}")
            return None
        
        provider = self.providers[provider_name]
        return provider.generate_content(prompt)
    
    def test_provider(self, provider_name: str) -> bool:
        """
        Teste la connectivité d'un fournisseur.
        
        Args:
            provider_name (str): Nom du fournisseur à tester
        
        Returns:
            bool: True si le test réussit, False sinon
        """
        if provider_name not in self.providers:
            return False
        
        provider = self.providers[provider_name]
        test_prompt = "Dis simplement 'Test réussi' en français."
        result = provider.generate_content(test_prompt)
        
        return result is not None and "test" in result.lower()