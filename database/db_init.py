#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'initialisation de la base de données

Ce module gère la création et l'initialisation de la base de données SQLite3
pour l'application YouTube Data Analyzer.
"""

import os
import sqlite3
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def initialize_database(db_path):
    """
    Initialise la base de données en créant les tables nécessaires
    à partir du fichier schema.sql.
    
    Args:
        db_path (str): Chemin vers le fichier de base de données SQLite3
    
    Returns:
        bool: True si l'initialisation a réussi, False sinon
    """
    try:
        # Création du répertoire parent si nécessaire
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lecture du fichier schema.sql
        schema_path = Path(__file__).parent / 'schema.sql'
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_script = f.read()
        
        # Exécution du script SQL
        cursor.executescript(schema_script)
        
        # Insertion de presets par défaut si la table est vide
        cursor.execute("SELECT COUNT(*) FROM presets")
        if cursor.fetchone()[0] == 0:
            create_default_presets(cursor)
        
        # Validation des changements
        conn.commit()
        conn.close()
        
        logger.info(f"Base de données initialisée avec succès: {db_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        return False


def create_default_presets(cursor):
    """
    Crée des presets par défaut dans la base de données avec informations étendues.
    
    Args:
        cursor: Curseur SQLite3 actif
    """
    default_presets = [
        {
            'name': 'Informations de base',
            'description': 'Informations essentielles: nom, auteur, descriptif, thumbnail',
            'content_type': 'video',
            'filters': '{"extended_info": false, "fields": ["title", "channel_title", "description", "thumbnail_url", "published_at", "duration"]}',
            'llm_model': 'gpt-3.5-turbo',
            'image_model': 'stable-diffusion',
            'export_format': 'json',
            'ui_template': 'basic',
            'is_default': 1
        },
        {
            'name': 'Analyse complète avec statistiques',
            'description': 'Analyse détaillée avec statistiques et métadonnées',
            'content_type': 'video',
            'filters': '{"extended_info": true, "fields": ["title", "channel_title", "description", "thumbnail_url", "published_at", "duration", "view_count", "like_count", "comment_count", "tags", "category_id", "language", "definition", "caption", "privacy_status", "topic_categories", "default_audio_language"]}',
            'llm_model': 'claude-3-sonnet',
            'image_model': 'stable-diffusion',
            'export_format': 'xlsx',
            'ui_template': 'detailed',
            'is_default': 0
        },
        {
            'name': 'Analyse technique avancée',
            'description': 'Analyse technique complète avec toutes les métadonnées disponibles',
            'content_type': 'video',
            'filters': '{"extended_info": true, "fields": ["title", "channel_title", "description", "thumbnail_url", "published_at", "duration", "view_count", "like_count", "comment_count", "tags", "category_id", "language", "definition", "caption", "licensed_content", "dimension", "projection", "privacy_status", "upload_status", "license", "embeddable", "public_stats_viewable", "topic_categories", "relevant_topic_ids", "default_audio_language", "live_broadcast_content", "thumbnails_standard", "thumbnails_maxres", "actual_start_time", "actual_end_time", "scheduled_start_time", "concurrent_viewers", "recording_date", "location_description"]}',
            'llm_model': 'gpt-4',
            'image_model': 'midjourney-api',
            'export_format': 'json',
            'ui_template': 'advanced',
            'is_default': 0
        }
    ]
    
    for preset in default_presets:
        cursor.execute("""
        INSERT INTO presets (name, description, content_type, filters, 
                           llm_model, image_model, export_format, ui_template, is_default)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            preset['name'],
            preset['description'],
            preset['content_type'],
            preset['filters'],
            preset['llm_model'],
            preset['image_model'],
            preset['export_format'],
            preset['ui_template'],
            preset['is_default']
        ))
    
    logger.info("Presets par défaut créés avec succès")


def get_connection(db_path):
    """
    Établit une connexion à la base de données.
    
    Args:
        db_path (str): Chemin vers le fichier de base de données SQLite3
    
    Returns:
        sqlite3.Connection: Objet de connexion à la base de données
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
    return conn