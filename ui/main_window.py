#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application YouTube Data Analyzer

Ce module définit la fenêtre principale avec PyQt6 et gère
la navigation entre les différents panneaux.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QStatusBar, QTabWidget, QMessageBox, QProgressBar,
        QLabel, QSplitter, QTextEdit, QFrame
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
    from PyQt6.QtGui import QAction, QIcon, QFont
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False
    QMainWindow = object
    QApplication = object
    QWidget = object
    pyqtSignal = lambda: None
    QThread = object

# Imports des modules core
sys.path.append(str(Path(__file__).parent.parent))
from core.youtube_api import YouTubeAPI
from core.llm_api import LLMManager
from core.imagegen_api import ImageGeneratorManager
from core.presets import PresetManager
from core.filters import DataFilter
from core.export import ExportManager
from core.voice_input import VoiceInputManager
from database.db_init import get_connection

# Configuration du logging
logger = logging.getLogger(__name__)


class YouTubeAnalyzerMainWindow(QMainWindow):
    """
    Fenêtre principale de l'application YouTube Data Analyzer.
    """
    
    # Signaux
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self):
        """
        Initialise la fenêtre principale.
        """
        super().__init__()
        
        # Vérification de PyQt6
        if not PYQT6_AVAILABLE:
            raise ImportError("PyQt6 n'est pas disponible. Installez PyQt6 pour utiliser l'interface graphique.")
        
        # Initialisation des gestionnaires
        # Get database path from project root
        from pathlib import Path
        import os
        project_root = Path(__file__).parent.parent
        db_path = project_root / 'data' / 'youtube_analyzer.db'
        self.db_connection = get_connection(str(db_path))
        
        # Get YouTube API key from environment
        youtube_api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.youtube_api = YouTubeAPI(youtube_api_key) if youtube_api_key else None
        self.llm_manager = LLMManager()
        
        # Create output directory for generated images
        images_output_dir = project_root / 'generated_images'
        self.image_manager = ImageGeneratorManager(str(images_output_dir))
        self.preset_manager = PresetManager(self.db_connection)
        self.data_filter = DataFilter()
        
        # Create output directory for exports
        exports_output_dir = project_root / 'exports'
        self.export_manager = ExportManager(str(exports_output_dir), self.db_connection)
        self.voice_manager = VoiceInputManager()
        
        # Variables d'état
        self.current_data = []
        self.filtered_data = []
        self.current_preset = None
        
        # Configuration de l'interface
        self.setup_ui()
        self.setup_connections()
        self.setup_status_bar()
        
        # Chargement initial
        self.load_initial_data()
        
        logger.info("Fenêtre principale initialisée")
    
    def setup_ui(self):
        """
        Configure l'interface utilisateur.
        """
        self.setWindowTitle("YouTube Data Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panneau de gauche (navigation et filtres)
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Panneau central (contenu principal)
        center_panel = self.create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Panneau de droite (détails et actions)
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Proportions du splitter
        main_splitter.setSizes([300, 700, 400])
        
        # Menu bar
        self.create_menu_bar()
    
    def create_menu_bar(self):
        """
        Crée la barre de menu.
        """
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        import_db_action = QAction('Importer base de données', self)
        import_db_action.triggered.connect(self.import_database)
        file_menu.addAction(import_db_action)
        
        export_db_action = QAction('Exporter base de données', self)
        export_db_action.triggered.connect(self.export_database)
        file_menu.addAction(export_db_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Quitter', self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Analyser
        analyze_menu = menubar.addMenu('Analyser')
        
        add_url_action = QAction('Ajouter URL', self)
        add_url_action.triggered.connect(self.show_add_url_dialog)
        analyze_menu.addAction(add_url_action)
        
        start_analysis_action = QAction('Lancer analyse', self)
        start_analysis_action.triggered.connect(self.start_analysis)
        analyze_menu.addAction(start_analysis_action)
        
        analyze_menu.addSeparator()
        
        view_videos_action = QAction('Voir vidéos analysées', self)
        view_videos_action.triggered.connect(self.show_videos_tab)
        analyze_menu.addAction(view_videos_action)
        
        view_channels_action = QAction('Voir chaînes/playlists', self)
        view_channels_action.triggered.connect(self.show_channels_tab)
        analyze_menu.addAction(view_channels_action)
        
        # Menu Générer
        generate_menu = menubar.addMenu('Générer')
        
        generate_text_action = QAction('Titre/description (texte)', self)
        generate_text_action.triggered.connect(self.show_text_generation_dialog)
        generate_menu.addAction(generate_text_action)
        
        generate_voice_action = QAction('Titre/description (dictée)', self)
        generate_voice_action.triggered.connect(self.show_voice_generation_dialog)
        generate_menu.addAction(generate_voice_action)
        
        generate_thumbnail_action = QAction('Miniature', self)
        generate_thumbnail_action.triggered.connect(self.show_thumbnail_generation_dialog)
        generate_menu.addAction(generate_thumbnail_action)
        
        generate_menu.addSeparator()
        
        generate_preset_action = QAction('Génération par preset', self)
        generate_preset_action.triggered.connect(self.show_preset_generation_dialog)
        generate_menu.addAction(generate_preset_action)
        
        # Menu Exporter
        export_menu = menubar.addMenu('Exporter')
        
        export_json_action = QAction('Vers JSON', self)
        export_json_action.triggered.connect(lambda: self.export_data('json'))
        export_menu.addAction(export_json_action)
        
        export_markdown_action = QAction('Vers Markdown', self)
        export_markdown_action.triggered.connect(lambda: self.export_data('markdown'))
        export_menu.addAction(export_markdown_action)
        
        export_text_action = QAction('Vers Texte', self)
        export_text_action.triggered.connect(lambda: self.export_data('text'))
        export_menu.addAction(export_text_action)
        
        export_menu.addSeparator()
        
        export_preset_action = QAction('Export par preset', self)
        export_preset_action.triggered.connect(self.show_preset_export_dialog)
        export_menu.addAction(export_preset_action)
        
        # Menu Paramètres
        settings_menu = menubar.addMenu('Paramètres')
        
        api_keys_action = QAction('Gestion clés API', self)
        api_keys_action.triggered.connect(self.show_api_settings)
        settings_menu.addAction(api_keys_action)
        
        models_action = QAction('Choix des modèles', self)
        models_action.triggered.connect(self.show_model_settings)
        settings_menu.addAction(models_action)
        
        presets_action = QAction('Édition des presets', self)
        presets_action.triggered.connect(self.show_preset_editor)
        settings_menu.addAction(presets_action)
        
        # Menu Aide
        help_menu = menubar.addMenu('Aide')
        
        about_action = QAction('À propos', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        test_api_action = QAction('Tester connectivité API', self)
        test_api_action.triggered.connect(self.test_api_connectivity)
        help_menu.addAction(test_api_action)
    
    def create_left_panel(self) -> QWidget:
        """
        Crée le panneau de gauche (navigation et filtres).
        
        Returns:
            QWidget: Panneau de gauche
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Titre
        title_label = QLabel("Navigation & Filtres")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Onglets pour différentes vues
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Onglet Filtres
        filters_widget = QWidget()
        filters_layout = QVBoxLayout(filters_widget)
        
        # Placeholder pour les filtres
        filters_placeholder = QLabel("Filtres dynamiques\n(à implémenter)")
        filters_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        filters_placeholder.setStyleSheet("color: gray; font-style: italic;")
        filters_layout.addWidget(filters_placeholder)
        
        tabs.addTab(filters_widget, "Filtres")
        
        # Onglet Presets
        presets_widget = QWidget()
        presets_layout = QVBoxLayout(presets_widget)
        
        presets_placeholder = QLabel("Presets sauvegardés\n(à implémenter)")
        presets_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        presets_placeholder.setStyleSheet("color: gray; font-style: italic;")
        presets_layout.addWidget(presets_placeholder)
        
        tabs.addTab(presets_widget, "Presets")
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """
        Crée le panneau central (contenu principal).
        
        Returns:
            QWidget: Panneau central
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Titre
        title_label = QLabel("Contenu Principal")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Onglets pour différents types de contenu
        self.content_tabs = QTabWidget()
        layout.addWidget(self.content_tabs)
        
        # Onglet Vidéos
        videos_widget = QWidget()
        videos_layout = QVBoxLayout(videos_widget)
        
        videos_placeholder = QLabel("Liste des vidéos\n(à implémenter)")
        videos_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        videos_placeholder.setStyleSheet("color: gray; font-style: italic;")
        videos_layout.addWidget(videos_placeholder)
        
        self.content_tabs.addTab(videos_widget, "Vidéos")
        
        # Onglet Chaînes
        channels_widget = QWidget()
        channels_layout = QVBoxLayout(channels_widget)
        
        channels_placeholder = QLabel("Liste des chaînes\n(à implémenter)")
        channels_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channels_placeholder.setStyleSheet("color: gray; font-style: italic;")
        channels_layout.addWidget(channels_placeholder)
        
        self.content_tabs.addTab(channels_widget, "Chaînes")
        
        # Onglet Playlists
        playlists_widget = QWidget()
        playlists_layout = QVBoxLayout(playlists_widget)
        
        playlists_placeholder = QLabel("Liste des playlists\n(à implémenter)")
        playlists_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        playlists_placeholder.setStyleSheet("color: gray; font-style: italic;")
        playlists_layout.addWidget(playlists_placeholder)
        
        self.content_tabs.addTab(playlists_widget, "Playlists")
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """
        Crée le panneau de droite (détails et actions).
        
        Returns:
            QWidget: Panneau de droite
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Titre
        title_label = QLabel("Détails & Actions")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Zone de détails
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        self.details_text = QTextEdit()
        self.details_text.setPlaceholderText("Sélectionnez un élément pour voir les détails...")
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_frame)
        
        # Zone d'actions
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QVBoxLayout(actions_frame)
        
        actions_placeholder = QLabel("Actions rapides\n(à implémenter)")
        actions_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_placeholder.setStyleSheet("color: gray; font-style: italic;")
        actions_layout.addWidget(actions_placeholder)
        
        layout.addWidget(actions_frame)
        
        return panel
    
    def setup_connections(self):
        """
        Configure les connexions de signaux.
        """
        self.status_message.connect(self.show_status_message)
        self.progress_update.connect(self.update_progress)
    
    def setup_status_bar(self):
        """
        Configure la barre de statut.
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Label de statut
        self.status_label = QLabel("Prêt")
        self.status_bar.addWidget(self.status_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Informations de connexion
        self.connection_label = QLabel("DB: Connecté")
        self.status_bar.addPermanentWidget(self.connection_label)
    
    def load_initial_data(self):
        """
        Charge les données initiales.
        """
        try:
            # Vérification de la connexion à la base de données
            if self.db_connection:
                self.connection_label.setText("DB: Connecté")
                self.connection_label.setStyleSheet("color: green;")
            else:
                self.connection_label.setText("DB: Erreur")
                self.connection_label.setStyleSheet("color: red;")
            
            # Chargement des presets
            presets = self.preset_manager.get_all_presets()
            logger.info(f"Chargé {len(presets)} presets")
            
            self.status_message.emit("Application initialisée")
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement initial: {str(e)}")
            self.status_message.emit(f"Erreur: {str(e)}")
    
    @pyqtSlot(str)
    def show_status_message(self, message: str):
        """
        Affiche un message dans la barre de statut.
        
        Args:
            message (str): Message à afficher
        """
        self.status_label.setText(message)
        
        # Auto-effacement après 5 secondes
        QTimer.singleShot(5000, lambda: self.status_label.setText("Prêt"))
    
    @pyqtSlot(int)
    def update_progress(self, value: int):
        """
        Met à jour la barre de progression.
        
        Args:
            value (int): Valeur de progression (0-100)
        """
        if value <= 0:
            self.progress_bar.setVisible(False)
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(value)
            
            if value >= 100:
                QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))
    
    # Méthodes des actions de menu (placeholders)
    def import_database(self):
        """Importe une base de données."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Import DB")
    
    def export_database(self):
        """Exporte la base de données."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Export DB")
    
    def show_add_url_dialog(self):
        """Affiche le dialogue d'ajout d'URL."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Ajout URL")
    
    def start_analysis(self):
        """Lance l'analyse."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Analyse")
    
    def show_videos_tab(self):
        """Affiche l'onglet des vidéos."""
        self.content_tabs.setCurrentIndex(0)
    
    def show_channels_tab(self):
        """Affiche l'onglet des chaînes."""
        self.content_tabs.setCurrentIndex(1)
    
    def show_text_generation_dialog(self):
        """Affiche le dialogue de génération de texte."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Génération texte")
    
    def show_voice_generation_dialog(self):
        """Affiche le dialogue de génération vocale."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Génération vocale")
    
    def show_thumbnail_generation_dialog(self):
        """Affiche le dialogue de génération de miniatures."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Génération miniatures")
    
    def show_preset_generation_dialog(self):
        """Affiche le dialogue de génération par preset."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Génération preset")
    
    def export_data(self, format_type: str):
        """Exporte les données dans le format spécifié."""
        QMessageBox.information(self, "Info", f"Fonctionnalité à implémenter: Export {format_type}")
    
    def show_preset_export_dialog(self):
        """Affiche le dialogue d'export par preset."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Export preset")
    
    def show_api_settings(self):
        """Affiche les paramètres API."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Paramètres API")
    
    def show_model_settings(self):
        """Affiche les paramètres de modèles."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Paramètres modèles")
    
    def show_preset_editor(self):
        """Affiche l'éditeur de presets."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Éditeur presets")
    
    def show_about(self):
        """Affiche la boîte À propos."""
        QMessageBox.about(self, "À propos", 
                         "YouTube Data Analyzer v1.0\n\n"
                         "Application modulaire pour l'analyse de contenu YouTube\n"
                         "avec génération IA et export multi-formats.")
    
    def test_api_connectivity(self):
        """Teste la connectivité des APIs."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Test connectivité")
    
    def closeEvent(self, event):
        """
        Gère la fermeture de l'application.
        
        Args:
            event: Événement de fermeture
        """
        # Arrêt de l'écoute vocale si active
        if self.voice_manager.is_listening:
            self.voice_manager.stop_continuous_listening()
        
        # Fermeture de la connexion à la base de données
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Application fermée")
        event.accept()


def create_application() -> QApplication:
    """
    Crée l'application Qt.
    
    Returns:
        QApplication: Application Qt
    """
    if not PYQT6_AVAILABLE:
        raise ImportError("PyQt6 n'est pas disponible")
    
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Data Analyzer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("YouTube Analyzer")
    
    return app


def main():
    """
    Point d'entrée principal pour l'interface PyQt6.
    """
    try:
        app = create_application()
        
        # Création et affichage de la fenêtre principale
        window = YouTubeAnalyzerMainWindow()
        window.show()
        
        # Lancement de la boucle d'événements
        sys.exit(app.exec())
    
    except ImportError as e:
        print(f"Erreur: {str(e)}")
        print("Installez PyQt6: pip install PyQt6")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erreur lors du lancement de l'application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()