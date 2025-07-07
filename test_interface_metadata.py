#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier l'affichage des métadonnées étendues
dans l'interface utilisateur.
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from ui.main_window import YouTubeAnalyzerMainWindow

def create_test_video_data():
    """Crée des données de test avec tous les champs de métadonnées."""
    return [
        {
            'title': 'Tutoriel Python - Les bases de la POO',
            'channel_title': 'CodeAcademy FR',
            'view_count': 125000,
            'like_count': 3500,
            'comment_count': 245,
            'duration': 'PT15M30S',
            'published_at': '2024-01-15T10:30:00Z',
            'tags': ['python', 'programmation', 'tutoriel', 'POO', 'débutant'],
            'description': 'Dans ce tutoriel, nous allons explorer les concepts fondamentaux de la programmation orientée objet en Python. Vous apprendrez à créer des classes, des objets, et à comprendre l\'héritage.',
            'category_id': '27',
            'language': 'fr',
            'definition': 'hd',
            'caption': 'true',
            'privacy_status': 'public',
            'license': 'youtube',
            'licensed_content': True,
            'dimension': '2d',
            'projection': 'rectangular',
            'embeddable': True,
            'public_stats_viewable': True,
            'topic_categories': [
                'https://en.wikipedia.org/wiki/Technology',
                'https://en.wikipedia.org/wiki/Computer_programming',
                'https://en.wikipedia.org/wiki/Software_engineering'
            ],
            'default_audio_language': 'fr',
            'live_broadcast_content': 'none',
            'location_description': 'Paris, France',
            'recording_date': '2024-01-10T14:00:00Z'
        },
        {
            'title': 'Live Stream - Q&A Développement Web',
            'channel_title': 'WebDev Masters',
            'view_count': 8500,
            'like_count': 420,
            'comment_count': 89,
            'duration': 'PT1H45M12S',
            'published_at': '2024-01-20T19:00:00Z',
            'tags': ['web', 'développement', 'live', 'Q&A', 'javascript'],
            'description': 'Session live de questions-réponses sur le développement web moderne. Nous aborderons React, Node.js, et les meilleures pratiques.',
            'category_id': '28',
            'language': 'fr',
            'definition': 'hd',
            'caption': 'false',
            'privacy_status': 'public',
            'license': 'creativeCommon',
            'licensed_content': False,
            'dimension': '2d',
            'projection': 'rectangular',
            'embeddable': True,
            'public_stats_viewable': True,
            'topic_categories': [
                'https://en.wikipedia.org/wiki/Web_development',
                'https://en.wikipedia.org/wiki/JavaScript'
            ],
            'default_audio_language': 'fr',
            'live_broadcast_content': 'live',
            'location_description': 'Lyon, France',
            'recording_date': '2024-01-20T19:00:00Z'
        },
        {
            'title': 'Vidéo 360° - Visite virtuelle du Louvre',
            'channel_title': 'Culture VR',
            'view_count': 45000,
            'like_count': 1200,
            'comment_count': 156,
            'duration': 'PT25M45S',
            'published_at': '2024-01-18T16:20:00Z',
            'tags': ['360', 'VR', 'Louvre', 'culture', 'visite virtuelle'],
            'description': 'Découvrez le musée du Louvre comme jamais auparavant avec cette visite virtuelle en 360°. Explorez les œuvres les plus célèbres du monde.',
            'category_id': '19',
            'language': 'fr',
            'definition': 'hd',
            'caption': 'true',
            'privacy_status': 'public',
            'license': 'youtube',
            'licensed_content': True,
            'dimension': '3d',
            'projection': '360',
            'embeddable': False,
            'public_stats_viewable': True,
            'topic_categories': [
                'https://en.wikipedia.org/wiki/Art',
                'https://en.wikipedia.org/wiki/Museum',
                'https://en.wikipedia.org/wiki/Virtual_reality'
            ],
            'default_audio_language': 'fr',
            'live_broadcast_content': 'none',
            'location_description': 'Musée du Louvre, Paris',
            'recording_date': '2024-01-15T10:00:00Z'
        }
    ]

def main():
    """Fonction principale pour tester l'interface."""
    app = QApplication(sys.argv)
    
    # Créer la fenêtre principale
    window = YouTubeAnalyzerMainWindow()
    
    # Charger les données de test
    test_data = create_test_video_data()
    window.display_video_data(test_data)
    
    # Afficher la fenêtre
    window.show()
    
    print("Interface lancée avec des données de test.")
    print("Fonctionnalités à tester:")
    print("- Scrolling horizontal pour voir toutes les colonnes")
    print("- Redimensionnement des colonnes")
    print("- Réorganisation des colonnes par glisser-déposer")
    print("- Menu contextuel (clic droit sur l'en-tête)")
    print("- Masquer/afficher des colonnes")
    print("- Auto-redimensionnement des colonnes")
    print("- Tooltips sur les cellules tronquées")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()