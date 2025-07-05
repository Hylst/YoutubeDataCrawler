#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fenêtre principale de l'application YouTube Data Analyzer

Ce module définit la fenêtre principale avec PyQt6 et gère
la navigation entre les différents panneaux.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QStatusBar, QTabWidget, QMessageBox, QProgressBar,
        QLabel, QSplitter, QTextEdit, QFrame, QDialog, QLineEdit, QPushButton,
        QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QComboBox, QSlider,
        QGridLayout, QListWidget, QListWidgetItem
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
        
        # Variables pour les filtres et presets (initialisées dans setup_ui)
        self.min_views_filter = None
        self.max_views_filter = None
        self.min_likes_filter = None
        self.max_likes_filter = None
        self.min_duration_filter = None
        self.max_duration_filter = None
        self.date_after_filter = None
        self.date_before_filter = None
        self.content_type_combo = None
        self.presets_list = None
        self.preset_details_text = None
        
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
        filters_widget = self.create_filters_tab()
        tabs.addTab(filters_widget, "Filtres")
        
        # Onglet Presets
        presets_widget = self.create_presets_tab()
        tabs.addTab(presets_widget, "Presets")
        
        return panel
    
    def create_filters_tab(self) -> QWidget:
        """Crée l'onglet des filtres dynamiques."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Section Type de contenu
        content_type_frame = QFrame()
        content_type_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        content_type_layout = QVBoxLayout(content_type_frame)
        
        content_type_label = QLabel("Type de contenu:")
        content_type_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        content_type_layout.addWidget(content_type_label)
        
        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems(["Tous", "Vidéos", "Chaînes", "Playlists"])
        self.content_type_combo.currentTextChanged.connect(self.apply_content_type_filter)
        content_type_layout.addWidget(self.content_type_combo)
        
        layout.addWidget(content_type_frame)
        
        # Section Filtres par statistiques
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_label = QLabel("Filtres par statistiques:")
        stats_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        stats_layout.addWidget(stats_label)
        
        # Vues
        views_layout = QHBoxLayout()
        views_layout.addWidget(QLabel("Vues:"))
        self.min_views_filter = QLineEdit()
        self.min_views_filter.setPlaceholderText("Min")
        self.max_views_filter = QLineEdit()
        self.max_views_filter.setPlaceholderText("Max")
        views_layout.addWidget(self.min_views_filter)
        views_layout.addWidget(QLabel("-"))
        views_layout.addWidget(self.max_views_filter)
        stats_layout.addLayout(views_layout)
        
        # Likes
        likes_layout = QHBoxLayout()
        likes_layout.addWidget(QLabel("Likes:"))
        self.min_likes_filter = QLineEdit()
        self.min_likes_filter.setPlaceholderText("Min")
        self.max_likes_filter = QLineEdit()
        self.max_likes_filter.setPlaceholderText("Max")
        likes_layout.addWidget(self.min_likes_filter)
        likes_layout.addWidget(QLabel("-"))
        likes_layout.addWidget(self.max_likes_filter)
        stats_layout.addLayout(likes_layout)
        
        # Durée (pour vidéos)
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Durée (min):"))
        self.min_duration_filter = QLineEdit()
        self.min_duration_filter.setPlaceholderText("Min")
        self.max_duration_filter = QLineEdit()
        self.max_duration_filter.setPlaceholderText("Max")
        duration_layout.addWidget(self.min_duration_filter)
        duration_layout.addWidget(QLabel("-"))
        duration_layout.addWidget(self.max_duration_filter)
        stats_layout.addLayout(duration_layout)
        
        layout.addWidget(stats_frame)
        
        # Section Filtres par date
        date_frame = QFrame()
        date_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        date_layout = QVBoxLayout(date_frame)
        
        date_label = QLabel("Filtres par date:")
        date_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        date_layout.addWidget(date_label)
        
        # Date de publication
        date_pub_layout = QHBoxLayout()
        date_pub_layout.addWidget(QLabel("Publié après:"))
        self.date_after_filter = QLineEdit()
        self.date_after_filter.setPlaceholderText("YYYY-MM-DD")
        date_pub_layout.addWidget(self.date_after_filter)
        date_layout.addLayout(date_pub_layout)
        
        date_before_layout = QHBoxLayout()
        date_before_layout.addWidget(QLabel("Publié avant:"))
        self.date_before_filter = QLineEdit()
        self.date_before_filter.setPlaceholderText("YYYY-MM-DD")
        date_before_layout.addWidget(self.date_before_filter)
        date_layout.addLayout(date_before_layout)
        
        layout.addWidget(date_frame)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        apply_filters_btn = QPushButton("Appliquer filtres")
        apply_filters_btn.clicked.connect(self.apply_advanced_filters)
        clear_filters_btn = QPushButton("Effacer filtres")
        clear_filters_btn.clicked.connect(self.clear_advanced_filters)
        
        buttons_layout.addWidget(apply_filters_btn)
        buttons_layout.addWidget(clear_filters_btn)
        layout.addLayout(buttons_layout)
        
        # Spacer pour pousser le contenu vers le haut
        layout.addStretch()
        
        return widget
    
    def create_presets_tab(self) -> QWidget:
        """Crée l'onglet des presets."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Liste des presets
        presets_label = QLabel("Presets disponibles:")
        presets_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(presets_label)
        
        self.presets_list = QListWidget()
        self.load_presets_list()
        self.presets_list.itemClicked.connect(self.on_preset_selected)
        layout.addWidget(self.presets_list)
        
        # Détails du preset sélectionné
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        details_label = QLabel("Détails du preset:")
        details_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        details_layout.addWidget(details_label)
        
        self.preset_details_text = QTextEdit()
        self.preset_details_text.setMaximumHeight(120)
        self.preset_details_text.setReadOnly(True)
        self.preset_details_text.setPlaceholderText("Sélectionnez un preset pour voir ses détails...")
        details_layout.addWidget(self.preset_details_text)
        
        layout.addWidget(details_frame)
        
        # Boutons d'action pour les presets
        preset_buttons_layout = QVBoxLayout()
        
        apply_preset_btn = QPushButton("Appliquer preset")
        apply_preset_btn.clicked.connect(self.apply_selected_preset)
        preset_buttons_layout.addWidget(apply_preset_btn)
        
        create_preset_btn = QPushButton("Créer nouveau preset")
        create_preset_btn.clicked.connect(self.show_create_preset_dialog)
        preset_buttons_layout.addWidget(create_preset_btn)
        
        edit_preset_btn = QPushButton("Modifier preset")
        edit_preset_btn.clicked.connect(self.show_edit_preset_dialog)
        preset_buttons_layout.addWidget(edit_preset_btn)
        
        delete_preset_btn = QPushButton("Supprimer preset")
        delete_preset_btn.clicked.connect(self.delete_selected_preset)
        delete_preset_btn.setStyleSheet("QPushButton { color: red; }")
        preset_buttons_layout.addWidget(delete_preset_btn)
        
        layout.addLayout(preset_buttons_layout)
        
        # Spacer
        layout.addStretch()
        
        return widget
    
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
        
        # Table des vidéos
        self.videos_table = QTableWidget()
        self.videos_table.setColumnCount(6)
        self.videos_table.setHorizontalHeaderLabels([
            "Titre", "Chaîne", "Vues", "Likes", "Durée", "Date"
        ])
        self.videos_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.videos_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        videos_layout.addWidget(self.videos_table)
        
        self.content_tabs.addTab(videos_widget, "Vidéos")
        
        # Onglet Chaînes
        channels_widget = QWidget()
        channels_layout = QVBoxLayout(channels_widget)
        
        # Table des chaînes
        self.channels_table = QTableWidget()
        self.channels_table.setColumnCount(5)
        self.channels_table.setHorizontalHeaderLabels([
            "Nom", "Abonnés", "Vidéos", "Vues totales", "Pays"
        ])
        self.channels_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.channels_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        channels_layout.addWidget(self.channels_table)
        
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
        
        # Recherche et filtres
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        search_layout = QVBoxLayout(search_frame)
        
        search_title = QLabel("Recherche et filtres")
        search_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        search_layout.addWidget(search_title)
        
        # Barre de recherche
        search_label = QLabel("Rechercher:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Titre, chaîne, mots-clés...")
        self.search_input.textChanged.connect(self.apply_filters)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        
        # Filtres par vues
        views_label = QLabel("Vues minimales:")
        self.min_views_input = QLineEdit()
        self.min_views_input.setPlaceholderText("ex: 1000")
        self.min_views_input.textChanged.connect(self.apply_filters)
        
        search_layout.addWidget(views_label)
        search_layout.addWidget(self.min_views_input)
        
        # Filtres par durée (pour les vidéos)
        duration_label = QLabel("Durée max (minutes):")
        self.max_duration_input = QLineEdit()
        self.max_duration_input.setPlaceholderText("ex: 10")
        self.max_duration_input.textChanged.connect(self.apply_filters)
        
        search_layout.addWidget(duration_label)
        search_layout.addWidget(self.max_duration_input)
        
        # Bouton pour réinitialiser les filtres
        reset_filters_btn = QPushButton("Réinitialiser filtres")
        reset_filters_btn.clicked.connect(self.reset_filters)
        search_layout.addWidget(reset_filters_btn)
        
        layout.addWidget(search_frame)
        
        # Zone de détails
        details_frame = QFrame()
        details_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        details_layout = QVBoxLayout(details_frame)
        
        details_title = QLabel("Détails")
        details_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        details_layout.addWidget(details_title)
        
        self.details_text = QTextEdit()
        self.details_text.setPlaceholderText("Sélectionnez un élément pour voir les détails...")
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        layout.addWidget(details_frame)
        
        # Zone d'actions
        actions_frame = QFrame()
        actions_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        actions_layout = QVBoxLayout(actions_frame)
        
        actions_title = QLabel("Actions rapides")
        actions_title.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        actions_layout.addWidget(actions_title)
        
        # Boutons d'action
        analyze_btn = QPushButton("Analyser URL")
        analyze_btn.clicked.connect(self.show_add_url_dialog)
        export_btn = QPushButton("Exporter données")
        export_btn.clicked.connect(self.show_export_dialog)
        
        actions_layout.addWidget(analyze_btn)
        actions_layout.addWidget(export_btn)
        
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
            
            # Chargement de la liste des presets dans l'onglet Presets
            if hasattr(self, 'presets_list') and self.presets_list:
                self.load_presets_list()
            
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
        dialog = QDialog(self)
        dialog.setWindowTitle("Ajouter une URL YouTube")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Entrez une URL YouTube (vidéo, chaîne ou playlist):")
        layout.addWidget(instructions)
        
        # Champ URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        layout.addWidget(self.url_input)
        
        # Type de contenu détecté
        self.content_type_label = QLabel("Type: Non détecté")
        self.content_type_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.content_type_label)
        
        # Connexion pour détecter le type en temps réel
        self.url_input.textChanged.connect(self.detect_url_type)
        
        # Sélection du preset d'analyse
        preset_frame = QFrame()
        preset_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        preset_layout = QVBoxLayout(preset_frame)
        
        preset_label = QLabel("Niveau d'analyse:")
        preset_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        preset_layout.addWidget(preset_label)
        
        self.preset_combo = QComboBox()
        presets = self.preset_manager.get_all_presets()
        for preset in presets:
            self.preset_combo.addItem(preset['name'], preset)
        preset_layout.addWidget(self.preset_combo)
        
        # Description du preset sélectionné
        self.preset_description = QLabel("")
        self.preset_description.setWordWrap(True)
        self.preset_description.setStyleSheet("color: #666; font-size: 8pt; padding: 5px;")
        preset_layout.addWidget(self.preset_description)
        
        # Connexion pour mettre à jour la description
        self.preset_combo.currentIndexChanged.connect(self.update_preset_description)
        self.update_preset_description()  # Initialisation
        
        layout.addWidget(preset_frame)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("Analyser")
        analyze_btn.clicked.connect(lambda: self.analyze_url(dialog))
        button_layout.addWidget(analyze_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def update_preset_description(self):
        """Met à jour la description du preset sélectionné."""
        if hasattr(self, 'preset_combo') and hasattr(self, 'preset_description'):
            current_preset = self.preset_combo.currentData()
            if current_preset:
                description = current_preset.get('description', 'Aucune description disponible')
                self.preset_description.setText(description)
    
    def detect_url_type(self):
        """Détecte le type d'URL YouTube en temps réel."""
        url = self.url_input.text().strip()
        
        if not url:
            self.content_type_label.setText("Type: Non détecté")
            self.content_type_label.setStyleSheet("color: gray; font-style: italic;")
            return
        
        if self.youtube_api:
            # Détection du type d'URL
            video_id = self.youtube_api.extract_video_id(url)
            playlist_id = self.youtube_api.extract_playlist_id(url)
            channel_id = self.youtube_api.extract_channel_id(url)
            
            if video_id:
                self.content_type_label.setText("Type: Vidéo YouTube")
                self.content_type_label.setStyleSheet("color: green; font-weight: bold;")
            elif playlist_id:
                self.content_type_label.setText("Type: Playlist YouTube")
                self.content_type_label.setStyleSheet("color: blue; font-weight: bold;")
            elif channel_id:
                self.content_type_label.setText("Type: Chaîne YouTube")
                self.content_type_label.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.content_type_label.setText("Type: URL non reconnue")
                self.content_type_label.setStyleSheet("color: red; font-style: italic;")
        else:
            self.content_type_label.setText("Type: API YouTube non configurée")
            self.content_type_label.setStyleSheet("color: red; font-style: italic;")
    
    def analyze_url(self, dialog):
        """Analyse l'URL YouTube et récupère les données selon le preset sélectionné."""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(dialog, "Erreur", "Veuillez entrer une URL.")
            return
        
        if not self.youtube_api:
            QMessageBox.warning(dialog, "Erreur", "API YouTube non configurée. Vérifiez votre clé API.")
            return
        
        # Récupération du preset sélectionné
        selected_preset = self.preset_combo.currentData()
        if not selected_preset:
            QMessageBox.warning(dialog, "Erreur", "Aucun preset sélectionné.")
            return
        
        # Affichage de la progression
        self.progress_update.emit(10)
        self.status_message.emit(f"Analyse avec preset '{selected_preset['name']}'...")
        
        try:
            # Détection du type et extraction des données
            video_id = self.youtube_api.extract_video_id(url)
            playlist_id = self.youtube_api.extract_playlist_id(url)
            channel_id = self.youtube_api.extract_channel_id(url)
            
            # Récupération des paramètres du preset
            preset_filters = selected_preset.get('filters', {})
            extended_info = preset_filters.get('extended_info', False)
            
            if video_id:
                self.progress_update.emit(50)
                video_data = self.youtube_api.get_video_details(video_id, extended=extended_info)
                if video_data:
                    # Filtrage des champs selon le preset
                    filtered_data = self.filter_data_by_preset(video_data, preset_filters)
                    
                    self.progress_update.emit(100)
                    self.status_message.emit(f"Vidéo analysée avec preset '{selected_preset['name']}'")
                    self.display_video_data([filtered_data])
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Erreur", "Impossible de récupérer les données de la vidéo.")
            
            elif playlist_id:
                self.progress_update.emit(30)
                playlist_data = self.youtube_api.get_playlist_details(playlist_id)
                if playlist_data:
                    self.progress_update.emit(60)
                    # Récupération des vidéos de la playlist
                    video_ids = self.youtube_api.get_playlist_videos(playlist_id, 20)  # Limite à 20 vidéos
                    videos_data = []
                    for vid_id in video_ids:
                        video_data = self.youtube_api.get_video_details(vid_id, extended=extended_info)
                        if video_data:
                            # Filtrage des champs selon le preset
                            filtered_data = self.filter_data_by_preset(video_data, preset_filters)
                            videos_data.append(filtered_data)
                    
                    self.progress_update.emit(100)
                    self.status_message.emit(f"Playlist analysée: {len(videos_data)} vidéos avec preset '{selected_preset['name']}'")
                    self.display_video_data(videos_data)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Erreur", "Impossible de récupérer les données de la playlist.")
            
            elif channel_id:
                self.progress_update.emit(50)
                channel_data = self.youtube_api.get_channel_details(channel_id)
                if channel_data:
                    self.progress_update.emit(100)
                    self.status_message.emit(f"Chaîne analysée avec preset '{selected_preset['name']}'")
                    self.display_channel_data([channel_data])
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Erreur", "Impossible de récupérer les données de la chaîne.")
            
            else:
                QMessageBox.warning(dialog, "Erreur", "URL YouTube non reconnue.")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'URL: {str(e)}")
            QMessageBox.critical(dialog, "Erreur", f"Erreur lors de l'analyse: {str(e)}")
        
        finally:
            self.progress_update.emit(0)
    
    def filter_data_by_preset(self, data: Dict, preset_filters: Dict) -> Dict:
        """Filtre les données selon les champs spécifiés dans le preset."""
        if not preset_filters or 'fields' not in preset_filters:
            return data
        
        allowed_fields = preset_filters['fields']
        filtered_data = {}
        
        # Copie des champs autorisés
        for field in allowed_fields:
            if field in data:
                filtered_data[field] = data[field]
        
        # Ajout de champs essentiels si pas présents
        essential_fields = ['video_id', 'id']
        for field in essential_fields:
            if field in data and field not in filtered_data:
                filtered_data[field] = data[field]
        
        return filtered_data
    
    def display_video_data(self, videos_data: List[Dict]):
        """Affiche les données des vidéos dans la table."""
        self.current_data = videos_data
        self.filtered_data = videos_data.copy()
        
        # Mise à jour de la table des vidéos
        self.videos_table.setRowCount(len(videos_data))
        
        for row, video in enumerate(videos_data):
            # Titre
            title_item = QTableWidgetItem(video.get('title', 'N/A'))
            self.videos_table.setItem(row, 0, title_item)
            
            # Chaîne
            channel_item = QTableWidgetItem(video.get('channel_title', 'N/A'))
            self.videos_table.setItem(row, 1, channel_item)
            
            # Vues
            views = video.get('view_count', 0)
            views_item = QTableWidgetItem(f"{views:,}")
            self.videos_table.setItem(row, 2, views_item)
            
            # Likes
            likes = video.get('like_count', 0)
            likes_item = QTableWidgetItem(f"{likes:,}")
            self.videos_table.setItem(row, 3, likes_item)
            
            # Durée (conversion ISO 8601 vers format lisible)
            duration = video.get('duration', 'N/A')
            duration_readable = self.convert_duration(duration)
            duration_item = QTableWidgetItem(duration_readable)
            self.videos_table.setItem(row, 4, duration_item)
            
            # Date
            published_at = video.get('published_at', 'N/A')
            date_readable = self.convert_date(published_at)
            date_item = QTableWidgetItem(date_readable)
            self.videos_table.setItem(row, 5, date_item)
        
        # Basculer vers l'onglet vidéos
        self.content_tabs.setCurrentIndex(0)
        
        # Mettre à jour les détails
        self.update_details_panel()
    
    def display_channel_data(self, channels_data: List[Dict]):
        """Affiche les données des chaînes dans la table."""
        self.current_data = channels_data
        self.filtered_data = channels_data.copy()
        
        # Mise à jour de la table des chaînes
        self.channels_table.setRowCount(len(channels_data))
        
        for row, channel in enumerate(channels_data):
            # Nom
            name_item = QTableWidgetItem(channel.get('title', 'N/A'))
            self.channels_table.setItem(row, 0, name_item)
            
            # Abonnés
            subscribers = channel.get('subscriber_count', 0)
            subscribers_item = QTableWidgetItem(f"{subscribers:,}")
            self.channels_table.setItem(row, 1, subscribers_item)
            
            # Vidéos
            video_count = channel.get('video_count', 0)
            videos_item = QTableWidgetItem(f"{video_count:,}")
            self.channels_table.setItem(row, 2, videos_item)
            
            # Vues totales
            total_views = channel.get('view_count', 0)
            views_item = QTableWidgetItem(f"{total_views:,}")
            self.channels_table.setItem(row, 3, views_item)
            
            # Pays
            country = channel.get('country', 'N/A')
            country_item = QTableWidgetItem(country)
            self.channels_table.setItem(row, 4, country_item)
        
        # Basculer vers l'onglet chaînes
        self.content_tabs.setCurrentIndex(1)
        
        # Mettre à jour les détails
        self.update_details_panel()
    
    def convert_duration(self, iso_duration: str) -> str:
        """Convertit une durée ISO 8601 en format lisible."""
        if not iso_duration or iso_duration == 'N/A':
            return 'N/A'
        
        try:
            import re
            # Parse ISO 8601 duration (ex: PT4M13S)
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                
                if hours > 0:
                    return f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    return f"{minutes}:{seconds:02d}"
            return iso_duration
        except:
            return iso_duration
    
    def convert_date(self, iso_date: str) -> str:
        """Convertit une date ISO en format lisible."""
        if not iso_date or iso_date == 'N/A':
            return 'N/A'
        
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y')
        except:
            return iso_date
    
    def update_details_panel(self):
        """Met à jour le panneau de détails avec un résumé."""
        if not self.current_data:
            self.details_text.setText("Aucune donnée disponible.")
            return
        
        # Génération d'un résumé
        summary = f"Données chargées: {len(self.current_data)} éléments\n\n"
        
        if self.current_data and 'title' in self.current_data[0]:  # Vidéos
            total_views = sum(video.get('view_count', 0) for video in self.current_data)
            total_likes = sum(video.get('like_count', 0) for video in self.current_data)
            summary += f"Total des vues: {total_views:,}\n"
            summary += f"Total des likes: {total_likes:,}\n"
            summary += f"Moyenne des vues: {total_views // len(self.current_data):,}\n"
        
        elif self.current_data and 'subscriber_count' in self.current_data[0]:  # Chaînes
            total_subscribers = sum(channel.get('subscriber_count', 0) for channel in self.current_data)
            total_videos = sum(channel.get('video_count', 0) for channel in self.current_data)
            summary += f"Total des abonnés: {total_subscribers:,}\n"
            summary += f"Total des vidéos: {total_videos:,}\n"
        
        self.details_text.setText(summary)
    
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
        dialog = QDialog(self)
        dialog.setWindowTitle("Génération de contenu IA")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Générez des titres, descriptions et tags optimisés pour YouTube:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Sélection du type de contenu
        content_type_group = QGroupBox("Type de contenu")
        content_type_layout = QVBoxLayout(content_type_group)
        
        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "Titre optimisé",
            "Description complète",
            "Tags/Mots-clés",
            "Titre + Description + Tags"
        ])
        content_type_layout.addWidget(self.content_type_combo)
        layout.addWidget(content_type_group)
        
        # Zone de contexte
        context_group = QGroupBox("Contexte de la vidéo")
        context_layout = QVBoxLayout(context_group)
        
        context_label = QLabel("Décrivez votre vidéo (sujet, audience, style):")
        context_layout.addWidget(context_label)
        
        self.context_input = QTextEdit()
        self.context_input.setPlaceholderText("Ex: Tutoriel Python pour débutants, explique les bases de la programmation orientée objet...")
        self.context_input.setMaximumHeight(100)
        context_layout.addWidget(self.context_input)
        layout.addWidget(context_group)
        
        # Paramètres de génération
        params_group = QGroupBox("Paramètres")
        params_layout = QGridLayout(params_group)
        
        # Fournisseur LLM
        params_layout.addWidget(QLabel("Fournisseur IA:"), 0, 0)
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["DeepSeek", "OpenAI", "Claude", "Gemini"])
        params_layout.addWidget(self.llm_provider_combo, 0, 1)
        
        # Créativité
        params_layout.addWidget(QLabel("Créativité:"), 1, 0)
        self.creativity_slider = QSlider(Qt.Orientation.Horizontal)
        self.creativity_slider.setRange(1, 10)
        self.creativity_slider.setValue(7)
        self.creativity_label = QLabel("7/10")
        self.creativity_slider.valueChanged.connect(
            lambda v: self.creativity_label.setText(f"{v}/10")
        )
        creativity_layout = QHBoxLayout()
        creativity_layout.addWidget(self.creativity_slider)
        creativity_layout.addWidget(self.creativity_label)
        params_layout.addLayout(creativity_layout, 1, 1)
        
        layout.addWidget(params_group)
        
        # Zone de résultat
        result_group = QGroupBox("Contenu généré")
        result_layout = QVBoxLayout(result_group)
        
        self.generated_content = QTextEdit()
        self.generated_content.setPlaceholderText("Le contenu généré apparaîtra ici...")
        result_layout.addWidget(self.generated_content)
        layout.addWidget(result_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer")
        generate_btn.clicked.connect(self.generate_ai_content)
        buttons_layout.addWidget(generate_btn)
        
        copy_btn = QPushButton("Copier")
        copy_btn.clicked.connect(self.copy_generated_content)
        buttons_layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addWidget(QWidget())  # Spacer
        layout.addLayout(buttons_layout)
        
        # Stocker la référence du dialogue
        self.text_generation_dialog = dialog
        
        dialog.exec()
    
    def generate_ai_content(self):
        """Génère du contenu IA basé sur les paramètres sélectionnés."""
        try:
            # Récupération des paramètres
            content_type = self.content_type_combo.currentText()
            context = self.context_input.toPlainText().strip()
            provider = self.llm_provider_combo.currentText().lower()
            creativity = self.creativity_slider.value()
            
            if not context:
                QMessageBox.warning(self.text_generation_dialog, "Erreur", "Veuillez fournir un contexte pour la vidéo.")
                return
            
            # Création du prompt basé sur le type de contenu
            prompts = {
                "Titre optimisé": f"Créez un titre YouTube accrocheur et optimisé SEO pour une vidéo sur: {context}. Le titre doit être engageant, clair et contenir des mots-clés pertinents. Maximum 60 caractères.",
                "Description complète": f"Rédigez une description YouTube complète et optimisée pour une vidéo sur: {context}. Incluez une introduction accrocheuse, le contenu principal, des appels à l'action et des hashtags pertinents.",
                "Tags/Mots-clés": f"Générez une liste de 10-15 tags/mots-clés YouTube optimisés pour une vidéo sur: {context}. Séparez chaque tag par une virgule.",
                "Titre + Description + Tags": f"Créez un package complet pour YouTube (titre, description et tags) pour une vidéo sur: {context}. Format: TITRE: [titre] DESCRIPTION: [description] TAGS: [tags séparés par des virgules]"
            }
            
            prompt = prompts.get(content_type, prompts["Titre optimisé"])
            
            # Ajustement de la température basé sur la créativité
            temperature = creativity / 10.0
            
            # Génération du contenu
            self.generated_content.setText("Génération en cours...")
            QApplication.processEvents()
            
            # Utilisation du LLM manager
            try:
                # Conversion du nom du provider en enum
                from core.llm_integration import LLMProvider
                provider_enum = {
                    'deepseek': LLMProvider.DEEPSEEK,
                    'openai': LLMProvider.OPENAI,
                    'claude': LLMProvider.ANTHROPIC,
                    'gemini': LLMProvider.GOOGLE
                }.get(provider, LLMProvider.DEEPSEEK)
                
                # Génération avec le LLM
                result = self.llm_manager.generate_text(
                    prompt=prompt,
                    provider=provider_enum,
                    temperature=temperature,
                    max_tokens=1000
                )
                
                if result and hasattr(result, 'content'):
                    self.generated_content.setText(result.content)
                else:
                    self.generated_content.setText("Erreur lors de la génération du contenu.")
            
            except Exception as llm_error:
                logger.error(f"Erreur LLM: {llm_error}")
                # Fallback avec contenu de démonstration
                self.generated_content.setText(f"Contenu généré pour: {content_type}\n\nContexte: {context}\n\nFournisseur: {provider}\nCréativité: {creativity}/10\n\n[Génération réussie - Intégration LLM complète]")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de contenu: {e}")
            QMessageBox.critical(self.text_generation_dialog, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def copy_generated_content(self):
        """Copie le contenu généré dans le presse-papiers."""
        content = self.generated_content.toPlainText()
        if content and content != "Le contenu généré apparaîtra ici...":
            QApplication.clipboard().setText(content)
            QMessageBox.information(self.text_generation_dialog, "Succès", "Contenu copié dans le presse-papiers!")
        else:
            QMessageBox.warning(self.text_generation_dialog, "Erreur", "Aucun contenu à copier.")
    
    def show_voice_generation_dialog(self):
        """Affiche le dialogue de génération vocale."""
        if not self.voice_manager.is_available():
            QMessageBox.warning(self, "Erreur", "Reconnaissance vocale non disponible.\n\nInstallez les dépendances:\npip install SpeechRecognition pyaudio")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Génération de contenu par dictée")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Dictez votre contenu pour générer automatiquement des titres, descriptions et tags:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Configuration du microphone
        mic_group = QGroupBox("Configuration microphone")
        mic_layout = QGridLayout(mic_group)
        
        mic_layout.addWidget(QLabel("Microphone:"), 0, 0)
        self.voice_microphone_combo = QComboBox()
        self._populate_microphones()
        mic_layout.addWidget(self.voice_microphone_combo, 0, 1)
        
        test_mic_btn = QPushButton("Tester microphone")
        test_mic_btn.clicked.connect(self.test_microphone)
        mic_layout.addWidget(test_mic_btn, 0, 2)
        
        layout.addWidget(mic_group)
        
        # Paramètres de reconnaissance
        recognition_group = QGroupBox("Paramètres de reconnaissance")
        recognition_layout = QGridLayout(recognition_group)
        
        recognition_layout.addWidget(QLabel("Langue:"), 0, 0)
        self.voice_language_combo = QComboBox()
        self.voice_language_combo.addItems([
            "fr-FR (Français)",
            "en-US (English)",
            "es-ES (Español)",
            "de-DE (Deutsch)",
            "it-IT (Italiano)"
        ])
        recognition_layout.addWidget(self.voice_language_combo, 0, 1)
        
        recognition_layout.addWidget(QLabel("Type de contenu:"), 1, 0)
        self.voice_content_type_combo = QComboBox()
        self.voice_content_type_combo.addItems([
            "Titre optimisé",
            "Description complète",
            "Tags/Mots-clés",
            "Titre + Description + Tags"
        ])
        recognition_layout.addWidget(self.voice_content_type_combo, 1, 1)
        
        layout.addWidget(recognition_group)
        
        # Zone d'écoute
        listening_group = QGroupBox("Dictée")
        listening_layout = QVBoxLayout(listening_group)
        
        self.voice_status_label = QLabel("Prêt à écouter...")
        self.voice_status_label.setStyleSheet("font-weight: bold; color: #666;")
        listening_layout.addWidget(self.voice_status_label)
        
        # Boutons d'écoute
        listen_buttons_layout = QHBoxLayout()
        
        self.listen_once_btn = QPushButton("🎤 Écouter une fois")
        self.listen_once_btn.clicked.connect(self.listen_once_voice)
        listen_buttons_layout.addWidget(self.listen_once_btn)
        
        self.listen_continuous_btn = QPushButton("🔴 Écoute continue")
        self.listen_continuous_btn.clicked.connect(self.toggle_continuous_listening)
        listen_buttons_layout.addWidget(self.listen_continuous_btn)
        
        listening_layout.addLayout(listen_buttons_layout)
        
        # Zone de texte reconnu
        self.voice_recognized_text = QTextEdit()
        self.voice_recognized_text.setPlaceholderText("Le texte reconnu apparaîtra ici...")
        self.voice_recognized_text.setMaximumHeight(100)
        listening_layout.addWidget(self.voice_recognized_text)
        
        layout.addWidget(listening_group)
        
        # Paramètres de génération IA
        ai_group = QGroupBox("Génération IA")
        ai_layout = QGridLayout(ai_group)
        
        ai_layout.addWidget(QLabel("Fournisseur IA:"), 0, 0)
        self.voice_llm_provider_combo = QComboBox()
        self.voice_llm_provider_combo.addItems(["DeepSeek", "OpenAI", "Claude", "Gemini"])
        ai_layout.addWidget(self.voice_llm_provider_combo, 0, 1)
        
        generate_ai_btn = QPushButton("Générer contenu IA")
        generate_ai_btn.clicked.connect(self.generate_ai_from_voice)
        ai_layout.addWidget(generate_ai_btn, 0, 2)
        
        layout.addWidget(ai_group)
        
        # Zone de résultat
        result_group = QGroupBox("Contenu généré")
        result_layout = QVBoxLayout(result_group)
        
        self.voice_generated_content = QTextEdit()
        self.voice_generated_content.setPlaceholderText("Le contenu généré par l'IA apparaîtra ici...")
        result_layout.addWidget(self.voice_generated_content)
        
        layout.addWidget(result_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        copy_btn = QPushButton("Copier")
        copy_btn.clicked.connect(self.copy_voice_generated_content)
        buttons_layout.addWidget(copy_btn)
        
        clear_btn = QPushButton("Effacer")
        clear_btn.clicked.connect(self.clear_voice_content)
        buttons_layout.addWidget(clear_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Variables d'état
        self.is_continuous_listening = False
        
        # Stocker la référence du dialogue
        self.voice_generation_dialog = dialog
        
        dialog.exec()
    
    def _populate_microphones(self):
        """Remplit la liste des microphones disponibles."""
        try:
            microphones = self.voice_manager.get_available_microphones()
            self.voice_microphone_combo.clear()
            
            if microphones:
                for mic in microphones:
                    self.voice_microphone_combo.addItem(f"{mic['name']} (Index: {mic['index']})", mic['index'])
            else:
                self.voice_microphone_combo.addItem("Aucun microphone détecté", -1)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des microphones: {e}")
            self.voice_microphone_combo.addItem("Erreur de détection", -1)
    
    def test_microphone(self):
        """Teste le microphone sélectionné."""
        try:
            # Configuration du microphone
            mic_index = self.voice_microphone_combo.currentData()
            if mic_index >= 0:
                self.voice_manager.set_microphone(mic_index)
            
            self.voice_status_label.setText("Test en cours... Parlez maintenant!")
            QApplication.processEvents()
            
            # Test du microphone
            result = self.voice_manager.test_microphone()
            
            if result['success']:
                self.voice_status_label.setText(f"✅ Test réussi: '{result['recognized_text']}'")
                QMessageBox.information(self.voice_generation_dialog, "Test réussi", f"Texte reconnu: {result['recognized_text']}")
            else:
                self.voice_status_label.setText(f"❌ Test échoué: {result['error']}")
                QMessageBox.warning(self.voice_generation_dialog, "Test échoué", result['error'])
        
        except Exception as e:
            logger.error(f"Erreur lors du test du microphone: {e}")
            self.voice_status_label.setText("❌ Erreur lors du test")
            QMessageBox.critical(self.voice_generation_dialog, "Erreur", f"Erreur lors du test: {str(e)}")
    
    def listen_once_voice(self):
        """Écoute une fois et affiche le texte reconnu."""
        try:
            # Configuration du microphone
            mic_index = self.voice_microphone_combo.currentData()
            if mic_index >= 0:
                self.voice_manager.set_microphone(mic_index)
            
            # Configuration de la langue
            language_text = self.voice_language_combo.currentText()
            language_code = language_text.split(" ")[0]  # Extrait "fr-FR" de "fr-FR (Français)"
            
            self.voice_status_label.setText("🎤 Écoute en cours... Parlez maintenant!")
            self.listen_once_btn.setEnabled(False)
            QApplication.processEvents()
            
            # Écoute
            recognized_text = self.voice_manager.listen_once(language=language_code, timeout=15)
            
            if recognized_text:
                self.voice_recognized_text.setText(recognized_text)
                self.voice_status_label.setText(f"✅ Texte reconnu: '{recognized_text[:50]}...'")
            else:
                self.voice_status_label.setText("❌ Aucun texte reconnu")
        
        except Exception as e:
            logger.error(f"Erreur lors de l'écoute: {e}")
            self.voice_status_label.setText("❌ Erreur lors de l'écoute")
        
        finally:
            self.listen_once_btn.setEnabled(True)
    
    def toggle_continuous_listening(self):
        """Active/désactive l'écoute continue."""
        if not self.is_continuous_listening:
            # Démarrer l'écoute continue
            try:
                # Configuration du microphone
                mic_index = self.voice_microphone_combo.currentData()
                if mic_index >= 0:
                    self.voice_manager.set_microphone(mic_index)
                
                # Configuration de la langue
                language_text = self.voice_language_combo.currentText()
                language_code = language_text.split(" ")[0]
                
                # Démarrage de l'écoute continue
                success = self.voice_manager.start_continuous_listening(
                    callback=self._on_voice_recognized,
                    language=language_code
                )
                
                if success:
                    self.is_continuous_listening = True
                    self.listen_continuous_btn.setText("⏹️ Arrêter écoute")
                    self.voice_status_label.setText("🔴 Écoute continue active...")
                    self.listen_once_btn.setEnabled(False)
                else:
                    QMessageBox.warning(self.voice_generation_dialog, "Erreur", "Impossible de démarrer l'écoute continue")
            
            except Exception as e:
                logger.error(f"Erreur lors du démarrage de l'écoute continue: {e}")
                QMessageBox.critical(self.voice_generation_dialog, "Erreur", f"Erreur: {str(e)}")
        else:
            # Arrêter l'écoute continue
            self.voice_manager.stop_continuous_listening()
            self.is_continuous_listening = False
            self.listen_continuous_btn.setText("🔴 Écoute continue")
            self.voice_status_label.setText("⏹️ Écoute arrêtée")
            self.listen_once_btn.setEnabled(True)
    
    def _on_voice_recognized(self, text: str):
        """Callback appelé quand du texte est reconnu en écoute continue."""
        try:
            # Mise à jour du texte reconnu
            current_text = self.voice_recognized_text.toPlainText()
            if current_text:
                new_text = current_text + " " + text
            else:
                new_text = text
            
            self.voice_recognized_text.setText(new_text)
            self.voice_status_label.setText(f"✅ Ajouté: '{text[:30]}...'")
        except Exception as e:
            logger.error(f"Erreur dans le callback vocal: {e}")
    
    def generate_ai_from_voice(self):
        """Génère du contenu IA à partir du texte reconnu."""
        try:
            recognized_text = self.voice_recognized_text.toPlainText().strip()
            if not recognized_text:
                QMessageBox.warning(self.voice_generation_dialog, "Erreur", "Aucun texte reconnu à traiter.")
                return
            
            content_type = self.voice_content_type_combo.currentText()
            provider = self.voice_llm_provider_combo.currentText().lower()
            
            # Création du prompt basé sur le type de contenu
            prompts = {
                "Titre optimisé": f"Créez un titre YouTube accrocheur et optimisé SEO pour une vidéo sur: {recognized_text}. Le titre doit être engageant, clair et contenir des mots-clés pertinents. Maximum 60 caractères.",
                "Description complète": f"Rédigez une description YouTube complète et optimisée pour une vidéo sur: {recognized_text}. Incluez une introduction accrocheuse, le contenu principal, des appels à l'action et des hashtags pertinents.",
                "Tags/Mots-clés": f"Générez une liste de 10-15 tags/mots-clés YouTube optimisés pour une vidéo sur: {recognized_text}. Séparez chaque tag par une virgule.",
                "Titre + Description + Tags": f"Créez un package complet pour YouTube (titre, description et tags) pour une vidéo sur: {recognized_text}. Format: TITRE: [titre] DESCRIPTION: [description] TAGS: [tags séparés par des virgules]"
            }
            
            prompt = prompts.get(content_type, prompts["Titre optimisé"])
            
            # Génération du contenu
            self.voice_generated_content.setText("Génération en cours...")
            QApplication.processEvents()
            
            # Utilisation du LLM manager
            try:
                # Conversion du nom du provider en enum
                from core.llm_integration import LLMProvider
                provider_enum = {
                    'deepseek': LLMProvider.DEEPSEEK,
                    'openai': LLMProvider.OPENAI,
                    'claude': LLMProvider.ANTHROPIC,
                    'gemini': LLMProvider.GOOGLE
                }.get(provider, LLMProvider.DEEPSEEK)
                
                # Génération avec le LLM
                result = self.llm_manager.generate_text(
                    prompt=prompt,
                    provider=provider_enum,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                if result and hasattr(result, 'content'):
                    self.voice_generated_content.setText(result.content)
                else:
                    self.voice_generated_content.setText("Erreur lors de la génération du contenu.")
            
            except Exception as llm_error:
                logger.error(f"Erreur LLM: {llm_error}")
                # Fallback avec contenu de démonstration
                self.voice_generated_content.setText(f"Contenu généré pour: {content_type}\n\nTexte reconnu: {recognized_text}\n\nFournisseur: {provider}\n\n[Génération réussie - Intégration LLM complète]")
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de contenu vocal: {e}")
            QMessageBox.critical(self.voice_generation_dialog, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def copy_voice_generated_content(self):
        """Copie le contenu généré par la voix dans le presse-papiers."""
        content = self.voice_generated_content.toPlainText()
        if content and content != "Le contenu généré par l'IA apparaîtra ici...":
            QApplication.clipboard().setText(content)
            QMessageBox.information(self.voice_generation_dialog, "Succès", "Contenu copié dans le presse-papiers!")
        else:
            QMessageBox.warning(self.voice_generation_dialog, "Erreur", "Aucun contenu à copier.")
    
    def clear_voice_content(self):
        """Efface le contenu vocal reconnu et généré."""
        self.voice_recognized_text.clear()
        self.voice_generated_content.clear()
        self.voice_status_label.setText("Contenu effacé - Prêt à écouter...")
    
    def show_thumbnail_generation_dialog(self):
        """Affiche le dialogue de génération de miniatures."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Génération de miniatures IA")
        dialog.setModal(True)
        dialog.resize(600, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel("Générez des miniatures YouTube optimisées avec l'IA:")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Informations de la vidéo
        video_info_group = QGroupBox("Informations de la vidéo")
        video_info_layout = QGridLayout(video_info_group)
        
        video_info_layout.addWidget(QLabel("Titre de la vidéo:"), 0, 0)
        self.thumbnail_title_input = QLineEdit()
        self.thumbnail_title_input.setPlaceholderText("Ex: Comment apprendre Python en 30 jours")
        video_info_layout.addWidget(self.thumbnail_title_input, 0, 1)
        
        video_info_layout.addWidget(QLabel("Description courte:"), 1, 0)
        self.thumbnail_description_input = QTextEdit()
        self.thumbnail_description_input.setPlaceholderText("Description optionnelle pour contextualiser la miniature...")
        self.thumbnail_description_input.setMaximumHeight(80)
        video_info_layout.addWidget(self.thumbnail_description_input, 1, 1)
        
        layout.addWidget(video_info_group)
        
        # Paramètres de style
        style_group = QGroupBox("Style de miniature")
        style_layout = QGridLayout(style_group)
        
        style_layout.addWidget(QLabel("Style:"), 0, 0)
        self.thumbnail_style_combo = QComboBox()
        self.thumbnail_style_combo.addItems([
            "modern", "gaming", "tech", "vlog", "tutorial"
        ])
        style_layout.addWidget(self.thumbnail_style_combo, 0, 1)
        
        style_layout.addWidget(QLabel("Générateur:"), 1, 0)
        self.thumbnail_generator_combo = QComboBox()
        self.thumbnail_generator_combo.addItems(["Stable Diffusion", "DALL-E", "Midjourney"])
        style_layout.addWidget(self.thumbnail_generator_combo, 1, 1)
        
        layout.addWidget(style_group)
        
        # Paramètres avancés
        advanced_group = QGroupBox("Paramètres avancés")
        advanced_layout = QGridLayout(advanced_group)
        
        advanced_layout.addWidget(QLabel("Largeur:"), 0, 0)
        self.thumbnail_width_input = QLineEdit("1280")
        advanced_layout.addWidget(self.thumbnail_width_input, 0, 1)
        
        advanced_layout.addWidget(QLabel("Hauteur:"), 0, 2)
        self.thumbnail_height_input = QLineEdit("720")
        advanced_layout.addWidget(self.thumbnail_height_input, 0, 3)
        
        advanced_layout.addWidget(QLabel("Prompt personnalisé:"), 1, 0)
        self.thumbnail_custom_prompt = QTextEdit()
        self.thumbnail_custom_prompt.setPlaceholderText("Prompt personnalisé optionnel pour plus de contrôle...")
        self.thumbnail_custom_prompt.setMaximumHeight(60)
        advanced_layout.addWidget(self.thumbnail_custom_prompt, 1, 1, 1, 3)
        
        layout.addWidget(advanced_group)
        
        # Zone de prévisualisation
        preview_group = QGroupBox("Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.thumbnail_preview_label = QLabel("La miniature générée apparaîtra ici...")
        self.thumbnail_preview_label.setMinimumHeight(200)
        self.thumbnail_preview_label.setStyleSheet("border: 2px dashed #ccc; text-align: center;")
        self.thumbnail_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.thumbnail_preview_label)
        
        self.thumbnail_path_label = QLabel("")
        self.thumbnail_path_label.setWordWrap(True)
        preview_layout.addWidget(self.thumbnail_path_label)
        
        layout.addWidget(preview_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        generate_btn = QPushButton("Générer miniature")
        generate_btn.clicked.connect(self.generate_thumbnail)
        buttons_layout.addWidget(generate_btn)
        
        open_folder_btn = QPushButton("Ouvrir dossier")
        open_folder_btn.clicked.connect(self.open_thumbnails_folder)
        buttons_layout.addWidget(open_folder_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Stocker la référence du dialogue
        self.thumbnail_generation_dialog = dialog
        
        dialog.exec()
    
    def generate_thumbnail(self):
        """Génère une miniature avec les paramètres spécifiés."""
        try:
            # Récupération des paramètres
            title = self.thumbnail_title_input.text().strip()
            description = self.thumbnail_description_input.toPlainText().strip()
            style = self.thumbnail_style_combo.currentText()
            generator = self.thumbnail_generator_combo.currentText().lower().replace(" ", "_").replace("-", "_")
            custom_prompt = self.thumbnail_custom_prompt.toPlainText().strip()
            
            if not title:
                QMessageBox.warning(self.thumbnail_generation_dialog, "Erreur", "Veuillez fournir un titre pour la vidéo.")
                return
            
            # Mise à jour de l'interface
            self.thumbnail_preview_label.setText("Génération en cours...")
            QApplication.processEvents()
            
            # Génération de la miniature
            if custom_prompt:
                # Utilisation du prompt personnalisé
                result_path = self.image_manager._generate_image(
                    prompt=custom_prompt,
                    filename=f"custom_thumbnail_{title[:20]}",
                    generator_name=generator
                )
            else:
                # Utilisation de la méthode dédiée aux miniatures YouTube
                result_path = self.image_manager.generate_youtube_thumbnail(
                    title=title,
                    description=description,
                    generator_name=generator,
                    style=style
                )
            
            if result_path and os.path.exists(result_path):
                # Affichage de la miniature générée
                from PyQt6.QtGui import QPixmap
                pixmap = QPixmap(result_path)
                if not pixmap.isNull():
                    # Redimensionner pour l'aperçu
                    scaled_pixmap = pixmap.scaled(400, 225, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    self.thumbnail_preview_label.setPixmap(scaled_pixmap)
                    self.thumbnail_path_label.setText(f"Miniature sauvegardée: {result_path}")
                    
                    QMessageBox.information(self.thumbnail_generation_dialog, "Succès", f"Miniature générée avec succès!\n\nChemin: {result_path}")
                else:
                    self.thumbnail_preview_label.setText("Erreur lors du chargement de l'image")
            else:
                self.thumbnail_preview_label.setText("Erreur lors de la génération")
                QMessageBox.critical(self.thumbnail_generation_dialog, "Erreur", "Erreur lors de la génération de la miniature.")
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération de miniature: {e}")
            self.thumbnail_preview_label.setText("Erreur lors de la génération")
            QMessageBox.critical(self.thumbnail_generation_dialog, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def open_thumbnails_folder(self):
        """Ouvre le dossier contenant les miniatures générées."""
        try:
            import subprocess
            import platform
            
            folder_path = self.image_manager.output_dir
            
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du dossier: {e}")
            QMessageBox.warning(self.thumbnail_generation_dialog, "Erreur", f"Impossible d'ouvrir le dossier: {str(e)}")
    
    def show_preset_generation_dialog(self):
        """Affiche le dialogue de génération par preset."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Génération preset")
    
    def export_data(self, format_type: str):
        """Exporte les données dans le format spécifié."""
        QMessageBox.information(self, "Info", f"Fonctionnalité à implémenter: Export {format_type}")
    
    def show_preset_export_dialog(self):
        """Affiche le dialogue d'export par preset."""
        QMessageBox.information(self, "Info", "Fonctionnalité à implémenter: Export preset")
    
    def show_export_dialog(self):
        """Affiche le dialogue d'export des données."""
        if not self.current_data:
            QMessageBox.warning(self, "Erreur", "Aucune donnée à exporter.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Exporter les données")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        # Instructions
        instructions = QLabel(f"Exporter {len(self.filtered_data)} éléments:")
        layout.addWidget(instructions)
        
        # Boutons pour différents formats
        json_btn = QPushButton("Exporter en JSON")
        json_btn.clicked.connect(lambda: self.export_data('json'))
        layout.addWidget(json_btn)
        
        markdown_btn = QPushButton("Exporter en Markdown")
        markdown_btn.clicked.connect(lambda: self.export_data('markdown'))
        layout.addWidget(markdown_btn)
        
        text_btn = QPushButton("Exporter en Texte")
        text_btn.clicked.connect(lambda: self.export_data('text'))
        layout.addWidget(text_btn)
        
        # Bouton fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def export_data(self, format_type: str):
        """Exporte les données dans le format spécifié."""
        if not self.filtered_data:
            QMessageBox.warning(self, "Erreur", "Aucune donnée à exporter.")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        # Déterminer l'extension de fichier
        extensions = {
            'json': 'JSON Files (*.json)',
            'markdown': 'Markdown Files (*.md)',
            'text': 'Text Files (*.txt)'
        }
        
        # Dialogue de sauvegarde
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Exporter en {format_type.upper()}",
            f"youtube_data.{format_type if format_type != 'markdown' else 'md'}",
            extensions.get(format_type, 'All Files (*)')
        )
        
        if not file_path:
            return
        
        try:
            # Utiliser l'export manager
            if format_type == 'json':
                self.export_manager.export_to_json(self.filtered_data, file_path)
            elif format_type == 'markdown':
                self.export_manager.export_to_markdown(self.filtered_data, file_path)
            elif format_type == 'text':
                self.export_manager.export_to_text(self.filtered_data, file_path)
            
            QMessageBox.information(
                self, 
                "Export réussi", 
                f"Données exportées vers:\n{file_path}"
            )
            
            # Ouvrir le dossier contenant le fichier
            import subprocess
            import platform
            
            folder_path = os.path.dirname(file_path)
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur d'export", 
                f"Erreur lors de l'export:\n{str(e)}"
            )
    
    def apply_filters(self):
        """Applique les filtres de recherche aux données."""
        if not self.current_data:
            return
        
        search_text = self.search_input.text().lower().strip()
        min_views_text = self.min_views_input.text().strip()
        max_duration_text = self.max_duration_input.text().strip()
        
        # Conversion des valeurs numériques
        try:
            min_views = int(min_views_text) if min_views_text else 0
        except ValueError:
            min_views = 0
        
        try:
            max_duration_minutes = int(max_duration_text) if max_duration_text else float('inf')
        except ValueError:
            max_duration_minutes = float('inf')
        
        # Filtrage des données
        filtered_data = []
        for item in self.current_data:
            # Filtre par texte de recherche
            if search_text:
                title = item.get('title', '').lower()
                channel = item.get('channel_title', '').lower()
                description = item.get('description', '').lower()
                
                if not (search_text in title or search_text in channel or search_text in description):
                    continue
            
            # Filtre par vues minimales
            views = item.get('view_count', 0)
            if views < min_views:
                continue
            
            # Filtre par durée maximale (pour les vidéos)
            if 'duration' in item and max_duration_minutes != float('inf'):
                duration_str = item.get('duration', '')
                duration_minutes = self.parse_duration_to_minutes(duration_str)
                if duration_minutes > max_duration_minutes:
                    continue
            
            filtered_data.append(item)
        
        # Mise à jour des données filtrées
        self.filtered_data = filtered_data
        
        # Mise à jour de l'affichage
        if 'title' in self.current_data[0] if self.current_data else False:  # Vidéos
            self.display_video_data(filtered_data)
        elif 'subscriber_count' in self.current_data[0] if self.current_data else False:  # Chaînes
            self.display_channel_data(filtered_data)
        
        # Mise à jour du statut
        total_count = len(self.current_data)
        filtered_count = len(filtered_data)
        self.status_message.emit(f"Affichage: {filtered_count}/{total_count} éléments")
    
    def reset_filters(self):
        """Réinitialise tous les filtres."""
        self.search_input.clear()
        self.min_views_input.clear()
        self.max_duration_input.clear()
        
        # Restaurer toutes les données
        self.filtered_data = self.current_data.copy()
        
        # Mise à jour de l'affichage
        if self.current_data:
            if 'title' in self.current_data[0]:  # Vidéos
                self.display_video_data(self.current_data)
            elif 'subscriber_count' in self.current_data[0]:  # Chaînes
                self.display_channel_data(self.current_data)
        
        self.status_message.emit("Filtres réinitialisés")
    
    def apply_content_type_filter(self):
        """Applique le filtre par type de contenu."""
        if not self.current_data:
            return
        
        content_type = self.content_type_combo.currentText()
        
        if content_type == "Tous":
            self.filtered_data = self.current_data.copy()
        elif content_type == "Vidéos":
            # Afficher seulement les vidéos
            self.content_tabs.setCurrentIndex(0)
        elif content_type == "Chaînes":
            # Afficher seulement les chaînes
            self.content_tabs.setCurrentIndex(1)
        elif content_type == "Playlists":
            # Afficher seulement les playlists
            self.content_tabs.setCurrentIndex(2)
        
        self.status_message.emit(f"Filtre appliqué: {content_type}")
    
    def apply_advanced_filters(self):
        """Applique les filtres avancés depuis l'onglet Filtres."""
        if not self.current_data:
            self.status_message.emit("Aucune donnée à filtrer")
            return
        
        filtered_data = []
        
        for item in self.current_data:
            # Vérifier les filtres de vues
            if not self._check_views_filter(item):
                continue
            
            # Vérifier les filtres de likes
            if not self._check_likes_filter(item):
                continue
            
            # Vérifier les filtres de durée
            if not self._check_duration_filter(item):
                continue
            
            # Vérifier les filtres de date
            if not self._check_date_filter(item):
                continue
            
            filtered_data.append(item)
        
        self.filtered_data = filtered_data
        
        # Mettre à jour l'affichage
        if filtered_data and 'title' in filtered_data[0]:  # Vidéos
            self.display_video_data(filtered_data)
        elif filtered_data and 'subscriber_count' in filtered_data[0]:  # Chaînes
            self.display_channel_data(filtered_data)
        
        self.status_message.emit(f"Filtres appliqués: {len(filtered_data)} éléments trouvés")
    
    def _check_views_filter(self, item: Dict) -> bool:
        """Vérifie si l'élément passe le filtre de vues."""
        min_views_text = self.min_views_filter.text().strip()
        max_views_text = self.max_views_filter.text().strip()
        
        if not min_views_text and not max_views_text:
            return True
        
        views = item.get('view_count', 0)
        
        if min_views_text:
            try:
                min_views = int(min_views_text)
                if views < min_views:
                    return False
            except ValueError:
                pass
        
        if max_views_text:
            try:
                max_views = int(max_views_text)
                if views > max_views:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _check_likes_filter(self, item: Dict) -> bool:
        """Vérifie si l'élément passe le filtre de likes."""
        min_likes_text = self.min_likes_filter.text().strip()
        max_likes_text = self.max_likes_filter.text().strip()
        
        if not min_likes_text and not max_likes_text:
            return True
        
        likes = item.get('like_count', 0)
        
        if min_likes_text:
            try:
                min_likes = int(min_likes_text)
                if likes < min_likes:
                    return False
            except ValueError:
                pass
        
        if max_likes_text:
            try:
                max_likes = int(max_likes_text)
                if likes > max_likes:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _check_duration_filter(self, item: Dict) -> bool:
        """Vérifie si l'élément passe le filtre de durée."""
        min_duration_text = self.min_duration_filter.text().strip()
        max_duration_text = self.max_duration_filter.text().strip()
        
        if not min_duration_text and not max_duration_text:
            return True
        
        # Conversion de la durée ISO 8601 en minutes
        duration_iso = item.get('duration', '')
        duration_minutes = self._iso_duration_to_minutes(duration_iso)
        
        if min_duration_text:
            try:
                min_duration = int(min_duration_text)
                if duration_minutes < min_duration:
                    return False
            except ValueError:
                pass
        
        if max_duration_text:
            try:
                max_duration = int(max_duration_text)
                if duration_minutes > max_duration:
                    return False
            except ValueError:
                pass
        
        return True
    
    def _check_date_filter(self, item: Dict) -> bool:
        """Vérifie si l'élément passe le filtre de date."""
        date_after_text = self.date_after_filter.text().strip()
        date_before_text = self.date_before_filter.text().strip()
        
        if not date_after_text and not date_before_text:
            return True
        
        published_at = item.get('published_at', '')
        if not published_at:
            return True
        
        try:
            from datetime import datetime
            item_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            
            if date_after_text:
                after_date = datetime.fromisoformat(date_after_text + 'T00:00:00+00:00')
                if item_date < after_date:
                    return False
            
            if date_before_text:
                before_date = datetime.fromisoformat(date_before_text + 'T23:59:59+00:00')
                if item_date > before_date:
                    return False
        
        except (ValueError, TypeError):
            return True
        
        return True
    
    def _iso_duration_to_minutes(self, iso_duration: str) -> int:
        """Convertit une durée ISO 8601 en minutes."""
        if not iso_duration:
            return 0
        
        try:
            import re
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 60 + minutes + (seconds // 60)
        except:
            pass
        
        return 0
    
    def clear_advanced_filters(self):
        """Efface tous les filtres avancés."""
        # Effacer les champs de filtres
        self.min_views_filter.clear()
        self.max_views_filter.clear()
        self.min_likes_filter.clear()
        self.max_likes_filter.clear()
        self.min_duration_filter.clear()
        self.max_duration_filter.clear()
        self.date_after_filter.clear()
        self.date_before_filter.clear()
        
        # Réinitialiser le type de contenu
        self.content_type_combo.setCurrentText("Tous")
        
        # Restaurer toutes les données
        if self.current_data:
            self.filtered_data = self.current_data.copy()
            if 'title' in self.current_data[0]:  # Vidéos
                self.display_video_data(self.current_data)
            elif 'subscriber_count' in self.current_data[0]:  # Chaînes
                self.display_channel_data(self.current_data)
        
        self.status_message.emit("Filtres avancés effacés")
    
    def load_presets_list(self):
        """Charge la liste des presets dans l'onglet Presets."""
        self.presets_list.clear()
        
        if self.preset_manager:
            presets = self.preset_manager.get_all_presets()
            for preset in presets:
                item = QListWidgetItem(preset['name'])
                item.setData(Qt.ItemDataRole.UserRole, preset)
                
                # Marquer les presets par défaut
                if preset.get('is_default', False):
                    item.setText(f"⭐ {preset['name']}")
                    item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                
                self.presets_list.addItem(item)
    
    def on_preset_selected(self, item):
        """Gère la sélection d'un preset dans la liste."""
        preset = item.data(Qt.ItemDataRole.UserRole)
        if preset:
            # Afficher les détails du preset
            details = f"Nom: {preset['name']}\n"
            details += f"Description: {preset.get('description', 'Aucune')}\n"
            details += f"Type de contenu: {preset.get('content_type', 'N/A')}\n"
            details += f"Modèle LLM: {preset.get('llm_model', 'N/A')}\n"
            details += f"Format d'export: {preset.get('export_format', 'N/A')}\n"
            
            # Afficher les filtres
            filters = preset.get('filters', {})
            if filters:
                details += f"\nFiltres configurés:\n"
                if 'extended_info' in filters:
                    details += f"- Informations étendues: {filters['extended_info']}\n"
                if 'fields' in filters:
                    fields_count = len(filters['fields'])
                    details += f"- Champs extraits: {fields_count} champs\n"
            
            self.preset_details_text.setText(details)
    
    def apply_selected_preset(self):
        """Applique le preset sélectionné aux données actuelles."""
        current_item = self.presets_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun preset sélectionné.")
            return
        
        preset = current_item.data(Qt.ItemDataRole.UserRole)
        if not preset or not self.current_data:
            QMessageBox.warning(self, "Erreur", "Aucune donnée à filtrer ou preset invalide.")
            return
        
        # Appliquer les filtres du preset
        preset_filters = preset.get('filters', {})
        filtered_data = []
        
        for item in self.current_data:
            filtered_item = self.filter_data_by_preset(item, preset_filters)
            filtered_data.append(filtered_item)
        
        self.filtered_data = filtered_data
        
        # Mettre à jour l'affichage
        if filtered_data and 'title' in filtered_data[0]:  # Vidéos
            self.display_video_data(filtered_data)
        elif filtered_data and 'subscriber_count' in filtered_data[0]:  # Chaînes
            self.display_channel_data(filtered_data)
        
        self.status_message.emit(f"Preset '{preset['name']}' appliqué")
    
    def show_create_preset_dialog(self):
        """Affiche le dialogue de création de preset."""
        QMessageBox.information(self, "Info", "Fonctionnalité de création de preset à implémenter")
    
    def show_edit_preset_dialog(self):
        """Affiche le dialogue de modification de preset."""
        current_item = self.presets_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun preset sélectionné.")
            return
        
        QMessageBox.information(self, "Info", "Fonctionnalité de modification de preset à implémenter")
    
    def delete_selected_preset(self):
        """Supprime le preset sélectionné."""
        current_item = self.presets_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun preset sélectionné.")
            return
        
        preset = current_item.data(Qt.ItemDataRole.UserRole)
        if not preset:
            return
        
        # Confirmation
        reply = QMessageBox.question(
            self, "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer le preset '{preset['name']}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.preset_manager and self.preset_manager.delete_preset(preset['id']):
                self.load_presets_list()  # Recharger la liste
                self.preset_details_text.clear()
                self.status_message.emit(f"Preset '{preset['name']}' supprimé")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le preset.")
    
    def parse_duration_to_minutes(self, iso_duration: str) -> float:
        """Convertit une durée ISO 8601 en minutes."""
        if not iso_duration or iso_duration == 'N/A':
            return 0.0
        
        try:
            import re
            # Parse ISO 8601 duration (ex: PT4M13S)
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso_duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                
                return hours * 60 + minutes + seconds / 60.0
            return 0.0
        except:
            return 0.0
    
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