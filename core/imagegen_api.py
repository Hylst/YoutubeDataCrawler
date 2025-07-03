#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'interface avec les APIs de génération d'images

Ce module gère les interactions avec différents fournisseurs d'IA
pour la génération de miniatures YouTube.
"""

import os
import json
import base64
import logging
import requests
from typing import Dict, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)


class BaseImageGenerator(ABC):
    """
    Classe de base abstraite pour tous les générateurs d'images.
    """
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialise le générateur d'images.
        
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
    def _extract_image_data(self, response: Dict) -> Tuple[bytes, str]:
        """
        Extrait les données d'image de la réponse.
        
        Returns:
            Tuple[bytes, str]: Données binaires de l'image et format
        """
        pass
    
    def generate_image(self, prompt: str, output_dir: str, filename: str = None, **kwargs) -> Optional[str]:
        """
        Génère une image à partir d'un prompt et la sauvegarde.
        
        Args:
            prompt (str): Prompt de description de l'image
            output_dir (str): Répertoire de sortie
            filename (str): Nom du fichier (sans extension)
            **kwargs: Arguments supplémentaires
        
        Returns:
            str: Chemin vers l'image générée ou None si erreur
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
                timeout=60  # Timeout plus long pour la génération d'images
            )
            
            if response.status_code == 200:
                image_data, image_format = self._extract_image_data(response.json())
                
                # Création du répertoire de sortie si nécessaire
                os.makedirs(output_dir, exist_ok=True)
                
                # Génération du nom de fichier si non fourni
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"thumbnail_{timestamp}"
                
                # Chemin complet du fichier
                file_path = os.path.join(output_dir, f"{filename}.{image_format}")
                
                # Sauvegarde de l'image
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Image générée avec succès: {file_path}")
                return file_path
            else:
                logger.error(f"Erreur API {self.__class__.__name__}: {response.status_code} - {response.text}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête {self.__class__.__name__}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'image {self.__class__.__name__}: {str(e)}")
            return None


class StableDiffusionGenerator(BaseImageGenerator):
    """
    Générateur d'images utilisant l'API HuggingFace pour Stable Diffusion.
    """
    
    def __init__(self, api_key: str, model: str = "stabilityai/stable-diffusion-xl-base-1.0"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return f"https://api-inference.huggingface.co/models/{self.model}"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": kwargs.get('negative_prompt', ''),
                "num_inference_steps": kwargs.get('steps', 30),
                "guidance_scale": kwargs.get('guidance_scale', 7.5),
                "width": kwargs.get('width', 1280),
                "height": kwargs.get('height', 720)
            }
        }
    
    def _extract_image_data(self, response: Dict) -> Tuple[bytes, str]:
        # Pour HuggingFace, la réponse est directement l'image en base64
        image_data = base64.b64decode(response[0]['image_base64'])
        return image_data, 'png'
    
    def generate_image(self, prompt: str, output_dir: str, filename: str = None, **kwargs) -> Optional[str]:
        """
        Génère une image avec Stable Diffusion via HuggingFace.
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
                timeout=60
            )
            
            if response.status_code == 200:
                # Création du répertoire de sortie si nécessaire
                os.makedirs(output_dir, exist_ok=True)
                
                # Génération du nom de fichier si non fourni
                if not filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"thumbnail_{timestamp}"
                
                # Chemin complet du fichier
                file_path = os.path.join(output_dir, f"{filename}.jpg")
                
                # Sauvegarde de l'image
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Image générée avec succès: {file_path}")
                return file_path
            else:
                logger.error(f"Erreur API Stable Diffusion: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'image Stable Diffusion: {str(e)}")
            return None


class DalleGenerator(BaseImageGenerator):
    """
    Générateur d'images utilisant l'API DALL-E d'OpenAI.
    """
    
    def __init__(self, api_key: str, model: str = "dall-e-3"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        return "https://api.openai.com/v1/images/generations"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": kwargs.get('size', "1024x1024"),
            "response_format": "b64_json"
        }
    
    def _extract_image_data(self, response: Dict) -> Tuple[bytes, str]:
        image_b64 = response['data'][0]['b64_json']
        image_data = base64.b64decode(image_b64)
        return image_data, 'png'


class MidjourneyGenerator(BaseImageGenerator):
    """
    Générateur d'images utilisant une API tierce pour Midjourney.
    Note: Midjourney n'a pas d'API officielle, ceci est un exemple d'intégration.
    """
    
    def __init__(self, api_key: str, model: str = "midjourney"):
        super().__init__(api_key, model)
    
    def _get_base_url(self) -> str:
        # URL fictive pour une API tierce Midjourney
        return "https://api.example.com/v1/midjourney/generate"
    
    def _format_request(self, prompt: str, **kwargs) -> Dict:
        return {
            "prompt": prompt,
            "width": kwargs.get('width', 1280),
            "height": kwargs.get('height', 720),
            "quality": kwargs.get('quality', "standard"),
            "style": kwargs.get('style', "raw")
        }
    
    def _extract_image_data(self, response: Dict) -> Tuple[bytes, str]:
        image_url = response['image_url']
        image_response = requests.get(image_url, timeout=30)
        return image_response.content, 'jpg'


class ImageGeneratorManager:
    """
    Gestionnaire principal pour les générateurs d'images.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialise le gestionnaire de générateurs d'images.
        
        Args:
            output_dir (str): Répertoire de sortie pour les images générées
        """
        self.generators = {}
        self.default_generator = None
        self.output_dir = output_dir
        
        # Création du répertoire de sortie si nécessaire
        os.makedirs(output_dir, exist_ok=True)
    
    def add_generator(self, name: str, generator: BaseImageGenerator, is_default: bool = False):
        """
        Ajoute un générateur d'images.
        
        Args:
            name (str): Nom du générateur
            generator (BaseImageGenerator): Instance du générateur
            is_default (bool): Si ce générateur est le défaut
        """
        self.generators[name] = generator
        if is_default or not self.default_generator:
            self.default_generator = name
        logger.info(f"Générateur d'images ajouté: {name}")
    
    def generate_youtube_thumbnail(self, title: str, description: str = None, 
                                  generator_name: str = None, style: str = "modern") -> Optional[str]:
        """
        Génère une miniature YouTube.
        
        Args:
            title (str): Titre de la vidéo
            description (str): Description de la vidéo
            generator_name (str): Nom du générateur à utiliser
            style (str): Style de la miniature
        
        Returns:
            str: Chemin vers l'image générée ou None si erreur
        """
        # Styles prédéfinis pour les miniatures
        style_prompts = {
            "modern": "modern, clean, minimalist design, high contrast",
            "gaming": "vibrant gaming thumbnail, action-packed, exciting",
            "tech": "futuristic tech design, digital, blue tones",
            "vlog": "bright, colorful vlog thumbnail, lifestyle",
            "tutorial": "educational, clear, instructional design"
        }
        
        style_text = style_prompts.get(style, style_prompts["modern"])
        
        # Construction du prompt
        prompt = f"""
        Create a YouTube thumbnail for a video titled '{title}'.
        Style: {style_text}.
        The thumbnail should be eye-catching, professional, and optimized for YouTube.
        It should have a 16:9 aspect ratio and be suitable for YouTube's platform.
        """
        
        if description:
            prompt += f"\nThe video is about: {description[:100]}..."
        
        # Génération du nom de fichier à partir du titre
        safe_title = "".join(c if c.isalnum() else "_" for c in title[:30])
        filename = f"thumbnail_{safe_title}_{datetime.now().strftime('%Y%m%d')}"
        
        return self._generate_image(prompt, filename, generator_name)
    
    def _generate_image(self, prompt: str, filename: str, generator_name: str = None) -> Optional[str]:
        """
        Génère une image en utilisant le générateur spécifié.
        
        Args:
            prompt (str): Prompt de description de l'image
            filename (str): Nom du fichier (sans extension)
            generator_name (str): Nom du générateur à utiliser
        
        Returns:
            str: Chemin vers l'image générée ou None si erreur
        """
        generator_name = generator_name or self.default_generator
        
        if not generator_name or generator_name not in self.generators:
            logger.error(f"Générateur d'images non trouvé: {generator_name}")
            return None
        
        generator = self.generators[generator_name]
        return generator.generate_image(prompt, self.output_dir, filename)
    
    def test_generator(self, generator_name: str) -> bool:
        """
        Teste la connectivité d'un générateur.
        
        Args:
            generator_name (str): Nom du générateur à tester
        
        Returns:
            bool: True si le test réussit, False sinon
        """
        if generator_name not in self.generators:
            return False
        
        generator = self.generators[generator_name]
        test_prompt = "A simple test image with blue background and text 'Test'"
        test_file = "generator_test"
        
        result = generator.generate_image(test_prompt, self.output_dir, test_file)
        return result is not None and os.path.exists(result)