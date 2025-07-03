#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'export des données YouTube

Ce module gère l'export des données dans différents formats :
JSON, Markdown, texte brut, et base de données.
"""

import os
import json
import csv
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

# Configuration du logging
logger = logging.getLogger(__name__)


class ExportManager:
    """
    Gestionnaire principal pour l'export des données.
    """
    
    def __init__(self, output_dir: str, db_connection=None):
        """
        Initialise le gestionnaire d'export.
        
        Args:
            output_dir (str): Répertoire de sortie pour les exports
            db_connection: Connexion à la base de données SQLite3
        """
        self.output_dir = output_dir
        self.db_connection = db_connection
        
        # Création du répertoire de sortie si nécessaire
        os.makedirs(output_dir, exist_ok=True)
        
        # Templates Markdown par défaut
        self.markdown_templates = {
            'video': self._get_video_markdown_template(),
            'channel': self._get_channel_markdown_template(),
            'playlist': self._get_playlist_markdown_template()
        }
    
    def export_to_json(self, data: List[Dict], filename: str = None, 
                      pretty: bool = True) -> Optional[str]:
        """
        Exporte les données au format JSON.
        
        Args:
            data (list): Données à exporter
            filename (str): Nom du fichier (sans extension)
            pretty (bool): Formatage indenté
        
        Returns:
            str: Chemin du fichier créé ou None si erreur
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{timestamp}"
            
            file_path = os.path.join(self.output_dir, f"{filename}.json")
            
            # Préparation des données pour l'export
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_items': len(data),
                    'format': 'json'
                },
                'data': data
            }
            
            # Écriture du fichier JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, f, ensure_ascii=False)
            
            # Enregistrement de l'export dans la base de données
            self._log_export('json', file_path, len(data))
            
            logger.info(f"Export JSON créé: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export JSON: {str(e)}")
            return None
    
    def export_to_markdown(self, data: List[Dict], content_type: str, 
                          filename: str = None, template: str = None) -> Optional[str]:
        """
        Exporte les données au format Markdown.
        
        Args:
            data (list): Données à exporter
            content_type (str): Type de contenu ('video', 'channel', 'playlist')
            filename (str): Nom du fichier (sans extension)
            template (str): Template Markdown personnalisé
        
        Returns:
            str: Chemin du fichier créé ou None si erreur
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{content_type}_{timestamp}"
            
            file_path = os.path.join(self.output_dir, f"{filename}.md")
            
            # Utilisation du template approprié
            if not template:
                template = self.markdown_templates.get(content_type, 
                                                      self.markdown_templates['video'])
            
            # Génération du contenu Markdown
            markdown_content = self._generate_markdown_content(data, content_type, template)
            
            # Écriture du fichier Markdown
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Enregistrement de l'export dans la base de données
            self._log_export('markdown', file_path, len(data))
            
            logger.info(f"Export Markdown créé: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export Markdown: {str(e)}")
            return None
    
    def export_to_text(self, data: List[Dict], content_type: str, 
                      filename: str = None, format_style: str = 'detailed') -> Optional[str]:
        """
        Exporte les données au format texte brut.
        
        Args:
            data (list): Données à exporter
            content_type (str): Type de contenu
            filename (str): Nom du fichier (sans extension)
            format_style (str): Style de formatage ('simple', 'detailed', 'compact')
        
        Returns:
            str: Chemin du fichier créé ou None si erreur
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{content_type}_{timestamp}"
            
            file_path = os.path.join(self.output_dir, f"{filename}.txt")
            
            # Génération du contenu texte
            text_content = self._generate_text_content(data, content_type, format_style)
            
            # Écriture du fichier texte
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # Enregistrement de l'export dans la base de données
            self._log_export('text', file_path, len(data))
            
            logger.info(f"Export texte créé: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export texte: {str(e)}")
            return None
    
    def export_to_csv(self, data: List[Dict], content_type: str, 
                     filename: str = None) -> Optional[str]:
        """
        Exporte les données au format CSV.
        
        Args:
            data (list): Données à exporter
            content_type (str): Type de contenu
            filename (str): Nom du fichier (sans extension)
        
        Returns:
            str: Chemin du fichier créé ou None si erreur
        """
        try:
            if not data:
                logger.warning("Aucune donnée à exporter")
                return None
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{content_type}_{timestamp}"
            
            file_path = os.path.join(self.output_dir, f"{filename}.csv")
            
            # Détermination des colonnes selon le type de contenu
            fieldnames = self._get_csv_fieldnames(content_type)
            
            # Écriture du fichier CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in data:
                    # Filtrage des champs selon les colonnes définies
                    filtered_item = {k: v for k, v in item.items() if k in fieldnames}
                    writer.writerow(filtered_item)
            
            # Enregistrement de l'export dans la base de données
            self._log_export('csv', file_path, len(data))
            
            logger.info(f"Export CSV créé: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export CSV: {str(e)}")
            return None
    
    def export_database(self, target_path: str) -> bool:
        """
        Exporte la base de données complète.
        
        Args:
            target_path (str): Chemin de destination
        
        Returns:
            bool: True si l'export a réussi, False sinon
        """
        try:
            if not self.db_connection:
                logger.error("Aucune connexion à la base de données")
                return False
            
            # Création d'une sauvegarde de la base de données
            backup = sqlite3.connect(target_path)
            self.db_connection.backup(backup)
            backup.close()
            
            # Enregistrement de l'export dans la base de données
            self._log_export('database', target_path, 0)
            
            logger.info(f"Export de base de données créé: {target_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export de base de données: {str(e)}")
            return False
    
    def _generate_markdown_content(self, data: List[Dict], content_type: str, 
                                  template: str) -> str:
        """
        Génère le contenu Markdown à partir des données et du template.
        
        Args:
            data (list): Données à formater
            content_type (str): Type de contenu
            template (str): Template Markdown
        
        Returns:
            str: Contenu Markdown formaté
        """
        # En-tête du document
        content = f"# Export {content_type.title()}\n\n"
        content += f"**Date d'export:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        content += f"**Nombre d'éléments:** {len(data)}\n\n"
        content += "---\n\n"
        
        # Génération du contenu pour chaque élément
        for i, item in enumerate(data, 1):
            item_content = template
            
            # Remplacement des placeholders
            for key, value in item.items():
                placeholder = f"{{{key}}}"
                if placeholder in item_content:
                    # Formatage spécial pour certains champs
                    if key == 'published_at' and value:
                        try:
                            date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            formatted_date = date_obj.strftime('%d/%m/%Y')
                            item_content = item_content.replace(placeholder, formatted_date)
                        except:
                            item_content = item_content.replace(placeholder, str(value))
                    elif key in ['view_count', 'like_count', 'subscriber_count'] and value:
                        formatted_number = f"{int(value):,}".replace(',', ' ')
                        item_content = item_content.replace(placeholder, formatted_number)
                    else:
                        item_content = item_content.replace(placeholder, str(value or ''))
            
            content += f"## {i}. {item.get('title', 'Sans titre')}\n\n"
            content += item_content + "\n\n"
        
        return content
    
    def _generate_text_content(self, data: List[Dict], content_type: str, 
                              format_style: str) -> str:
        """
        Génère le contenu texte à partir des données.
        
        Args:
            data (list): Données à formater
            content_type (str): Type de contenu
            format_style (str): Style de formatage
        
        Returns:
            str: Contenu texte formaté
        """
        content = f"EXPORT {content_type.upper()}\n"
        content += "=" * 50 + "\n"
        content += f"Date d'export: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        content += f"Nombre d'éléments: {len(data)}\n\n"
        
        for i, item in enumerate(data, 1):
            content += f"{i}. {item.get('title', 'Sans titre')}\n"
            content += "-" * 40 + "\n"
            
            if format_style == 'simple':
                content += f"URL: https://youtube.com/watch?v={item.get('video_id', '')}\n"
                content += f"Chaîne: {item.get('channel_title', '')}\n"
            
            elif format_style == 'detailed':
                if content_type == 'video':
                    content += f"ID Vidéo: {item.get('video_id', '')}\n"
                    content += f"Chaîne: {item.get('channel_title', '')}\n"
                    content += f"Durée: {item.get('duration', '')}\n"
                    content += f"Vues: {item.get('view_count', 0):,}\n"
                    content += f"Likes: {item.get('like_count', 0):,}\n"
                    content += f"Date: {item.get('published_at', '')}\n"
                    if item.get('description'):
                        desc = item['description'][:200] + "..." if len(item['description']) > 200 else item['description']
                        content += f"Description: {desc}\n"
                
                elif content_type == 'channel':
                    content += f"ID Chaîne: {item.get('channel_id', '')}\n"
                    content += f"Abonnés: {item.get('subscriber_count', 0):,}\n"
                    content += f"Vidéos: {item.get('video_count', 0):,}\n"
                    content += f"Vues totales: {item.get('view_count', 0):,}\n"
                    content += f"Pays: {item.get('country', '')}\n"
            
            elif format_style == 'compact':
                content += f"{item.get('channel_title', '')} | {item.get('view_count', 0):,} vues\n"
            
            content += "\n"
        
        return content
    
    def _get_csv_fieldnames(self, content_type: str) -> List[str]:
        """
        Retourne les noms de colonnes pour l'export CSV selon le type de contenu.
        
        Args:
            content_type (str): Type de contenu
        
        Returns:
            list: Liste des noms de colonnes
        """
        if content_type == 'video':
            return [
                'video_id', 'title', 'channel_title', 'duration', 
                'view_count', 'like_count', 'comment_count', 
                'published_at', 'language'
            ]
        elif content_type == 'channel':
            return [
                'channel_id', 'title', 'subscriber_count', 
                'video_count', 'view_count', 'published_at', 'country'
            ]
        elif content_type == 'playlist':
            return [
                'playlist_id', 'title', 'channel_title', 
                'item_count', 'published_at'
            ]
        else:
            return []
    
    def _get_video_markdown_template(self) -> str:
        """
        Retourne le template Markdown pour les vidéos.
        """
        return """
**Chaîne:** {channel_title}
**Durée:** {duration}
**Vues:** {view_count}
**Likes:** {like_count}
**Date de publication:** {published_at}
**URL:** https://youtube.com/watch?v={video_id}

**Description:**
{description}
"""
    
    def _get_channel_markdown_template(self) -> str:
        """
        Retourne le template Markdown pour les chaînes.
        """
        return """
**ID Chaîne:** {channel_id}
**Abonnés:** {subscriber_count}
**Nombre de vidéos:** {video_count}
**Vues totales:** {view_count}
**Pays:** {country}
**Date de création:** {published_at}
**URL:** https://youtube.com/channel/{channel_id}

**Description:**
{description}
"""
    
    def _get_playlist_markdown_template(self) -> str:
        """
        Retourne le template Markdown pour les playlists.
        """
        return """
**Chaîne:** {channel_title}
**Nombre d'éléments:** {item_count}
**Date de création:** {published_at}
**URL:** https://youtube.com/playlist?list={playlist_id}

**Description:**
{description}
"""
    
    def _log_export(self, export_type: str, file_path: str, item_count: int):
        """
        Enregistre l'export dans la base de données.
        
        Args:
            export_type (str): Type d'export
            file_path (str): Chemin du fichier
            item_count (int): Nombre d'éléments exportés
        """
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
            INSERT INTO exports (export_type, file_path, item_count)
            VALUES (?, ?, ?)
            """, (export_type, file_path, item_count))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'export: {str(e)}")
    
    def get_export_history(self) -> List[Dict]:
        """
        Récupère l'historique des exports.
        
        Returns:
            list: Liste des exports précédents
        """
        if not self.db_connection:
            return []
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
            SELECT export_type, file_path, item_count, created_at
            FROM exports
            ORDER BY created_at DESC
            LIMIT 50
            """)
            
            exports = []
            for row in cursor.fetchall():
                export = {
                    'type': row[0],
                    'file_path': row[1],
                    'item_count': row[2],
                    'created_at': row[3]
                }
                exports.append(export)
            
            return exports
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {str(e)}")
            return []