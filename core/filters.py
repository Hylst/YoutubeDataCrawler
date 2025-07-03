#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de filtrage des données YouTube

Ce module fournit des fonctionnalités de filtrage avancées
pour les vidéos, chaînes et playlists YouTube.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Callable

# Configuration du logging
logger = logging.getLogger(__name__)


class FilterCriteria:
    """
    Classe pour définir les critères de filtrage.
    """
    
    def __init__(self):
        """
        Initialise les critères de filtrage.
        """
        self.criteria = {}
    
    def add_duration_filter(self, min_duration: str = None, max_duration: str = None):
        """
        Ajoute un filtre de durée.
        
        Args:
            min_duration (str): Durée minimale au format ISO 8601 (ex: PT5M)
            max_duration (str): Durée maximale au format ISO 8601
        """
        if min_duration:
            self.criteria['min_duration'] = min_duration
        if max_duration:
            self.criteria['max_duration'] = max_duration
    
    def add_view_count_filter(self, min_views: int = None, max_views: int = None):
        """
        Ajoute un filtre de nombre de vues.
        
        Args:
            min_views (int): Nombre minimal de vues
            max_views (int): Nombre maximal de vues
        """
        if min_views is not None:
            self.criteria['min_views'] = min_views
        if max_views is not None:
            self.criteria['max_views'] = max_views
    
    def add_like_count_filter(self, min_likes: int = None, max_likes: int = None):
        """
        Ajoute un filtre de nombre de likes.
        
        Args:
            min_likes (int): Nombre minimal de likes
            max_likes (int): Nombre maximal de likes
        """
        if min_likes is not None:
            self.criteria['min_likes'] = min_likes
        if max_likes is not None:
            self.criteria['max_likes'] = max_likes
    
    def add_date_filter(self, start_date: str = None, end_date: str = None):
        """
        Ajoute un filtre de date de publication.
        
        Args:
            start_date (str): Date de début au format YYYY-MM-DD
            end_date (str): Date de fin au format YYYY-MM-DD
        """
        if start_date:
            self.criteria['start_date'] = start_date
        if end_date:
            self.criteria['end_date'] = end_date
    
    def add_keyword_filter(self, include_keywords: List[str] = None, 
                          exclude_keywords: List[str] = None):
        """
        Ajoute un filtre de mots-clés.
        
        Args:
            include_keywords (list): Mots-clés à inclure
            exclude_keywords (list): Mots-clés à exclure
        """
        if include_keywords:
            self.criteria['include_keywords'] = include_keywords
        if exclude_keywords:
            self.criteria['exclude_keywords'] = exclude_keywords
    
    def add_language_filter(self, languages: List[str]):
        """
        Ajoute un filtre de langue.
        
        Args:
            languages (list): Codes de langue (ex: ['en', 'fr'])
        """
        self.criteria['languages'] = languages
    
    def add_channel_filter(self, channel_ids: List[str] = None, 
                          exclude_channel_ids: List[str] = None):
        """
        Ajoute un filtre de chaîne.
        
        Args:
            channel_ids (list): IDs de chaînes à inclure
            exclude_channel_ids (list): IDs de chaînes à exclure
        """
        if channel_ids:
            self.criteria['channel_ids'] = channel_ids
        if exclude_channel_ids:
            self.criteria['exclude_channel_ids'] = exclude_channel_ids
    
    def to_dict(self) -> Dict:
        """
        Convertit les critères en dictionnaire.
        
        Returns:
            dict: Critères de filtrage
        """
        return self.criteria.copy()


class DataFilter:
    """
    Classe principale pour le filtrage des données YouTube.
    """
    
    def __init__(self):
        """
        Initialise le filtre de données.
        """
        self.filters = {
            'video': self._filter_videos,
            'channel': self._filter_channels,
            'playlist': self._filter_playlists
        }
    
    def filter_data(self, data: List[Dict], content_type: str, 
                   criteria: Union[FilterCriteria, Dict]) -> List[Dict]:
        """
        Filtre les données selon les critères spécifiés.
        
        Args:
            data (list): Liste des données à filtrer
            content_type (str): Type de contenu ('video', 'channel', 'playlist')
            criteria (FilterCriteria or dict): Critères de filtrage
        
        Returns:
            list: Données filtrées
        """
        if not data:
            return []
        
        if isinstance(criteria, FilterCriteria):
            criteria = criteria.to_dict()
        
        if content_type not in self.filters:
            logger.warning(f"Type de contenu non supporté: {content_type}")
            return data
        
        filter_func = self.filters[content_type]
        filtered_data = filter_func(data, criteria)
        
        logger.info(f"Filtrage terminé: {len(filtered_data)}/{len(data)} éléments conservés")
        return filtered_data
    
    def _filter_videos(self, videos: List[Dict], criteria: Dict) -> List[Dict]:
        """
        Filtre les vidéos selon les critères.
        
        Args:
            videos (list): Liste des vidéos
            criteria (dict): Critères de filtrage
        
        Returns:
            list: Vidéos filtrées
        """
        filtered_videos = []
        
        for video in videos:
            if self._video_matches_criteria(video, criteria):
                filtered_videos.append(video)
        
        return filtered_videos
    
    def _filter_channels(self, channels: List[Dict], criteria: Dict) -> List[Dict]:
        """
        Filtre les chaînes selon les critères.
        
        Args:
            channels (list): Liste des chaînes
            criteria (dict): Critères de filtrage
        
        Returns:
            list: Chaînes filtrées
        """
        filtered_channels = []
        
        for channel in channels:
            if self._channel_matches_criteria(channel, criteria):
                filtered_channels.append(channel)
        
        return filtered_channels
    
    def _filter_playlists(self, playlists: List[Dict], criteria: Dict) -> List[Dict]:
        """
        Filtre les playlists selon les critères.
        
        Args:
            playlists (list): Liste des playlists
            criteria (dict): Critères de filtrage
        
        Returns:
            list: Playlists filtrées
        """
        filtered_playlists = []
        
        for playlist in playlists:
            if self._playlist_matches_criteria(playlist, criteria):
                filtered_playlists.append(playlist)
        
        return filtered_playlists
    
    def _video_matches_criteria(self, video: Dict, criteria: Dict) -> bool:
        """
        Vérifie si une vidéo correspond aux critères.
        
        Args:
            video (dict): Données de la vidéo
            criteria (dict): Critères de filtrage
        
        Returns:
            bool: True si la vidéo correspond aux critères
        """
        # Filtre de durée
        if 'min_duration' in criteria or 'max_duration' in criteria:
            duration_seconds = self._parse_duration(video.get('duration', ''))
            
            if 'min_duration' in criteria:
                min_seconds = self._parse_duration(criteria['min_duration'])
                if duration_seconds < min_seconds:
                    return False
            
            if 'max_duration' in criteria:
                max_seconds = self._parse_duration(criteria['max_duration'])
                if duration_seconds > max_seconds:
                    return False
        
        # Filtre de vues
        if 'min_views' in criteria:
            if video.get('view_count', 0) < criteria['min_views']:
                return False
        
        if 'max_views' in criteria:
            if video.get('view_count', 0) > criteria['max_views']:
                return False
        
        # Filtre de likes
        if 'min_likes' in criteria:
            if video.get('like_count', 0) < criteria['min_likes']:
                return False
        
        if 'max_likes' in criteria:
            if video.get('like_count', 0) > criteria['max_likes']:
                return False
        
        # Filtre de date
        if 'start_date' in criteria or 'end_date' in criteria:
            published_date = self._parse_date(video.get('published_at', ''))
            
            if 'start_date' in criteria:
                start_date = datetime.fromisoformat(criteria['start_date'])
                if published_date < start_date:
                    return False
            
            if 'end_date' in criteria:
                end_date = datetime.fromisoformat(criteria['end_date'])
                if published_date > end_date:
                    return False
        
        # Filtre de mots-clés inclus
        if 'include_keywords' in criteria:
            if not self._contains_keywords(video, criteria['include_keywords']):
                return False
        
        # Filtre de mots-clés exclus
        if 'exclude_keywords' in criteria:
            if self._contains_keywords(video, criteria['exclude_keywords']):
                return False
        
        # Filtre de langue
        if 'languages' in criteria:
            video_language = video.get('language', '').lower()
            if video_language not in [lang.lower() for lang in criteria['languages']]:
                return False
        
        # Filtre de chaîne
        if 'channel_ids' in criteria:
            if video.get('channel_id') not in criteria['channel_ids']:
                return False
        
        if 'exclude_channel_ids' in criteria:
            if video.get('channel_id') in criteria['exclude_channel_ids']:
                return False
        
        return True
    
    def _channel_matches_criteria(self, channel: Dict, criteria: Dict) -> bool:
        """
        Vérifie si une chaîne correspond aux critères.
        
        Args:
            channel (dict): Données de la chaîne
            criteria (dict): Critères de filtrage
        
        Returns:
            bool: True si la chaîne correspond aux critères
        """
        # Filtre d'abonnés
        if 'min_subscribers' in criteria:
            if channel.get('subscriber_count', 0) < criteria['min_subscribers']:
                return False
        
        if 'max_subscribers' in criteria:
            if channel.get('subscriber_count', 0) > criteria['max_subscribers']:
                return False
        
        # Filtre de nombre de vidéos
        if 'min_videos' in criteria:
            if channel.get('video_count', 0) < criteria['min_videos']:
                return False
        
        if 'max_videos' in criteria:
            if channel.get('video_count', 0) > criteria['max_videos']:
                return False
        
        # Filtre de date de création
        if 'start_date' in criteria or 'end_date' in criteria:
            published_date = self._parse_date(channel.get('published_at', ''))
            
            if 'start_date' in criteria:
                start_date = datetime.fromisoformat(criteria['start_date'])
                if published_date < start_date:
                    return False
            
            if 'end_date' in criteria:
                end_date = datetime.fromisoformat(criteria['end_date'])
                if published_date > end_date:
                    return False
        
        # Filtre de mots-clés
        if 'include_keywords' in criteria:
            if not self._contains_keywords(channel, criteria['include_keywords']):
                return False
        
        if 'exclude_keywords' in criteria:
            if self._contains_keywords(channel, criteria['exclude_keywords']):
                return False
        
        # Filtre de pays
        if 'countries' in criteria:
            channel_country = channel.get('country', '').lower()
            if channel_country not in [country.lower() for country in criteria['countries']]:
                return False
        
        return True
    
    def _playlist_matches_criteria(self, playlist: Dict, criteria: Dict) -> bool:
        """
        Vérifie si une playlist correspond aux critères.
        
        Args:
            playlist (dict): Données de la playlist
            criteria (dict): Critères de filtrage
        
        Returns:
            bool: True si la playlist correspond aux critères
        """
        # Filtre de nombre d'éléments
        if 'min_items' in criteria:
            if playlist.get('item_count', 0) < criteria['min_items']:
                return False
        
        if 'max_items' in criteria:
            if playlist.get('item_count', 0) > criteria['max_items']:
                return False
        
        # Filtre de date
        if 'start_date' in criteria or 'end_date' in criteria:
            published_date = self._parse_date(playlist.get('published_at', ''))
            
            if 'start_date' in criteria:
                start_date = datetime.fromisoformat(criteria['start_date'])
                if published_date < start_date:
                    return False
            
            if 'end_date' in criteria:
                end_date = datetime.fromisoformat(criteria['end_date'])
                if published_date > end_date:
                    return False
        
        # Filtre de mots-clés
        if 'include_keywords' in criteria:
            if not self._contains_keywords(playlist, criteria['include_keywords']):
                return False
        
        if 'exclude_keywords' in criteria:
            if self._contains_keywords(playlist, criteria['exclude_keywords']):
                return False
        
        # Filtre de chaîne
        if 'channel_ids' in criteria:
            if playlist.get('channel_id') not in criteria['channel_ids']:
                return False
        
        if 'exclude_channel_ids' in criteria:
            if playlist.get('channel_id') in criteria['exclude_channel_ids']:
                return False
        
        return True
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse une durée ISO 8601 en secondes.
        
        Args:
            duration_str (str): Durée au format ISO 8601 (ex: PT5M30S)
        
        Returns:
            int: Durée en secondes
        """
        if not duration_str:
            return 0
        
        # Pattern pour parser PT5M30S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse une date ISO 8601.
        
        Args:
            date_str (str): Date au format ISO 8601
        
        Returns:
            datetime: Objet datetime
        """
        if not date_str:
            return datetime.min
        
        try:
            # Supprime le Z final et parse
            clean_date = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_date)
        except ValueError:
            logger.warning(f"Format de date invalide: {date_str}")
            return datetime.min
    
    def _contains_keywords(self, item: Dict, keywords: List[str]) -> bool:
        """
        Vérifie si un élément contient des mots-clés.
        
        Args:
            item (dict): Élément à vérifier
            keywords (list): Liste de mots-clés
        
        Returns:
            bool: True si au moins un mot-clé est trouvé
        """
        # Texte à rechercher
        search_text = ""
        search_text += item.get('title', '').lower() + " "
        search_text += item.get('description', '').lower() + " "
        
        # Ajout des tags pour les vidéos
        if 'tags' in item:
            try:
                tags = json.loads(item['tags']) if isinstance(item['tags'], str) else item['tags']
                if isinstance(tags, list):
                    search_text += " ".join(tags).lower()
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Recherche des mots-clés
        for keyword in keywords:
            if keyword.lower() in search_text:
                return True
        
        return False
    
    def get_filter_statistics(self, original_data: List[Dict], 
                             filtered_data: List[Dict]) -> Dict:
        """
        Génère des statistiques sur le filtrage.
        
        Args:
            original_data (list): Données originales
            filtered_data (list): Données filtrées
        
        Returns:
            dict: Statistiques de filtrage
        """
        original_count = len(original_data)
        filtered_count = len(filtered_data)
        
        stats = {
            'original_count': original_count,
            'filtered_count': filtered_count,
            'removed_count': original_count - filtered_count,
            'retention_rate': (filtered_count / original_count * 100) if original_count > 0 else 0
        }
        
        return stats