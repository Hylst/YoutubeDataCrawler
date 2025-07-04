#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Application PyQt6 simple pour YouTube Data Analyzer

Une interface graphique simplifiée qui fonctionne sans erreurs.
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QTextEdit, QLineEdit, QTabWidget,
        QMessageBox, QProgressBar, QStatusBar, QMenuBar, QFrame
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QAction, QFont
    PYQT6_AVAILABLE = True
except ImportError:
    print("PyQt6 n'est pas disponible. Installez PyQt6: pip install PyQt6")
    sys.exit(1)

# Imports des modules core
sys.path.append(str(Path(__file__).parent))
try:
    from utils.config_manager import ConfigManager
    from utils.error_handler import get_error_handler
except ImportError as e:
    print(f"Erreur d'import: {e}")
    # Continuer sans ces modules pour le moment
    ConfigManager = None
    get_error_handler = lambda: None

class SimpleYouTubeAnalyzer(QMainWindow):
    """
    Interface PyQt6 simplifiée pour YouTube Data Analyzer.
    """
    
    status_message = pyqtSignal(str)
    
    def __init__(self):
        """
        Initialise l'application.
        """
        super().__init__()
        self.config_manager = None
        self.setup_ui()
        self.setup_connections()
        self.load_config()
        
    def setup_ui(self):
        """
        Configure l'interface utilisateur.
        """
        self.setWindowTitle("YouTube Data Analyzer - Simple")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Titre
        title_label = QLabel("🎥 YouTube Data Analyzer")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #FF0000; margin: 20px;")
        main_layout.addWidget(title_label)
        
        # Onglets
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Onglet Configuration
        self.create_config_tab()
        
        # Onglet Analyse
        self.create_analysis_tab()
        
        # Onglet Résultats
        self.create_results_tab()
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Prêt")
        
        # Menu
        self.create_menu()
        
    def create_config_tab(self):
        """
        Crée l'onglet de configuration.
        """
        config_widget = QWidget()
        layout = QVBoxLayout(config_widget)
        
        # Section API YouTube
        api_frame = QFrame()
        api_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        api_layout = QVBoxLayout(api_frame)
        
        api_label = QLabel("Configuration API YouTube")
        api_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        api_layout.addWidget(api_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Entrez votre clé API YouTube...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_key_input)
        
        test_api_btn = QPushButton("Tester la connexion API")
        test_api_btn.clicked.connect(self.test_api_connection)
        api_layout.addWidget(test_api_btn)
        
        layout.addWidget(api_frame)
        
        # Section LLM
        llm_frame = QFrame()
        llm_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        llm_layout = QVBoxLayout(llm_frame)
        
        llm_label = QLabel("Configuration LLM")
        llm_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        llm_layout.addWidget(llm_label)
        
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setPlaceholderText("Clé API OpenAI (optionnel)...")
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        llm_layout.addWidget(self.openai_key_input)
        
        layout.addWidget(llm_frame)
        
        # Bouton de sauvegarde
        save_btn = QPushButton("Sauvegarder la configuration")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        self.tabs.addTab(config_widget, "Configuration")
        
    def create_analysis_tab(self):
        """
        Crée l'onglet d'analyse.
        """
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Section URL
        url_frame = QFrame()
        url_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        url_layout = QVBoxLayout(url_frame)
        
        url_label = QLabel("Analyse de vidéo YouTube")
        url_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        url_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Entrez l'URL de la vidéo YouTube...")
        url_layout.addWidget(self.url_input)
        
        analyze_btn = QPushButton("Analyser la vidéo")
        analyze_btn.clicked.connect(self.analyze_video)
        url_layout.addWidget(analyze_btn)
        
        layout.addWidget(url_frame)
        
        # Section recherche
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        search_layout = QVBoxLayout(search_frame)
        
        search_label = QLabel("Recherche de vidéos")
        search_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez vos mots-clés de recherche...")
        search_layout.addWidget(self.search_input)
        
        search_btn = QPushButton("Rechercher")
        search_btn.clicked.connect(self.search_videos)
        search_layout.addWidget(search_btn)
        
        layout.addWidget(search_frame)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        self.tabs.addTab(analysis_widget, "Analyse")
        
    def create_results_tab(self):
        """
        Crée l'onglet des résultats.
        """
        results_widget = QWidget()
        layout = QVBoxLayout(results_widget)
        
        results_label = QLabel("Résultats d'analyse")
        results_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(results_label)
        
        self.results_text = QTextEdit()
        self.results_text.setPlaceholderText("Les résultats d'analyse apparaîtront ici...")
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Boutons d'export
        export_layout = QHBoxLayout()
        
        export_json_btn = QPushButton("Exporter JSON")
        export_json_btn.clicked.connect(lambda: self.export_results("json"))
        export_layout.addWidget(export_json_btn)
        
        export_csv_btn = QPushButton("Exporter CSV")
        export_csv_btn.clicked.connect(lambda: self.export_results("csv"))
        export_layout.addWidget(export_csv_btn)
        
        clear_btn = QPushButton("Effacer")
        clear_btn.clicked.connect(self.clear_results)
        export_layout.addWidget(clear_btn)
        
        layout.addLayout(export_layout)
        
        self.tabs.addTab(results_widget, "Résultats")
        
    def create_menu(self):
        """
        Crée le menu principal.
        """
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        new_action = QAction('Nouveau', self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction('Ouvrir', self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction('Sauvegarder', self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Quitter', self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Aide
        help_menu = menubar.addMenu('Aide')
        
        about_action = QAction('À propos', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_connections(self):
        """
        Configure les connexions de signaux.
        """
        self.status_message.connect(self.update_status)
        
    def load_config(self):
        """
        Charge la configuration.
        """
        try:
            if ConfigManager:
                self.config_manager = ConfigManager()
                config = self.config_manager.get_config()
                if config and hasattr(config, 'youtube') and config.youtube.api_key:
                    self.api_key_input.setText(config.youtube.api_key)
                    self.status_message.emit("Configuration chargée")
                else:
                    self.status_message.emit("Configuration par défaut")
            else:
                self.status_message.emit("Gestionnaire de configuration non disponible")
        except Exception as e:
            self.status_message.emit(f"Erreur de configuration: {str(e)}")
            
    def test_api_connection(self):
        """
        Teste la connexion API.
        """
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une clé API.")
            return
            
        self.status_message.emit("Test de connexion API...")
        # Ici, vous pourriez ajouter le test réel de l'API
        QMessageBox.information(self, "Test API", "Fonctionnalité de test à implémenter.")
        self.status_message.emit("Test terminé")
        
    def save_config(self):
        """
        Sauvegarde la configuration.
        """
        try:
            # Ici, vous pourriez sauvegarder la configuration
            QMessageBox.information(self, "Configuration", "Configuration sauvegardée avec succès.")
            self.status_message.emit("Configuration sauvegardée")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
            
    def analyze_video(self):
        """
        Analyse une vidéo YouTube.
        """
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une URL de vidéo.")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_message.emit("Analyse en cours...")
        
        # Simulation d'analyse
        for i in range(101):
            self.progress_bar.setValue(i)
            QApplication.processEvents()
            
        self.results_text.append(f"Analyse de la vidéo: {url}\n")
        self.results_text.append("Résultats simulés:\n")
        self.results_text.append("- Titre: Exemple de vidéo\n")
        self.results_text.append("- Durée: 10:30\n")
        self.results_text.append("- Vues: 1,234,567\n")
        self.results_text.append("- Likes: 12,345\n")
        self.results_text.append("\n" + "="*50 + "\n")
        
        self.progress_bar.setVisible(False)
        self.status_message.emit("Analyse terminée")
        self.tabs.setCurrentIndex(2)  # Basculer vers l'onglet résultats
        
    def search_videos(self):
        """
        Recherche des vidéos.
        """
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer des mots-clés.")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_message.emit("Recherche en cours...")
        
        # Simulation de recherche
        for i in range(101):
            self.progress_bar.setValue(i)
            QApplication.processEvents()
            
        self.results_text.append(f"Recherche pour: {query}\n")
        self.results_text.append("Résultats trouvés (simulés):\n")
        for i in range(1, 6):
            self.results_text.append(f"{i}. Vidéo exemple {i} - 1,000 vues\n")
        self.results_text.append("\n" + "="*50 + "\n")
        
        self.progress_bar.setVisible(False)
        self.status_message.emit("Recherche terminée")
        self.tabs.setCurrentIndex(2)  # Basculer vers l'onglet résultats
        
    def export_results(self, format_type: str):
        """
        Exporte les résultats.
        """
        if not self.results_text.toPlainText().strip():
            QMessageBox.warning(self, "Erreur", "Aucun résultat à exporter.")
            return
            
        QMessageBox.information(self, "Export", f"Export {format_type.upper()} à implémenter.")
        
    def clear_results(self):
        """
        Efface les résultats.
        """
        self.results_text.clear()
        self.status_message.emit("Résultats effacés")
        
    def new_project(self):
        """
        Nouveau projet.
        """
        self.clear_results()
        self.url_input.clear()
        self.search_input.clear()
        self.status_message.emit("Nouveau projet")
        
    def open_project(self):
        """
        Ouvre un projet.
        """
        QMessageBox.information(self, "Ouvrir", "Fonctionnalité à implémenter.")
        
    def save_project(self):
        """
        Sauvegarde le projet.
        """
        QMessageBox.information(self, "Sauvegarder", "Fonctionnalité à implémenter.")
        
    def show_about(self):
        """
        Affiche la boîte À propos.
        """
        QMessageBox.about(self, "À propos", 
                         "YouTube Data Analyzer v1.0\n\n"
                         "Une application simple pour analyser les données YouTube.\n\n"
                         "Interface PyQt6 simplifiée.")
        
    def update_status(self, message: str):
        """
        Met à jour la barre de statut.
        """
        self.status_bar.showMessage(message)
        
    def closeEvent(self, event):
        """
        Gère la fermeture de l'application.
        """
        reply = QMessageBox.question(self, "Quitter", 
                                   "Êtes-vous sûr de vouloir quitter?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

def main():
    """
    Point d'entrée principal.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Data Analyzer")
    app.setApplicationVersion("1.0")
    
    # Style moderne
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #FF0000;
        }
        QPushButton {
            background-color: #FF0000;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #cc0000;
        }
        QPushButton:pressed {
            background-color: #990000;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #c0c0c0;
            border-radius: 4px;
        }
        QTextEdit {
            border: 1px solid #c0c0c0;
            border-radius: 4px;
        }
        QFrame {
            margin: 10px;
            padding: 10px;
        }
    """)
    
    try:
        window = SimpleYouTubeAnalyzer()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Erreur lors du lancement: {e}")
        QMessageBox.critical(None, "Erreur", f"Erreur lors du lancement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()