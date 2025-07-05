#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module d'interface avec l'API YouTube Data v3

Ce module gère toutes les interactions avec l'API YouTube pour récupérer
les informations sur les vidéos, chaînes et playlists.
"""

import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration du logging
logger = logging.getLogger(__name__)


class YouTubeAPI:
    """
    Classe pour gérer les interactions avec l'API YouTube Data v3.
    """
    
    def __init__(self, api_key: str):
        """
        Initialise l'instance de l'API YouTube.
        
        Args:
            api_key (str): Clé API YouTube Data v3
        """
        self.api_key = api_key
        self.youtube = None
        self._initialize_service()
    
    def _initialize_service(self):
        """
        Initialise le service YouTube API.
        """
        try:
            self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            logger.info("Service YouTube API initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du service YouTube API: {str(e)}")
            raise
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrait l'ID de vidéo à partir d'une URL YouTube.
        
        Args:
            url (str): URL YouTube
        
        Returns:
            str: ID de la vidéo ou None si non trouvé
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Si c'est déjà un ID de vidéo
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
        
        return None
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """
        Extrait l'ID de playlist à partir d'une URL YouTube.
        
        Args:
            url (str): URL YouTube
        
        Returns:
            str: ID de la playlist ou None si non trouvé
        """
        pattern = r'[?&]list=([a-zA-Z0-9_-]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        
        # Si c'est déjà un ID de playlist
        if re.match(r'^[a-zA-Z0-9_-]+$', url) and len(url) > 11:
            return url
        
        return None
    
    def extract_channel_id(self, url: str) -> Optional[str]:
        """
        Extrait l'ID de chaîne à partir d'une URL YouTube.
        
        Args:
            url (str): URL YouTube
        
        Returns:
            str: ID de la chaîne ou None si non trouvé
        """
        patterns = [
            r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
            r'youtube\.com/c/([a-zA-Z0-9_-]+)',
            r'youtube\.com/user/([a-zA-Z0-9_-]+)',
            r'youtube\.com/@([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_video_details(self, video_id: str, extended: bool = False) -> Optional[Dict]:
        """
        Récupère les détails d'une vidéo YouTube.
        
        Args:
            video_id (str): ID de la vidéo
            extended (bool): Si True, récupère des informations étendues
        
        Returns:
            dict: Informations de la vidéo ou None si erreur
        """
        try:
            # Parties de base
            parts = ['snippet', 'statistics', 'contentDetails']
            
            # Parties étendues si demandées
            if extended:
                parts.extend(['status', 'topicDetails', 'recordingDetails', 'liveStreamingDetails'])
            
            request = self.youtube.videos().list(
                part=','.join(parts),
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                logger.warning(f"Aucune vidéo trouvée pour l'ID: {video_id}")
                return None
            
            video = response['items'][0]
            
            # Formatage des données de base
            video_data = {
                'video_id': video_id,
                'title': video['snippet']['title'],
                'description': video['snippet']['description'],
                'duration': video['contentDetails']['duration'],
                'published_at': video['snippet']['publishedAt'],
                'channel_id': video['snippet']['channelId'],
                'channel_title': video['snippet']['channelTitle'],
                'view_count': int(video['statistics'].get('viewCount', 0)),
                'like_count': int(video['statistics'].get('likeCount', 0)),
                'comment_count': int(video['statistics'].get('commentCount', 0)),
                'tags': json.dumps(video['snippet'].get('tags', [])),
                'category_id': video['snippet'].get('categoryId', ''),
                'language': video['snippet'].get('defaultLanguage', ''),
                'thumbnail_url': video['snippet']['thumbnails'].get('high', {}).get('url', '')
            }
            
            # Ajout des données étendues si demandées
            if extended:
                # Informations de contenu détaillées
                content_details = video.get('contentDetails', {})
                video_data.update({
                    'definition': content_details.get('definition', ''),  # hd, sd
                    'caption': content_details.get('caption', ''),  # true/false
                    'licensed_content': content_details.get('licensedContent', False),
                    'dimension': content_details.get('dimension', ''),  # 2d, 3d
                    'projection': content_details.get('projection', '')  # rectangular, 360
                })
                
                # Statut de la vidéo
                status = video.get('status', {})
                video_data.update({
                    'privacy_status': status.get('privacyStatus', ''),  # public, private, unlisted
                    'upload_status': status.get('uploadStatus', ''),  # processed, uploaded, etc.
                    'license': status.get('license', ''),  # youtube, creativeCommon
                    'embeddable': status.get('embeddable', True),
                    'public_stats_viewable': status.get('publicStatsViewable', True)
                })
                
                # Sujets/Topics
                topic_details = video.get('topicDetails', {})
                video_data.update({
                    'topic_categories': json.dumps(topic_details.get('topicCategories', [])),
                    'relevant_topic_ids': json.dumps(topic_details.get('relevantTopicIds', []))
                })
                
                # Informations de diffusion en direct
                live_streaming = video.get('liveStreamingDetails', {})
                if live_streaming:
                    video_data.update({
                        'actual_start_time': live_streaming.get('actualStartTime', ''),
                        'actual_end_time': live_streaming.get('actualEndTime', ''),
                        'scheduled_start_time': live_streaming.get('scheduledStartTime', ''),
                        'concurrent_viewers': live_streaming.get('concurrentViewers', 0)
                    })
                
                # Informations d'enregistrement
                recording_details = video.get('recordingDetails', {})
                if recording_details:
                    video_data.update({
                        'recording_date': recording_details.get('recordingDate', ''),
                        'location_description': recording_details.get('locationDescription', '')
                    })
                
                # Informations supplémentaires du snippet
                snippet = video['snippet']
                video_data.update({
                    'default_audio_language': snippet.get('defaultAudioLanguage', ''),
                    'live_broadcast_content': snippet.get('liveBroadcastContent', 'none'),
                    'thumbnails_standard': snippet['thumbnails'].get('standard', {}).get('url', ''),
                    'thumbnails_maxres': snippet['thumbnails'].get('maxres', {}).get('url', '')
                })
            
            logger.info(f"Détails {'étendus ' if extended else ''}récupérés pour la vidéo: {video_data['title']}")
            return video_data
        
        except HttpError as e:
            logger.error(f"Erreur HTTP lors de la récupération de la vidéo {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vidéo {video_id}: {str(e)}")
            return None
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'une chaîne YouTube.
        
        Args:
            channel_id (str): ID de la chaîne
        
        Returns:
            dict: Informations de la chaîne ou None si erreur
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                logger.warning(f"Aucune chaîne trouvée pour l'ID: {channel_id}")
                return None
            
            channel = response['items'][0]
            
            # Formatage des données
            channel_data = {
                'channel_id': channel_id,
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                'video_count': int(channel['statistics'].get('videoCount', 0)),
                'view_count': int(channel['statistics'].get('viewCount', 0)),
                'published_at': channel['snippet']['publishedAt'],
                'thumbnail_url': channel['snippet']['thumbnails'].get('high', {}).get('url', ''),
                'country': channel['snippet'].get('country', '')
            }
            
            logger.info(f"Détails récupérés pour la chaîne: {channel_data['title']}")
            return channel_data
        
        except HttpError as e:
            logger.error(f"Erreur HTTP lors de la récupération de la chaîne {channel_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la chaîne {channel_id}: {str(e)}")
            return None
    
    def get_playlist_details(self, playlist_id: str) -> Optional[Dict]:
        """
        Récupère les détails d'une playlist YouTube.
        
        Args:
            playlist_id (str): ID de la playlist
        
        Returns:
            dict: Informations de la playlist ou None si erreur
        """
        try:
            request = self.youtube.playlists().list(
                part='snippet,contentDetails',
                id=playlist_id
            )
            response = request.execute()
            
            if not response['items']:
                logger.warning(f"Aucune playlist trouvée pour l'ID: {playlist_id}")
                return None
            
            playlist = response['items'][0]
            
            # Formatage des données
            playlist_data = {
                'playlist_id': playlist_id,
                'title': playlist['snippet']['title'],
                'description': playlist['snippet']['description'],
                'channel_id': playlist['snippet']['channelId'],
                'channel_title': playlist['snippet']['channelTitle'],
                'item_count': playlist['contentDetails']['itemCount'],
                'published_at': playlist['snippet']['publishedAt'],
                'thumbnail_url': playlist['snippet']['thumbnails'].get('high', {}).get('url', '')
            }
            
            logger.info(f"Détails récupérés pour la playlist: {playlist_data['title']}")
            return playlist_data
        
        except HttpError as e:
            logger.error(f"Erreur HTTP lors de la récupération de la playlist {playlist_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la playlist {playlist_id}: {str(e)}")
            return None
    
    def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> List[str]:
        """
        Récupère la liste des IDs de vidéos d'une playlist.
        
        Args:
            playlist_id (str): ID de la playlist
            max_results (int): Nombre maximum de résultats
        
        Returns:
            list: Liste des IDs de vidéos
        """
        video_ids = []
        next_page_token = None
        
        try:
            while len(video_ids) < max_results:
                request = self.youtube.playlistItems().list(
                    part='contentDetails',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response['items']:
                    video_ids.append(item['contentDetails']['videoId'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Récupéré {len(video_ids)} vidéos de la playlist {playlist_id}")
            return video_ids
        
        except HttpError as e:
            logger.error(f"Erreur HTTP lors de la récupération des vidéos de la playlist {playlist_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des vidéos de la playlist {playlist_id}: {str(e)}")
            return []
    
    def test_api_key(self) -> bool:
        """
        Teste la validité de la clé API.
        
        Returns:
            bool: True si la clé API est valide, False sinon
        """
        try:
            request = self.youtube.videos().list(
                part='snippet',
                id='dQw4w9WgXcQ',  # Never Gonna Give You Up - Rick Astley
                maxResults=1
            )
            response = request.execute()
            logger.info("Clé API YouTube valide")
            return True
        
        except HttpError as e:
            logger.error(f"Clé API YouTube invalide: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du test de la clé API: {str(e)}")
            return False