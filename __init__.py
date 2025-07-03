#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube Data Analyzer

Application modulaire pour l'analyse de contenu YouTube
avec génération IA et export multi-formats.

Version: 1.0.0
Auteur: YouTube Data Analyzer Team
Licence: MIT
"""

__version__ = "1.0.0"
__author__ = "YouTube Data Analyzer Team"
__license__ = "MIT"
__description__ = "Application modulaire pour l'analyse de contenu YouTube avec génération IA"

# Imports principaux pour faciliter l'utilisation
try:
    from .core.youtube_api import YouTubeAPI
    from .core.llm_api import LLMManager
    from .core.imagegen_api import ImageGeneratorManager
    from .core.presets import PresetManager
    from .core.filters import DataFilter, FilterCriteria
    from .core.export import ExportManager
    from .core.voice_input import VoiceInputManager
    from .database.db_init import initialize_database, get_db_connection
except ImportError:
    # Imports relatifs ne fonctionnent pas en exécution directe
    pass

# Métadonnées du package
__all__ = [
    'YouTubeAPI',
    'LLMManager', 
    'ImageGeneratorManager',
    'PresetManager',
    'DataFilter',
    'FilterCriteria',
    'ExportManager',
    'VoiceInputManager',
    'initialize_database',
    'get_db_connection'
]

# Configuration par défaut
DEFAULT_CONFIG = {
    'database_path': 'data/youtube_analyzer.db',
    'export_directory': 'data/export',
    'thumbnails_directory': 'data/thumbnails',
    'logs_directory': 'data/logs',
    'env_file': 'data/.env',
    'log_level': 'INFO',
    'max_retries': 3,
    'api_timeout': 30,
    'default_ui': 'pyqt6'
}

# Informations sur les dépendances
REQUIRED_DEPENDENCIES = [
    'google-api-python-client',
    'requests',
    'python-dotenv',
    'sqlite3'  # Inclus dans Python standard
]

OPTIONAL_DEPENDENCIES = {
    'ui': ['PyQt6'],
    'web': ['streamlit', 'flask'],
    'voice': ['speech_recognition', 'pyaudio'],
    'image': ['Pillow'],
    'data': ['pandas', 'numpy'],
    'dev': ['pytest', 'black', 'flake8']
}

def get_version():
    """
    Retourne la version de l'application.
    
    Returns:
        str: Version de l'application
    """
    return __version__

def get_info():
    """
    Retourne les informations sur l'application.
    
    Returns:
        dict: Informations sur l'application
    """
    return {
        'name': 'YouTube Data Analyzer',
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'description': __description__
    }

def check_dependencies():
    """
    Vérifie la disponibilité des dépendances.
    
    Returns:
        dict: Statut des dépendances
    """
    import importlib
    
    status = {
        'required': {},
        'optional': {}
    }
    
    # Vérification des dépendances requises
    for dep in REQUIRED_DEPENDENCIES:
        try:
            if dep == 'sqlite3':
                import sqlite3
            else:
                importlib.import_module(dep.replace('-', '_'))
            status['required'][dep] = True
        except ImportError:
            status['required'][dep] = False
    
    # Vérification des dépendances optionnelles
    for category, deps in OPTIONAL_DEPENDENCIES.items():
        status['optional'][category] = {}
        for dep in deps:
            try:
                importlib.import_module(dep.replace('-', '_'))
                status['optional'][category][dep] = True
            except ImportError:
                status['optional'][category][dep] = False
    
    return status