# YouTube Data Analyzer

## 🎯 Objectif

YouTube Data Analyzer est une application locale et modulaire en Python permettant d'explorer, filtrer et analyser des vidéos, chaînes et playlists YouTube via l'API officielle. L'application offre des fonctionnalités avancées de génération de contenu IA, d'export multi-formats et de gestion de presets personnalisés.

## ✨ Fonctionnalités principales

### 🔍 Analyse de contenu YouTube
- **Extraction via URL ou ID** : vidéos uniques, playlists entières, chaînes complètes
- **Données complètes** : titre, description, durée, statistiques, mots-clés, hashtags, langue, date
- **Stockage local** : toutes les données normalisées dans une base SQLite3
- **Filtres dynamiques** : via presets personnalisés et critères avancés

### 🧠 Génération IA
- **Contenu textuel** : titres YouTube optimisés, descriptions courtes/longues, tags
- **Miniatures** : génération d'images via HuggingFace Flux
- **Entrées multiples** : texte saisi, dictée vocale, ou analyse de vidéos existantes
- **Providers supportés** : OpenAI, Claude, Gemini, DeepSeek, OpenRouter, X/Grok

### 📤 Export multi-formats
- **Formats** : JSON, Markdown, Texte brut, CSV, Export DB complet
- **Templates personnalisables** : Markdown avec regroupement par playlist/chaîne
- **Export par preset** : critères prédéfinis pour exports automatisés

### 🎛️ Gestion des presets
- **Critères multiples** : type de contenu, durée, popularité, mots-clés, dates
- **Modèles IA** : configuration par défaut des LLMs et générateurs d'images
- **Interface graphique** : éditeur intégré pour création/modification

### 🎤 Reconnaissance vocale
- **Dictée de prompts** : génération de contenu par commande vocale
- **Calibrage automatique** : adaptation au bruit ambiant
- **Langues multiples** : français, anglais, et autres langues supportées

## 🏗️ Architecture technique

### Technologies utilisées

| Composant | Technologie |
|-----------|-------------|
| Base de données | SQLite3 |
| Interface | PyQt6 (desktop) / Streamlit (web) |
| API YouTube | YouTube Data API v3 |
| IA texte | APIs LLMs via requests |
| IA image | HuggingFace Spaces |
| Audio | speech_recognition + pyaudio |
| Configuration | .env + SQLite3 |

### Structure du projet

```
youtube_analyzer/
├── main.py                     # Point d'entrée principal
├── ui/
│   ├── main_window.py         # Fenêtre principale PyQt6
│   ├── menu.py                # Gestion des menus
│   └── panels/                # Panneaux spécialisés
│       ├── video_list.py      # Liste des vidéos
│       ├── video_details.py   # Détails d'une vidéo
│       ├── api_settings.py    # Configuration APIs
│       ├── presets_editor.py  # Éditeur de presets
│       ├── generation_panel.py # Génération IA
│       └── export_panel.py    # Panneau d'export
├── core/
│   ├── youtube_api.py         # Interface YouTube API
│   ├── llm_api.py            # Gestionnaire LLMs
│   ├── imagegen_api.py       # Génération d'images
│   ├── presets.py            # Gestion des presets
│   ├── filters.py            # Filtres avancés
│   ├── export.py             # Gestionnaire d'exports
│   └── voice_input.py        # Reconnaissance vocale
├── database/
│   ├── db_init.py            # Initialisation DB
│   └── schema.sql            # Schéma de base
├── data/
│   ├── .env                  # Variables d'environnement
│   ├── export/               # Fichiers exportés
│   └── thumbnails/           # Miniatures générées
├── assets/
│   └── ui_icons/             # Icônes interface
├── requirements.txt          # Dépendances Python
└── README.md                # Documentation
```

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- Clé API YouTube Data v3
- Clés API pour les services IA (optionnel)

### Installation des dépendances

```bash
# Cloner ou télécharger le projet
cd youtube_analyzer

# Installer les dépendances
pip install -r requirements.txt

# Pour la reconnaissance vocale (Windows)
pip install pyaudio

# Pour la reconnaissance vocale (Linux/Mac)
sudo apt-get install portaudio19-dev  # Ubuntu/Debian
brew install portaudio  # macOS
pip install pyaudio
```

### Configuration

1. **Créer le fichier `.env`** dans le dossier `data/` :

```env
# YouTube API
YOUTUBE_API_KEY=votre_cle_youtube_api

# LLM APIs (optionnel)
OPENAI_API_KEY=votre_cle_openai
ANTHROPIC_API_KEY=votre_cle_claude
GOOGLE_API_KEY=votre_cle_gemini
DEEPSEEK_API_KEY=votre_cle_deepseek

# HuggingFace (optionnel)
HUGGINGFACE_API_KEY=votre_cle_huggingface

# Configuration par défaut
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-3.5-turbo
DEFAULT_IMAGE_PROVIDER=huggingface
```

2. **Obtenir une clé API YouTube** :
   - Aller sur [Google Cloud Console](https://console.cloud.google.com/)
   - Créer un nouveau projet ou sélectionner un projet existant
   - Activer l'API YouTube Data v3
   - Créer des identifiants (clé API)
   - Copier la clé dans le fichier `.env`

## 🎮 Utilisation

### Lancement de l'application

```bash
# Interface graphique PyQt6
python main.py

# Interface web Streamlit (alternative)
streamlit run ui/streamlit_app.py
```

### Utilisation de base

1. **Analyser du contenu YouTube** :
   - Menu `Analyser` → `Ajouter URL`
   - Coller l'URL d'une vidéo, playlist ou chaîne
   - Cliquer sur `Lancer analyse`

2. **Filtrer les résultats** :
   - Utiliser le panneau de filtres à gauche
   - Créer des presets personnalisés
   - Appliquer des critères multiples

3. **Générer du contenu IA** :
   - Menu `Générer` → choisir le type de contenu
   - Saisir un prompt ou utiliser la dictée vocale
   - Configurer le modèle IA dans les paramètres

4. **Exporter les données** :
   - Menu `Exporter` → choisir le format
   - Utiliser les presets pour exports automatisés
   - Personnaliser les templates Markdown

### Exemples d'utilisation

#### Analyser une chaîne YouTube complète

```python
from core.youtube_api import YouTubeAPI
from database.db_init import get_db_connection

# Initialisation
api = YouTubeAPI()
db = get_db_connection()

# Analyser une chaîne
channel_url = "https://www.youtube.com/@example"
channel_data = api.get_channel_info_from_url(channel_url)

# Les données sont automatiquement sauvegardées en DB
```

#### Générer du contenu avec IA

```python
from core.llm_api import LLMManager

# Initialisation
llm_manager = LLMManager()

# Générer un titre
title = llm_manager.generate_youtube_title(
    "Tutoriel Python pour débutants",
    provider="openai",
    model="gpt-3.5-turbo"
)

print(f"Titre généré: {title}")
```

#### Utiliser la reconnaissance vocale

```python
from core.voice_input import VoiceInputManager, VoicePromptGenerator

# Initialisation
voice_manager = VoiceInputManager()
prompt_generator = VoicePromptGenerator(voice_manager)

# Générer un prompt par dictée
if voice_manager.is_available():
    prompt = prompt_generator.generate_prompt_from_voice("title", "fr-FR")
    print(f"Prompt généré: {prompt}")
```

## 🔧 Configuration avancée

### Presets personnalisés

Les presets permettent de sauvegarder des configurations complètes :

```python
from core.presets import PresetManager

preset_manager = PresetManager(db_connection)

# Créer un preset
preset_data = {
    'name': 'Vidéos populaires récentes',
    'content_type': 'video',
    'min_views': 10000,
    'max_duration': 600,  # 10 minutes
    'date_after': '2024-01-01',
    'keywords_include': ['tutoriel', 'guide'],
    'default_llm_provider': 'openai',
    'export_format': 'markdown'
}

preset_manager.create_preset(preset_data)
```

### Filtres avancés

```python
from core.filters import DataFilter, FilterCriteria

# Créer des critères de filtrage
criteria = FilterCriteria(
    content_type='video',
    min_duration=60,
    max_duration=1800,
    min_views=1000,
    keywords_include=['python', 'tutorial'],
    date_after='2024-01-01'
)

# Appliquer les filtres
data_filter = DataFilter(db_connection)
filtered_videos = data_filter.apply_filters(criteria)
```

## 📊 Base de données

### Tables principales

- **videos** : Informations complètes des vidéos
- **channels** : Données des chaînes YouTube
- **playlists** : Métadonnées des playlists
- **api_keys** : Gestion sécurisée des clés API
- **presets** : Configurations sauvegardées
- **exports** : Historique des exports

### Sauvegarde et restauration

```bash
# Exporter la base de données
python -c "from core.export import ExportManager; ExportManager().export_database('backup.db')"

# Importer une base de données
cp backup.db data/youtube_analyzer.db
```

## 🧪 Tests

```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=core --cov=ui --cov-report=html

# Tests d'un module spécifique
pytest tests/test_youtube_api.py
```

## 📦 Packaging

### Créer un exécutable

```bash
# Avec PyInstaller
pyinstaller --onefile --windowed main.py

# Avec cx_Freeze
python setup.py build
```

## 🔍 Dépannage

### Problèmes courants

1. **Erreur d'API YouTube** :
   - Vérifier la clé API dans `.env`
   - Contrôler les quotas dans Google Cloud Console
   - Tester avec `Menu Aide` → `Tester connectivité API`

2. **Reconnaissance vocale non fonctionnelle** :
   - Installer `pyaudio` : `pip install pyaudio`
   - Vérifier les permissions du microphone
   - Tester avec `voice_manager.test_microphone()`

3. **Interface graphique ne se lance pas** :
   - Installer PyQt6 : `pip install PyQt6`
   - Utiliser l'alternative Streamlit : `streamlit run ui/streamlit_app.py`

4. **Erreurs de base de données** :
   - Supprimer `data/youtube_analyzer.db` pour réinitialiser
   - Vérifier les permissions d'écriture dans le dossier `data/`

### Logs et débogage

Les logs sont sauvegardés dans `data/logs/` avec rotation automatique :

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :
- Consulter la documentation dans l'application (`Menu Aide`)
- Vérifier les issues GitHub existantes
- Créer une nouvelle issue avec les détails du problème

## 🔮 Roadmap

### Version 1.1
- [ ] Interface web complète avec React
- [ ] Support de plus de providers IA
- [ ] Analyse de sentiment des commentaires
- [ ] Export vers bases de données externes

### Version 1.2
- [ ] Analyse automatique par mots-clés
- [ ] Notifications de nouvelles vidéos
- [ ] Intégration avec d'autres plateformes
- [ ] API REST pour intégrations externes

---

**YouTube Data Analyzer** - Analysez, générez et exportez votre contenu YouTube avec l'IA 🚀