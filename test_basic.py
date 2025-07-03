#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests de base pour YouTube Data Analyzer

Script de test simple pour vérifier le bon fonctionnement
des modules principaux sans dépendances externes.
"""

import sys
import os
from pathlib import Path

# Configuration du path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """
    Teste l'importation des modules principaux.
    """
    print("Test des imports...")
    
    try:
        # Test des modules core
        from core.youtube_api import YouTubeAPI
        print("✓ core.youtube_api")
        
        from core.llm_api import LLMManager
        print("✓ core.llm_api")
        
        from core.imagegen_api import ImageGeneratorManager
        print("✓ core.imagegen_api")
        
        from core.presets import PresetManager
        print("✓ core.presets")
        
        from core.filters import DataFilter
        print("✓ core.filters")
        
        from core.export import ExportManager
        print("✓ core.export")
        
        from core.voice_input import VoiceInputManager
        print("✓ core.voice_input")
        
        # Test des modules database
        from database.db_init import initialize_database, get_db_connection
        print("✓ database.db_init")
        
        return True
        
    except ImportError as e:
        print(f"✗ Erreur d'import: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Erreur: {str(e)}")
        return False

def test_database():
    """
    Teste l'initialisation de la base de données.
    """
    print("\nTest de la base de données...")
    
    try:
        from database.db_init import initialize_database, get_db_connection
        
        # Test avec une base temporaire
        test_db_path = project_root / 'test_temp.db'
        
        # Suppression si existe
        if test_db_path.exists():
            test_db_path.unlink()
        
        # Initialisation
        initialize_database(str(test_db_path))
        print("✓ Initialisation de la base")
        
        # Test de connexion
        conn = get_db_connection(str(test_db_path))
        if conn:
            print("✓ Connexion à la base")
            
            # Test de requête simple
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"✓ Tables créées: {len(tables)}")
            
            conn.close()
        else:
            print("✗ Erreur de connexion")
            return False
        
        # Nettoyage
        if test_db_path.exists():
            test_db_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur base de données: {str(e)}")
        return False

def test_youtube_api():
    """
    Teste l'API YouTube (sans clé).
    """
    print("\nTest de l'API YouTube...")
    
    try:
        from core.youtube_api import YouTubeAPI
        
        # Initialisation sans clé
        api = YouTubeAPI()
        print("✓ Initialisation YouTubeAPI")
        
        # Test d'extraction d'ID
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = api.extract_video_id(video_url)
        if video_id == "dQw4w9WgXcQ":
            print("✓ Extraction d'ID vidéo")
        else:
            print(f"✗ Extraction d'ID vidéo: {video_id}")
            return False
        
        # Test d'extraction d'ID playlist
        playlist_url = "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq1TXTd_"
        playlist_id = api.extract_playlist_id(playlist_url)
        if playlist_id == "PLrAXtmRdnEQy6nuLMHjMZOz59Oq1TXTd_":
            print("✓ Extraction d'ID playlist")
        else:
            print(f"✗ Extraction d'ID playlist: {playlist_id}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur API YouTube: {str(e)}")
        return False

def test_llm_manager():
    """
    Teste le gestionnaire LLM (sans clés).
    """
    print("\nTest du gestionnaire LLM...")
    
    try:
        from core.llm_api import LLMManager
        
        # Initialisation
        manager = LLMManager()
        print("✓ Initialisation LLMManager")
        
        # Test des providers disponibles
        providers = manager.get_available_providers()
        print(f"✓ Providers disponibles: {', '.join(providers)}")
        
        # Test de validation de provider
        if manager.is_provider_available('openai'):
            print("✓ Provider OpenAI reconnu")
        else:
            print("✗ Provider OpenAI non reconnu")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur LLM Manager: {str(e)}")
        return False

def test_voice_input():
    """
    Teste le gestionnaire de reconnaissance vocale.
    """
    print("\nTest de la reconnaissance vocale...")
    
    try:
        from core.voice_input import VoiceInputManager
        
        # Initialisation
        manager = VoiceInputManager()
        print("✓ Initialisation VoiceInputManager")
        
        # Test de disponibilité
        if manager.is_available():
            print("✓ Reconnaissance vocale disponible")
            
            # Test des microphones
            mics = manager.get_available_microphones()
            print(f"✓ Microphones détectés: {len(mics)}")
        else:
            print("⚠ Reconnaissance vocale non disponible (modules manquants)")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur reconnaissance vocale: {str(e)}")
        return False

def test_filters():
    """
    Teste le système de filtres.
    """
    print("\nTest du système de filtres...")
    
    try:
        from core.filters import FilterCriteria, DataFilter
        
        # Test de création de critères
        criteria = FilterCriteria(
            content_type='video',
            min_duration=60,
            max_duration=3600,
            keywords_include=['test']
        )
        print("✓ Création de critères de filtrage")
        
        # Test de validation
        if criteria.content_type == 'video':
            print("✓ Critères valides")
        else:
            print("✗ Critères invalides")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur système de filtres: {str(e)}")
        return False

def test_export():
    """
    Teste le gestionnaire d'export.
    """
    print("\nTest du gestionnaire d'export...")
    
    try:
        from core.export import ExportManager
        from database.db_init import get_db_connection
        
        # Création d'une base temporaire
        test_db_path = project_root / 'test_export.db'
        if test_db_path.exists():
            test_db_path.unlink()
        
        from database.db_init import initialize_database
        initialize_database(str(test_db_path))
        
        conn = get_db_connection(str(test_db_path))
        
        # Initialisation du gestionnaire
        manager = ExportManager(conn)
        print("✓ Initialisation ExportManager")
        
        # Test de génération de contenu vide
        content = manager.generate_content([], 'json', 'video')
        if content:
            print("✓ Génération de contenu JSON")
        else:
            print("✗ Erreur génération de contenu")
            return False
        
        # Nettoyage
        conn.close()
        if test_db_path.exists():
            test_db_path.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur gestionnaire d'export: {str(e)}")
        return False

def test_ui_imports():
    """
    Teste l'importation des modules UI.
    """
    print("\nTest des modules UI...")
    
    try:
        # Test PyQt6 (optionnel)
        try:
            from ui.main_window import YouTubeAnalyzerMainWindow
            print("✓ Interface PyQt6 disponible")
        except ImportError:
            print("⚠ Interface PyQt6 non disponible (PyQt6 non installé)")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur modules UI: {str(e)}")
        return False

def run_all_tests():
    """
    Lance tous les tests.
    """
    print("="*60)
    print("YouTube Data Analyzer - Tests de base")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Base de données", test_database),
        ("API YouTube", test_youtube_api),
        ("Gestionnaire LLM", test_llm_manager),
        ("Reconnaissance vocale", test_voice_input),
        ("Système de filtres", test_filters),
        ("Gestionnaire d'export", test_export),
        ("Modules UI", test_ui_imports)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erreur critique dans {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:<8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont passés!")
        print("\nL'application est prête à être utilisée.")
        print("Prochaines étapes:")
        print("1. Configurez vos clés API dans data/.env")
        print("2. Lancez l'application: python main.py")
    else:
        print("⚠ Certains tests ont échoué.")
        print("Vérifiez les dépendances et la configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)