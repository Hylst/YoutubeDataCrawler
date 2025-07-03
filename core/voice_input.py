#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de reconnaissance vocale

Ce module gère la reconnaissance vocale pour permettre
la dictée de prompts pour la génération de contenu.
"""

import logging
import threading
import time
from typing import Optional, Callable, Dict, Any

try:
    import speech_recognition as sr
    import pyaudio
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None
    pyaudio = None

# Configuration du logging
logger = logging.getLogger(__name__)


class VoiceInputManager:
    """
    Gestionnaire de reconnaissance vocale.
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire de reconnaissance vocale.
        """
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.listening_thread = None
        self.callback = None
        
        # Vérification de la disponibilité des modules
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.warning("Modules de reconnaissance vocale non disponibles. "
                         "Installez speech_recognition et pyaudio.")
            return
        
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Calibrage du microphone
            self._calibrate_microphone()
            
            logger.info("Gestionnaire de reconnaissance vocale initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la reconnaissance vocale: {str(e)}")
    
    def is_available(self) -> bool:
        """
        Vérifie si la reconnaissance vocale est disponible.
        
        Returns:
            bool: True si disponible, False sinon
        """
        return SPEECH_RECOGNITION_AVAILABLE and self.recognizer is not None
    
    def _calibrate_microphone(self):
        """
        Calibre le microphone pour réduire le bruit ambiant.
        """
        try:
            with self.microphone as source:
                logger.info("Calibrage du microphone en cours...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Calibrage terminé")
        except Exception as e:
            logger.warning(f"Erreur lors du calibrage du microphone: {str(e)}")
    
    def listen_once(self, language: str = "fr-FR", timeout: int = 10) -> Optional[str]:
        """
        Écoute une fois et retourne le texte reconnu.
        
        Args:
            language (str): Code de langue (ex: "fr-FR", "en-US")
            timeout (int): Timeout en secondes
        
        Returns:
            str: Texte reconnu ou None si erreur
        """
        if not self.is_available():
            logger.error("Reconnaissance vocale non disponible")
            return None
        
        try:
            logger.info("Écoute en cours... Parlez maintenant.")
            
            with self.microphone as source:
                # Écoute de l'audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=30)
            
            logger.info("Reconnaissance en cours...")
            
            # Reconnaissance vocale
            text = self.recognizer.recognize_google(audio, language=language)
            
            logger.info(f"Texte reconnu: {text}")
            return text
        
        except sr.WaitTimeoutError:
            logger.warning("Timeout: aucun son détecté")
            return None
        except sr.UnknownValueError:
            logger.warning("Impossible de comprendre l'audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Erreur du service de reconnaissance: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la reconnaissance vocale: {str(e)}")
            return None
    
    def start_continuous_listening(self, callback: Callable[[str], None], 
                                  language: str = "fr-FR") -> bool:
        """
        Démarre l'écoute continue.
        
        Args:
            callback (callable): Fonction appelée avec le texte reconnu
            language (str): Code de langue
        
        Returns:
            bool: True si démarré avec succès, False sinon
        """
        if not self.is_available():
            logger.error("Reconnaissance vocale non disponible")
            return False
        
        if self.is_listening:
            logger.warning("Écoute déjà en cours")
            return False
        
        self.callback = callback
        self.is_listening = True
        
        # Démarrage du thread d'écoute
        self.listening_thread = threading.Thread(
            target=self._continuous_listening_loop,
            args=(language,),
            daemon=True
        )
        self.listening_thread.start()
        
        logger.info("Écoute continue démarrée")
        return True
    
    def stop_continuous_listening(self):
        """
        Arrête l'écoute continue.
        """
        if not self.is_listening:
            return
        
        self.is_listening = False
        
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=2)
        
        logger.info("Écoute continue arrêtée")
    
    def _continuous_listening_loop(self, language: str):
        """
        Boucle d'écoute continue.
        
        Args:
            language (str): Code de langue
        """
        while self.is_listening:
            try:
                with self.microphone as source:
                    # Écoute avec timeout court pour permettre l'arrêt
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                
                if not self.is_listening:
                    break
                
                # Reconnaissance vocale
                text = self.recognizer.recognize_google(audio, language=language)
                
                if text and self.callback:
                    self.callback(text)
            
            except sr.WaitTimeoutError:
                # Timeout normal, continue la boucle
                continue
            except sr.UnknownValueError:
                # Audio non compris, continue
                continue
            except sr.RequestError as e:
                logger.error(f"Erreur du service de reconnaissance: {str(e)}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erreur dans la boucle d'écoute: {str(e)}")
                time.sleep(1)
    
    def get_available_microphones(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des microphones disponibles.
        
        Returns:
            list: Liste des microphones avec leurs informations
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return []
        
        try:
            microphones = []
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                microphones.append({
                    'index': index,
                    'name': name
                })
            return microphones
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des microphones: {str(e)}")
            return []
    
    def set_microphone(self, device_index: int) -> bool:
        """
        Définit le microphone à utiliser.
        
        Args:
            device_index (int): Index du microphone
        
        Returns:
            bool: True si défini avec succès, False sinon
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            return False
        
        try:
            self.microphone = sr.Microphone(device_index=device_index)
            self._calibrate_microphone()
            logger.info(f"Microphone défini: index {device_index}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la définition du microphone: {str(e)}")
            return False
    
    def test_microphone(self) -> Dict[str, Any]:
        """
        Teste le microphone actuel.
        
        Returns:
            dict: Résultats du test
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Reconnaissance vocale non disponible'
            }
        
        try:
            logger.info("Test du microphone... Dites quelque chose.")
            
            with self.microphone as source:
                # Test d'écoute courte
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Test de reconnaissance
            text = self.recognizer.recognize_google(audio, language="fr-FR")
            
            return {
                'success': True,
                'recognized_text': text,
                'message': 'Test réussi'
            }
        
        except sr.WaitTimeoutError:
            return {
                'success': False,
                'error': 'Timeout: aucun son détecté'
            }
        except sr.UnknownValueError:
            return {
                'success': False,
                'error': 'Audio détecté mais non compris'
            }
        except sr.RequestError as e:
            return {
                'success': False,
                'error': f'Erreur du service: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur: {str(e)}'
            }
    
    def configure_recognition_settings(self, energy_threshold: int = None, 
                                     dynamic_energy_threshold: bool = None,
                                     pause_threshold: float = None):
        """
        Configure les paramètres de reconnaissance.
        
        Args:
            energy_threshold (int): Seuil d'énergie pour la détection vocale
            dynamic_energy_threshold (bool): Ajustement automatique du seuil
            pause_threshold (float): Durée de pause pour fin de phrase
        """
        if not self.recognizer:
            return
        
        try:
            if energy_threshold is not None:
                self.recognizer.energy_threshold = energy_threshold
                logger.info(f"Seuil d'énergie défini: {energy_threshold}")
            
            if dynamic_energy_threshold is not None:
                self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold
                logger.info(f"Seuil dynamique: {dynamic_energy_threshold}")
            
            if pause_threshold is not None:
                self.recognizer.pause_threshold = pause_threshold
                logger.info(f"Seuil de pause: {pause_threshold}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la configuration: {str(e)}")


class VoicePromptGenerator:
    """
    Générateur de prompts basé sur la reconnaissance vocale.
    """
    
    def __init__(self, voice_manager: VoiceInputManager):
        """
        Initialise le générateur de prompts vocaux.
        
        Args:
            voice_manager (VoiceInputManager): Gestionnaire de reconnaissance vocale
        """
        self.voice_manager = voice_manager
        self.prompt_templates = {
            'title': "Génère un titre YouTube pour une vidéo sur: {content}",
            'description': "Génère une description YouTube pour une vidéo sur: {content}",
            'tags': "Génère des tags YouTube pour une vidéo sur: {content}",
            'thumbnail': "Génère une description d'image pour une miniature YouTube sur: {content}"
        }
    
    def generate_prompt_from_voice(self, prompt_type: str, 
                                  language: str = "fr-FR") -> Optional[str]:
        """
        Génère un prompt à partir d'une entrée vocale.
        
        Args:
            prompt_type (str): Type de prompt ('title', 'description', 'tags', 'thumbnail')
            language (str): Code de langue
        
        Returns:
            str: Prompt généré ou None si erreur
        """
        if not self.voice_manager.is_available():
            logger.error("Reconnaissance vocale non disponible")
            return None
        
        if prompt_type not in self.prompt_templates:
            logger.error(f"Type de prompt non supporté: {prompt_type}")
            return None
        
        # Écoute de l'entrée vocale
        logger.info(f"Décrivez le contenu pour générer un {prompt_type}...")
        voice_content = self.voice_manager.listen_once(language=language, timeout=15)
        
        if not voice_content:
            return None
        
        # Génération du prompt
        template = self.prompt_templates[prompt_type]
        prompt = template.format(content=voice_content)
        
        logger.info(f"Prompt généré: {prompt}")
        return prompt
    
    def add_custom_template(self, name: str, template: str):
        """
        Ajoute un template de prompt personnalisé.
        
        Args:
            name (str): Nom du template
            template (str): Template avec placeholder {content}
        """
        self.prompt_templates[name] = template
        logger.info(f"Template personnalisé ajouté: {name}")