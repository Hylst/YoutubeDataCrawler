#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
YouTube Data Analyzer - Application principale

Application modulaire pour l'analyse de contenu YouTube
avec génération IA et export multi-formats.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Configuration du répertoire de travail
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

# Import application modules
try:
    from utils.config_manager import ConfigManager
    from utils.error_handler import get_error_handler, create_user_friendly_message
    from utils.dependency_checker import DependencyChecker
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)

# Initialize error handler
error_handler = get_error_handler()

# Initialize configuration manager
try:
    config_manager = ConfigManager()
    config = config_manager.load_config()
    
    if config:
        print("✅ Configuration loaded successfully.")
        config_summary = config_manager.get_config_summary()
        
        # Display configuration status
        for category, status in config_summary.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {category.replace('_', ' ').title()}: {'Configured' if status else 'Not Configured'}")
    else:
        print("⚠️ Warning: Configuration could not be loaded properly.")
        print("Some features may not work correctly.")
except Exception as e:
    error_msg = create_user_friendly_message(e)
    print(f"❌ Configuration error: {error_msg}")
    config = None

# Configuration du logging
def setup_logging(log_level: str = "INFO"):
    """
    Configure le système de logging.
    
    Args:
        log_level (str): Niveau de logging
    """
    # Création du répertoire de logs
    log_dir = project_root / 'data' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration du logging
    log_file = log_dir / 'youtube_analyzer.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# Import des modules du projet
from database.db_init import initialize_database


def setup_project_structure():
    """
    Crée la structure de répertoires du projet.
    """
    directories = [
        'data/export',
        'data/thumbnails', 
        'data/logs',
        'data/backups',
        'assets/ui_icons',
        'ui/panels'
    ]
    
    logger = logging.getLogger(__name__)
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Répertoire créé/vérifié: {dir_path}")


def check_environment():
    """
    Vérifie la configuration de l'environnement.
    
    Returns:
        bool: True si l'environnement est correctement configuré
    """
    logger = logging.getLogger(__name__)
    
    # Vérification du fichier .env
    env_file = project_root / '.env'
    env_example = project_root / 'data' / '.env.example'
    
    if not env_file.exists():
        if env_example.exists():
            logger.warning(f"Fichier .env manquant. Copiez {env_example} vers {env_file} et configurez vos clés API.")
        else:
            logger.warning("Fichier .env manquant. Créez-le avec vos clés API.")
        return False
    
    # Chargement des variables d'environnement
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        # Vérification de la clé YouTube (obligatoire)
        youtube_key = os.getenv('YOUTUBE_API_KEY')
        if not youtube_key or youtube_key == 'your_youtube_api_key_here':
            logger.warning("Clé API YouTube non configurée dans le fichier .env")
            return False
        
        logger.info("Configuration de l'environnement validée")
        return True
        
    except ImportError:
        logger.warning("Module python-dotenv non installé. Installez-le avec: pip install python-dotenv")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'environnement: {str(e)}")
        return False


def launch_pyqt6_interface():
    """
    Lance l'interface PyQt6.
    """
    logger = logging.getLogger(__name__)
    
    try:
        from ui.main_window import main as pyqt6_main
        logger.info("Lancement de l'interface PyQt6")
        pyqt6_main()
    except ImportError as e:
        logger.error(f"PyQt6 non disponible: {str(e)}")
        logger.info("Installez PyQt6 avec: pip install PyQt6")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du lancement de PyQt6: {str(e)}")
        return False
    
    return True


def launch_streamlit_interface():
    """
    Lance l'interface Streamlit.
    """
    logger = logging.getLogger(__name__)
    
    try:
        import streamlit as st
        import subprocess
        
        logger.info("Lancement de l'interface Streamlit")
        
        # Lancement de Streamlit
        streamlit_app = project_root / 'ui' / 'streamlit_app.py'
        if not streamlit_app.exists():
            logger.error("Fichier streamlit_app.py non trouvé")
            return False
        
        # Commande Streamlit
        cmd = [sys.executable, '-m', 'streamlit', 'run', str(streamlit_app)]
        subprocess.run(cmd)
        
    except ImportError:
        logger.error("Streamlit non disponible")
        logger.info("Installez Streamlit avec: pip install streamlit")
        return False
    except Exception as e:
        logger.error(f"Erreur lors du lancement de Streamlit: {str(e)}")
        return False
    
    return True


def launch_cli_interface():
    """
    Lance l'interface en ligne de commande.
    """
    logger = logging.getLogger(__name__)
    
    print("\n" + "="*60)
    print("YouTube Data Analyzer - Interface CLI")
    print("="*60)
    
    try:
        from core.youtube_api import YouTubeAPI
        from core.llm_api import LLMManager
        from database.db_init import get_db_connection
        
        # Initialisation des composants
        youtube_api = YouTubeAPI()
        llm_manager = LLMManager()
        db = get_db_connection()
        
        print("\nComposants initialisés:")
        print(f"✓ API YouTube: {'Configurée' if youtube_api.api_key else 'Non configurée'}")
        print(f"✓ Base de données: {'Connectée' if db else 'Erreur'}")
        print(f"✓ Gestionnaire LLM: Initialisé")
        
        # Menu interactif simple
        while True:
            print("\n" + "-"*40)
            print("Options disponibles:")
            print("1. Analyser une URL YouTube")
            print("2. Lister les vidéos en base")
            print("3. Générer du contenu IA")
            print("4. Exporter des données")
            print("5. Tester les APIs")
            print("0. Quitter")
            
            choice = input("\nVotre choix: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                url = input("URL YouTube: ").strip()
                if url:
                    print(f"Analyse de: {url}")
                    # TODO: Implémenter l'analyse
                    print("Fonctionnalité à implémenter")
            elif choice == '2':
                print("Liste des vidéos en base:")
                # TODO: Implémenter la liste
                print("Fonctionnalité à implémenter")
            elif choice == '3':
                print("Génération de contenu IA:")
                # TODO: Implémenter la génération
                print("Fonctionnalité à implémenter")
            elif choice == '4':
                print("Export de données:")
                # TODO: Implémenter l'export
                print("Fonctionnalité à implémenter")
            elif choice == '5':
                print("Test des APIs:")
                # Test YouTube API
                if youtube_api.test_api_key():
                    print("✓ API YouTube: OK")
                else:
                    print("✗ API YouTube: Erreur")
                
                # Test LLM
                available_providers = llm_manager.get_available_providers()
                print(f"✓ Providers LLM disponibles: {', '.join(available_providers)}")
            else:
                print("Option invalide")
        
        print("\nAu revoir!")
        
    except Exception as e:
        logger.error(f"Erreur dans l'interface CLI: {str(e)}")
        return False
    
    return True


def show_status():
    """
    Affiche le statut de l'application.
    """
    print("\n" + "="*60)
    print("YouTube Data Analyzer - Statut")
    print("="*60)
    
    # Vérification de la structure
    print("\nStructure du projet:")
    required_dirs = ['data', 'core', 'ui', 'database']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        status = "✓" if dir_path.exists() else "✗"
        print(f"  {status} {dir_name}/")
    
    # Vérification de la base de données
    db_path = project_root / 'data' / 'youtube_analyzer.db'
    db_status = "✓" if db_path.exists() else "✗"
    print(f"\nBase de données:")
    print(f"  {db_status} {db_path}")
    
    # Vérification de la configuration
    env_path = project_root / 'data' / '.env'
    env_status = "✓" if env_path.exists() else "✗"
    print(f"\nConfiguration:")
    print(f"  {env_status} {env_path}")
    
    # Vérification des dépendances
    print(f"\nDépendances:")
    dependencies = [
        ('PyQt6', 'PyQt6'),
        ('Streamlit', 'streamlit'),
        ('YouTube API', 'google-api-python-client'),
        ('Reconnaissance vocale', 'speech_recognition'),
        ('Variables d\'environnement', 'python-dotenv')
    ]
    
    for name, module in dependencies:
        try:
            __import__(module.replace('-', '_'))
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} (pip install {module})")


def main():
    """
    Point d'entrée principal de l'application.
    """
    # Analyse des arguments de ligne de commande
    parser = argparse.ArgumentParser(
        description="YouTube Data Analyzer - Application d'analyse de contenu YouTube"
    )
    parser.add_argument(
        '--interface', '-i',
        choices=['pyqt6', 'streamlit', 'cli', 'auto'],
        default='auto',
        help="Type d'interface à lancer (défaut: auto)"
    )
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Niveau de logging (défaut: INFO)"
    )
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help="Afficher le statut de l'application"
    )
    parser.add_argument(
        '--setup', 
        action='store_true',
        help="Configurer l'application (structure + base de données)"
    )
    
    args = parser.parse_args()
    
    # Configuration du logging
    logger = setup_logging(args.log_level)
    
    try:
        logger.info("Démarrage de YouTube Data Analyzer v1.0")
        
        # Affichage du statut si demandé
        if args.status:
            show_status()
            return
        
        # Configuration de la structure du projet
        setup_project_structure()
        
        # Initialisation de la base de données
        db_path = project_root / 'data' / 'youtube_analyzer.db'
        initialize_database(str(db_path))
        logger.info(f"Base de données initialisée: {db_path}")
        
        # Configuration uniquement si demandé
        if args.setup:
            print("\n" + "="*50)
            print("Configuration de YouTube Data Analyzer")
            print("="*50)
            print(f"\nStructure créée dans: {project_root}")
            print(f"Base de données: {db_path}")
            print("\nProchaines étapes:")
            print("1. Copiez data/.env.example vers data/.env")
            print("2. Configurez vos clés API dans data/.env")
            print("3. Lancez l'application: python main.py")
            return
        
        # Vérification de l'environnement
        env_ok = check_environment()
        if not env_ok:
            logger.warning("Configuration incomplète. Utilisez --setup pour configurer.")
        
        # Lancement de l'interface
        interface_launched = False
        
        if args.interface == 'auto':
            # Tentative PyQt6 en premier, puis Streamlit, puis CLI
            if launch_pyqt6_interface():
                interface_launched = True
            elif launch_streamlit_interface():
                interface_launched = True
            else:
                interface_launched = launch_cli_interface()
        
        elif args.interface == 'pyqt6':
            interface_launched = launch_pyqt6_interface()
        
        elif args.interface == 'streamlit':
            interface_launched = launch_streamlit_interface()
        
        elif args.interface == 'cli':
            interface_launched = launch_cli_interface()
        
        if not interface_launched:
            logger.error("Impossible de lancer une interface utilisateur")
            logger.info("Utilisez --status pour vérifier la configuration")
            sys.exit(1)
        
        logger.info("Application fermée normalement")
        
    except KeyboardInterrupt:
        logger.info("Application interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()