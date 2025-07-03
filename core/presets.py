#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de gestion des presets

Ce module gère les presets personnalisés pour le filtrage,
l'affichage et l'export des données YouTube.
"""

import json
import logging
import sqlite3
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Configuration du logging
logger = logging.getLogger(__name__)


class PresetManager:
    """
    Gestionnaire des presets pour l'application.
    """
    
    def __init__(self, db_connection):
        """
        Initialise le gestionnaire de presets.
        
        Args:
            db_connection: Connexion à la base de données SQLite3
        """
        self.conn = db_connection
        self.cursor = self.conn.cursor()
    
    def get_all_presets(self) -> List[Dict]:
        """
        Récupère tous les presets disponibles.
        
        Returns:
            list: Liste des presets
        """
        try:
            self.cursor.execute("""
            SELECT id, name, description, content_type, filters, 
                   llm_model, image_model, export_format, ui_template, is_default
            FROM presets
            ORDER BY is_default DESC, name ASC
            """)
            
            presets = []
            for row in self.cursor.fetchall():
                preset = {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'content_type': row[3],
                    'filters': json.loads(row[4]) if row[4] else {},
                    'llm_model': row[5],
                    'image_model': row[6],
                    'export_format': row[7],
                    'ui_template': row[8],
                    'is_default': bool(row[9])
                }
                presets.append(preset)
            
            logger.info(f"Récupéré {len(presets)} presets")
            return presets
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des presets: {str(e)}")
            return []
    
    def get_preset_by_id(self, preset_id: int) -> Optional[Dict]:
        """
        Récupère un preset par son ID.
        
        Args:
            preset_id (int): ID du preset
        
        Returns:
            dict: Preset ou None si non trouvé
        """
        try:
            self.cursor.execute("""
            SELECT id, name, description, content_type, filters, 
                   llm_model, image_model, export_format, ui_template, is_default
            FROM presets
            WHERE id = ?
            """, (preset_id,))
            
            row = self.cursor.fetchone()
            if not row:
                logger.warning(f"Preset non trouvé: ID {preset_id}")
                return None
            
            preset = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'content_type': row[3],
                'filters': json.loads(row[4]) if row[4] else {},
                'llm_model': row[5],
                'image_model': row[6],
                'export_format': row[7],
                'ui_template': row[8],
                'is_default': bool(row[9])
            }
            
            logger.info(f"Preset récupéré: {preset['name']}")
            return preset
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du preset {preset_id}: {str(e)}")
            return None
    
    def get_default_preset(self, content_type: str = None) -> Optional[Dict]:
        """
        Récupère le preset par défaut pour un type de contenu.
        
        Args:
            content_type (str): Type de contenu ('video', 'channel', 'playlist')
        
        Returns:
            dict: Preset par défaut ou None si non trouvé
        """
        try:
            query = """
            SELECT id, name, description, content_type, filters, 
                   llm_model, image_model, export_format, ui_template, is_default
            FROM presets
            WHERE is_default = 1
            """
            
            params = ()
            if content_type:
                query += " AND content_type = ?"
                params = (content_type,)
            
            query += " LIMIT 1"
            
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            
            if not row:
                logger.warning(f"Aucun preset par défaut trouvé pour {content_type or 'tous les types'}")
                return None
            
            preset = {
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'content_type': row[3],
                'filters': json.loads(row[4]) if row[4] else {},
                'llm_model': row[5],
                'image_model': row[6],
                'export_format': row[7],
                'ui_template': row[8],
                'is_default': bool(row[9])
            }
            
            logger.info(f"Preset par défaut récupéré: {preset['name']}")
            return preset
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du preset par défaut: {str(e)}")
            return None
    
    def create_preset(self, preset_data: Dict) -> Optional[int]:
        """
        Crée un nouveau preset.
        
        Args:
            preset_data (dict): Données du preset
        
        Returns:
            int: ID du nouveau preset ou None si erreur
        """
        try:
            # Vérification des champs obligatoires
            required_fields = ['name', 'content_type']
            for field in required_fields:
                if field not in preset_data:
                    logger.error(f"Champ obligatoire manquant: {field}")
                    return None
            
            # Préparation des données
            name = preset_data['name']
            description = preset_data.get('description', '')
            content_type = preset_data['content_type']
            filters = json.dumps(preset_data.get('filters', {}))
            llm_model = preset_data.get('llm_model', '')
            image_model = preset_data.get('image_model', '')
            export_format = preset_data.get('export_format', 'markdown')
            ui_template = preset_data.get('ui_template', 'standard')
            is_default = 1 if preset_data.get('is_default', False) else 0
            
            # Si ce preset est défini comme défaut, désactiver les autres par défaut
            if is_default:
                self.cursor.execute("""
                UPDATE presets
                SET is_default = 0
                WHERE content_type = ?
                """, (content_type,))
            
            # Insertion du nouveau preset
            self.cursor.execute("""
            INSERT INTO presets (
                name, description, content_type, filters, 
                llm_model, image_model, export_format, ui_template, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, description, content_type, filters,
                llm_model, image_model, export_format, ui_template, is_default
            ))
            
            self.conn.commit()
            preset_id = self.cursor.lastrowid
            
            logger.info(f"Preset créé: {name} (ID: {preset_id})")
            return preset_id
        
        except sqlite3.IntegrityError as e:
            logger.error(f"Erreur d'intégrité lors de la création du preset: {str(e)}")
            self.conn.rollback()
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la création du preset: {str(e)}")
            self.conn.rollback()
            return None
    
    def update_preset(self, preset_id: int, preset_data: Dict) -> bool:
        """
        Met à jour un preset existant.
        
        Args:
            preset_id (int): ID du preset à mettre à jour
            preset_data (dict): Nouvelles données du preset
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon
        """
        try:
            # Vérification de l'existence du preset
            self.cursor.execute("SELECT id FROM presets WHERE id = ?", (preset_id,))
            if not self.cursor.fetchone():
                logger.warning(f"Preset non trouvé: ID {preset_id}")
                return False
            
            # Préparation des données
            update_fields = []
            params = []
            
            if 'name' in preset_data:
                update_fields.append("name = ?")
                params.append(preset_data['name'])
            
            if 'description' in preset_data:
                update_fields.append("description = ?")
                params.append(preset_data['description'])
            
            if 'content_type' in preset_data:
                update_fields.append("content_type = ?")
                params.append(preset_data['content_type'])
            
            if 'filters' in preset_data:
                update_fields.append("filters = ?")
                params.append(json.dumps(preset_data['filters']))
            
            if 'llm_model' in preset_data:
                update_fields.append("llm_model = ?")
                params.append(preset_data['llm_model'])
            
            if 'image_model' in preset_data:
                update_fields.append("image_model = ?")
                params.append(preset_data['image_model'])
            
            if 'export_format' in preset_data:
                update_fields.append("export_format = ?")
                params.append(preset_data['export_format'])
            
            if 'ui_template' in preset_data:
                update_fields.append("ui_template = ?")
                params.append(preset_data['ui_template'])
            
            if 'is_default' in preset_data:
                is_default = 1 if preset_data['is_default'] else 0
                update_fields.append("is_default = ?")
                params.append(is_default)
                
                # Si ce preset est défini comme défaut, désactiver les autres par défaut
                if is_default:
                    # Récupérer le type de contenu du preset
                    self.cursor.execute("SELECT content_type FROM presets WHERE id = ?", (preset_id,))
                    content_type = self.cursor.fetchone()[0]
                    
                    self.cursor.execute("""
                    UPDATE presets
                    SET is_default = 0
                    WHERE content_type = ? AND id != ?
                    """, (content_type, preset_id))
            
            # Mise à jour du preset
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
            UPDATE presets
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            params.append(preset_id)
            self.cursor.execute(query, params)
            self.conn.commit()
            
            logger.info(f"Preset mis à jour: ID {preset_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du preset {preset_id}: {str(e)}")
            self.conn.rollback()
            return False
    
    def delete_preset(self, preset_id: int) -> bool:
        """
        Supprime un preset.
        
        Args:
            preset_id (int): ID du preset à supprimer
        
        Returns:
            bool: True si la suppression a réussi, False sinon
        """
        try:
            # Vérification de l'existence du preset
            self.cursor.execute("SELECT is_default FROM presets WHERE id = ?", (preset_id,))
            row = self.cursor.fetchone()
            if not row:
                logger.warning(f"Preset non trouvé: ID {preset_id}")
                return False
            
            # Empêcher la suppression du preset par défaut
            if row[0]:
                logger.warning(f"Impossible de supprimer le preset par défaut: ID {preset_id}")
                return False
            
            # Suppression du preset
            self.cursor.execute("DELETE FROM presets WHERE id = ?", (preset_id,))
            self.conn.commit()
            
            logger.info(f"Preset supprimé: ID {preset_id}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du preset {preset_id}: {str(e)}")
            self.conn.rollback()
            return False
    
    def apply_preset_filters(self, preset_id: int, query_base: str) -> str:
        """
        Applique les filtres d'un preset à une requête SQL.
        
        Args:
            preset_id (int): ID du preset
            query_base (str): Requête SQL de base
        
        Returns:
            str: Requête SQL avec filtres appliqués
        """
        preset = self.get_preset_by_id(preset_id)
        if not preset:
            return query_base
        
        filters = preset.get('filters', {})
        content_type = preset.get('content_type')
        
        where_clauses = []
        params = []
        
        # Application des filtres selon le type de contenu
        if content_type == 'video':
            # Filtre de durée minimale
            if 'min_duration' in filters:
                where_clauses.append("duration >= ?")
                params.append(filters['min_duration'])
            
            # Filtre de durée maximale
            if 'max_duration' in filters:
                where_clauses.append("duration <= ?")
                params.append(filters['max_duration'])
            
            # Filtre de vues minimales
            if 'min_views' in filters:
                where_clauses.append("view_count >= ?")
                params.append(filters['min_views'])
            
            # Filtre de likes minimaux
            if 'min_likes' in filters:
                where_clauses.append("like_count >= ?")
                params.append(filters['min_likes'])
            
            # Filtre de date de publication minimale
            if 'min_date' in filters:
                where_clauses.append("published_at >= ?")
                params.append(filters['min_date'])
            
            # Filtre de date de publication maximale
            if 'max_date' in filters:
                where_clauses.append("published_at <= ?")
                params.append(filters['max_date'])
            
            # Filtre de mots-clés inclus
            if 'keywords' in filters and filters['keywords']:
                keywords = filters['keywords']
                if isinstance(keywords, list):
                    for keyword in keywords:
                        where_clauses.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
                        keyword_param = f"%{keyword}%"
                        params.extend([keyword_param, keyword_param, keyword_param])
            
            # Filtre de mots-clés exclus
            if 'exclude_keywords' in filters and filters['exclude_keywords']:
                exclude_keywords = filters['exclude_keywords']
                if isinstance(exclude_keywords, list):
                    for keyword in exclude_keywords:
                        where_clauses.append("(title NOT LIKE ? AND description NOT LIKE ? AND tags NOT LIKE ?)")
                        keyword_param = f"%{keyword}%"
                        params.extend([keyword_param, keyword_param, keyword_param])
        
        elif content_type == 'channel':
            # Filtre d'abonnés minimaux
            if 'min_subscribers' in filters:
                where_clauses.append("subscriber_count >= ?")
                params.append(filters['min_subscribers'])
            
            # Filtre de vidéos minimales
            if 'min_videos' in filters:
                where_clauses.append("video_count >= ?")
                params.append(filters['min_videos'])
            
            # Filtre d'âge maximal en jours
            if 'max_age_days' in filters:
                where_clauses.append("published_at >= date('now', ?)")
                params.append(f"-{filters['max_age_days']} days")
        
        elif content_type == 'playlist':
            # Filtre de nombre d'éléments minimal
            if 'min_items' in filters:
                where_clauses.append("item_count >= ?")
                params.append(filters['min_items'])
            
            # Filtre de mots-clés inclus
            if 'keywords' in filters and filters['keywords']:
                keywords = filters['keywords']
                if isinstance(keywords, list):
                    for keyword in keywords:
                        where_clauses.append("(title LIKE ? OR description LIKE ?)")
                        keyword_param = f"%{keyword}%"
                        params.extend([keyword_param, keyword_param])
        
        # Construction de la requête finale
        if where_clauses:
            if 'WHERE' in query_base:
                query = f"{query_base} AND {' AND '.join(where_clauses)}"
            else:
                query = f"{query_base} WHERE {' AND '.join(where_clauses)}"
        else:
            query = query_base
        
        logger.info(f"Requête avec filtres appliqués: {query}")
        return query, params