# Documentation des Presets d'Analyse YouTube

Cette documentation décrit les trois presets d'analyse disponibles dans l'application YouTube Data Analyzer, chacun offrant un niveau différent d'extraction d'informations.

## Vue d'ensemble

L'application propose maintenant trois presets d'analyse prédéfinis qui permettent d'extraire différents niveaux d'informations des vidéos YouTube :

1. **Informations de base** - Données essentielles
2. **Analyse complète avec statistiques** - Données détaillées avec métriques
3. **Analyse technique avancée** - Toutes les métadonnées disponibles

## Preset 1: Informations de base

### Description
Ce preset extrait les informations essentielles d'une vidéo YouTube : nom, auteur, descriptif et thumbnail.

### Champs extraits
- `title` - Titre de la vidéo
- `channel_title` - Nom de la chaîne
- `description` - Description de la vidéo
- `thumbnail_url` - URL de la miniature
- `published_at` - Date de publication
- `duration` - Durée de la vidéo

### Utilisation recommandée
- Analyse rapide de contenu
- Aperçu général des vidéos
- Export léger de données
- Première approche d'analyse

### Configuration
- **Modèle LLM** : GPT-3.5 Turbo
- **Modèle d'image** : Stable Diffusion
- **Format d'export** : JSON
- **Template UI** : Basic
- **Informations étendues** : Non

## Preset 2: Analyse complète avec statistiques

### Description
Ce preset fournit une analyse détaillée incluant les statistiques de performance et les métadonnées importantes.

### Champs extraits
#### Informations de base
- `title` - Titre de la vidéo
- `channel_title` - Nom de la chaîne
- `description` - Description de la vidéo
- `thumbnail_url` - URL de la miniature
- `published_at` - Date de publication
- `duration` - Durée de la vidéo

#### Statistiques de performance
- `view_count` - Nombre de vues
- `like_count` - Nombre de likes
- `comment_count` - Nombre de commentaires

#### Métadonnées
- `tags` - Mots-clés de la vidéo
- `category_id` - Catégorie YouTube
- `language` - Langue de la vidéo
- `definition` - Qualité vidéo (HD/SD)
- `caption` - Disponibilité des sous-titres
- `privacy_status` - Statut de confidentialité
- `topic_categories` - Catégories thématiques
- `default_audio_language` - Langue audio par défaut

### Utilisation recommandée
- Analyse de performance de contenu
- Recherche de tendances
- Analyse concurrentielle
- Rapports détaillés

### Configuration
- **Modèle LLM** : Claude-3 Sonnet
- **Modèle d'image** : Stable Diffusion
- **Format d'export** : XLSX
- **Template UI** : Detailed
- **Informations étendues** : Oui

## Preset 3: Analyse technique avancée

### Description
Ce preset extrait toutes les métadonnées techniques disponibles via l'API YouTube, incluant les détails de streaming en direct et d'enregistrement.

### Champs extraits
#### Toutes les informations des presets précédents, plus :

#### Métadonnées techniques
- `licensed_content` - Contenu sous licence
- `dimension` - Dimension vidéo (2D/3D)
- `projection` - Type de projection (rectangulaire/360°)
- `upload_status` - Statut d'upload
- `license` - Type de licence (YouTube/Creative Commons)
- `embeddable` - Possibilité d'intégration
- `public_stats_viewable` - Visibilité des statistiques publiques
- `relevant_topic_ids` - IDs des sujets pertinents
- `live_broadcast_content` - Type de contenu en direct

#### Miniatures étendues
- `thumbnails_standard` - Miniature standard
- `thumbnails_maxres` - Miniature haute résolution

#### Détails de streaming en direct
- `actual_start_time` - Heure de début réelle
- `actual_end_time` - Heure de fin réelle
- `scheduled_start_time` - Heure de début programmée
- `concurrent_viewers` - Spectateurs simultanés

#### Détails d'enregistrement
- `recording_date` - Date d'enregistrement
- `location_description` - Description du lieu

### Utilisation recommandée
- Analyse technique approfondie
- Recherche académique
- Audit de contenu complet
- Analyse de métadonnées avancée
- Développement d'outils spécialisés

### Configuration
- **Modèle LLM** : GPT-4
- **Modèle d'image** : Midjourney API
- **Format d'export** : JSON
- **Template UI** : Advanced
- **Informations étendues** : Oui

## Utilisation dans l'interface

### Sélection du preset
1. Cliquez sur "Analyser URL" dans l'interface principale
2. Entrez l'URL YouTube de la vidéo
3. Sélectionnez le preset souhaité dans la liste déroulante "Niveau d'analyse"
4. Lisez la description du preset pour confirmer votre choix
5. Cliquez sur "Analyser"

### Résultats
Les données extraites seront affichées dans l'interface selon le template UI configuré pour le preset :
- **Basic** : Affichage simplifié avec les champs essentiels
- **Detailed** : Affichage complet avec toutes les métadonnées
- **Advanced** : Affichage technique avec tous les détails disponibles

## Personnalisation

Les presets peuvent être modifiés dans le fichier `database/db_init.py` :

```python
# Exemple de modification d'un preset
{
    'name': 'Mon preset personnalisé',
    'description': 'Description de mon preset',
    'content_type': 'video',
    'filters': '{
        "extended_info": true,
        "fields": ["title", "description", "view_count"]
    }',
    'llm_model': 'gpt-4',
    'image_model': 'stable-diffusion',
    'export_format': 'json',
    'ui_template': 'detailed',
    'is_default': 0
}
```

## Considérations de performance

- **Preset 1** : Rapide, consommation API minimale
- **Preset 2** : Modéré, bon équilibre performance/informations
- **Preset 3** : Plus lent, consommation API maximale mais informations complètes

## Limites de l'API YouTube

Certains champs peuvent ne pas être disponibles selon :
- Le type de vidéo (normale, en direct, première)
- Les paramètres de confidentialité de la chaîne
- Les restrictions géographiques
- Les limitations de l'API YouTube Data v3

## Évolutions futures

- Ajout de presets spécialisés (gaming, éducation, musique)
- Personnalisation avancée des champs
- Presets pour chaînes et playlists
- Intégration avec d'autres APIs (Twitter, TikTok)