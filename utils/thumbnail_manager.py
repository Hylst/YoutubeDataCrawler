#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module de gestion des thumbnails YouTube

Ce module gère le téléchargement, l'affichage et l'ajout de métadonnées
IPTC/XMP aux thumbnails des vidéos YouTube.
"""

import os
import re
import requests
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
from iptcinfo3 import IPTCInfo
import json

# Configuration du logging
logger = logging.getLogger(__name__)


class ThumbnailManager:
    """
    Gestionnaire pour les thumbnails YouTube avec métadonnées IPTC/XMP.
    """
    
    def __init__(self, download_dir: str = "thumbnails"):
        """
        Initialise le gestionnaire de thumbnails.
        
        Args:
            download_dir (str): Répertoire de téléchargement des thumbnails
        """
        self.download_dir = download_dir
        self.ensure_download_dir()
    
    def ensure_download_dir(self):
        """Crée le répertoire de téléchargement s'il n'existe pas."""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            logger.info(f"Répertoire de thumbnails créé: {self.download_dir}")
    
    def slugify_title(self, title: str) -> str:
        """
        Convertit un titre de vidéo en nom de fichier valide.
        
        Args:
            title (str): Titre de la vidéo
        
        Returns:
            str: Titre slugifié
        """
        # Suppression des caractères spéciaux
        slug = re.sub(r'[^\w\s-]', '', title)
        # Remplacement des espaces par des tirets
        slug = re.sub(r'[-\s]+', '-', slug)
        # Suppression des tirets en début/fin
        slug = slug.strip('-')
        # Limitation de la longueur
        slug = slug[:100]
        
        return slug.lower()
    
    def get_thumbnail_urls(self, video_data: Dict) -> Dict[str, str]:
        """
        Extrait toutes les URLs de thumbnails disponibles.
        
        Args:
            video_data (dict): Données de la vidéo
        
        Returns:
            dict: URLs des thumbnails par qualité
        """
        thumbnails = {}
        
        # URL principale (high quality)
        if 'thumbnail_url' in video_data and video_data['thumbnail_url']:
            thumbnails['high'] = video_data['thumbnail_url']
        
        # URLs étendues si disponibles
        if 'thumbnails_standard' in video_data and video_data['thumbnails_standard']:
            thumbnails['standard'] = video_data['thumbnails_standard']
        
        if 'thumbnails_maxres' in video_data and video_data['thumbnails_maxres']:
            thumbnails['maxres'] = video_data['thumbnails_maxres']
        
        # URLs par défaut basées sur l'ID vidéo
        video_id = video_data.get('video_id', '')
        if video_id:
            thumbnails.update({
                'default': f"https://img.youtube.com/vi/{video_id}/default.jpg",
                'medium': f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                'high_fallback': f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                'standard_fallback': f"https://img.youtube.com/vi/{video_id}/sddefault.jpg",
                'maxres_fallback': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            })
        
        return thumbnails
    
    def download_thumbnail(self, url: str, filename: str) -> Optional[str]:
        """
        Télécharge un thumbnail depuis une URL.
        
        Args:
            url (str): URL du thumbnail
            filename (str): Nom du fichier de destination
        
        Returns:
            str: Chemin du fichier téléchargé ou None si erreur
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            filepath = os.path.join(self.download_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Thumbnail téléchargé: {filepath}")
            return filepath
        
        except requests.RequestException as e:
            logger.error(f"Erreur lors du téléchargement de {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du téléchargement: {str(e)}")
            return None
    
    def add_iptc_metadata(self, image_path: str, video_data: Dict) -> bool:
        """
        Ajoute les métadonnées IPTC à l'image.
        
        Args:
            image_path (str): Chemin de l'image
            video_data (dict): Données de la vidéo
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Création de l'objet IPTC
            info = IPTCInfo(image_path, force=True)
            
            # Métadonnées de base
            info['headline'] = video_data.get('title', '')[:64]  # Limitation IPTC
            info['caption/abstract'] = video_data.get('description', '')[:2000]
            info['keywords'] = self.extract_keywords(video_data)
            info['byline'] = video_data.get('channel_title', '')
            info['credit'] = 'YouTube'
            info['source'] = 'YouTube API'
            info['copyright notice'] = f"© {video_data.get('channel_title', 'Unknown')}"
            
            # Dates
            if 'published_at' in video_data:
                try:
                    pub_date = datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00'))
                    info['date created'] = pub_date.strftime('%Y%m%d')
                except:
                    pass
            
            # Catégorie
            if 'category_id' in video_data:
                info['category'] = f"YouTube Category {video_data['category_id']}"
            
            # Langue
            if 'language' in video_data and video_data['language']:
                info['language identifier'] = video_data['language']
            
            # Statistiques dans les mots-clés spéciaux
            stats_keywords = []
            if 'view_count' in video_data:
                stats_keywords.append(f"views:{video_data['view_count']}")
            if 'like_count' in video_data:
                stats_keywords.append(f"likes:{video_data['like_count']}")
            if 'comment_count' in video_data:
                stats_keywords.append(f"comments:{video_data['comment_count']}")
            
            if stats_keywords:
                existing_keywords = info['keywords'] or []
                info['keywords'] = existing_keywords + stats_keywords
            
            # Sauvegarde
            info.save()
            logger.info(f"Métadonnées IPTC ajoutées à {image_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des métadonnées IPTC: {str(e)}")
            return False
    
    def extract_keywords(self, video_data: Dict) -> list:
        """
        Extrait les mots-clés depuis les données de la vidéo.
        
        Args:
            video_data (dict): Données de la vidéo
        
        Returns:
            list: Liste des mots-clés
        """
        keywords = []
        
        # Tags de la vidéo
        if 'tags' in video_data and video_data['tags']:
            try:
                tags = json.loads(video_data['tags']) if isinstance(video_data['tags'], str) else video_data['tags']
                if isinstance(tags, list):
                    keywords.extend(tags[:20])  # Limitation à 20 tags
            except:
                pass
        
        # Ajout d'informations contextuelles
        keywords.append('YouTube')
        keywords.append('Video Thumbnail')
        
        if 'channel_title' in video_data:
            keywords.append(f"Channel:{video_data['channel_title']}")
        
        if 'video_id' in video_data:
            keywords.append(f"ID:{video_data['video_id']}")
        
        return keywords[:32]  # Limitation IPTC
    
    def create_xmp_sidecar(self, image_path: str, video_data: Dict) -> bool:
        """
        Crée un fichier XMP sidecar avec les métadonnées étendues.
        
        Args:
            image_path (str): Chemin de l'image
            video_data (dict): Données de la vidéo
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            xmp_path = os.path.splitext(image_path)[0] + '.xmp'
            
            # Template XMP
            xmp_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:youtube="http://youtube.com/ns/1.0/">
   
   <!-- Métadonnées Dublin Core -->
   <dc:title>{self.escape_xml(video_data.get('title', ''))}</dc:title>
   <dc:description>{self.escape_xml(video_data.get('description', '')[:1000])}</dc:description>
   <dc:creator>{self.escape_xml(video_data.get('channel_title', ''))}</dc:creator>
   <dc:source>YouTube</dc:source>
   <dc:rights>© {self.escape_xml(video_data.get('channel_title', 'Unknown'))}</dc:rights>
   
   <!-- Métadonnées XMP -->
   <xmp:CreateDate>{video_data.get('published_at', '')}</xmp:CreateDate>
   <xmp:ModifyDate>{datetime.now().isoformat()}</xmp:ModifyDate>
   
   <!-- Métadonnées YouTube spécifiques -->
   <youtube:videoId>{video_data.get('video_id', '')}</youtube:videoId>
   <youtube:channelId>{video_data.get('channel_id', '')}</youtube:channelId>
   <youtube:duration>{video_data.get('duration', '')}</youtube:duration>
   <youtube:viewCount>{video_data.get('view_count', 0)}</youtube:viewCount>
   <youtube:likeCount>{video_data.get('like_count', 0)}</youtube:likeCount>
   <youtube:commentCount>{video_data.get('comment_count', 0)}</youtube:commentCount>
   <youtube:categoryId>{video_data.get('category_id', '')}</youtube:categoryId>
   <youtube:language>{video_data.get('language', '')}</youtube:language>
   
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>'''
            
            with open(xmp_path, 'w', encoding='utf-8') as f:
                f.write(xmp_content)
            
            logger.info(f"Fichier XMP créé: {xmp_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du fichier XMP: {str(e)}")
            return False
    
    def escape_xml(self, text: str) -> str:
        """
        Échappe les caractères spéciaux XML.
        
        Args:
            text (str): Texte à échapper
        
        Returns:
            str: Texte échappé
        """
        if not text:
            return ''
        
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&apos;'))
    
    def download_and_process_thumbnail(self, video_data: Dict, quality: str = 'maxres') -> Optional[Tuple[str, str]]:
        """
        Télécharge et traite un thumbnail avec métadonnées.
        
        Args:
            video_data (dict): Données de la vidéo
            quality (str): Qualité du thumbnail ('high', 'maxres', 'standard')
        
        Returns:
            tuple: (chemin_image, chemin_xmp) ou None si erreur
        """
        try:
            # Génération du nom de fichier
            title_slug = self.slugify_title(video_data.get('title', 'unknown'))
            video_id = video_data.get('video_id', 'unknown')
            filename = f"{title_slug}_{video_id}_{quality}.jpg"
            
            # Récupération des URLs
            thumbnail_urls = self.get_thumbnail_urls(video_data)
            
            # Sélection de l'URL selon la qualité demandée (priorité aux hautes résolutions)
            url = None
            if quality in thumbnail_urls:
                url = thumbnail_urls[quality]
            elif f"{quality}_fallback" in thumbnail_urls:
                url = thumbnail_urls[f"{quality}_fallback"]
            elif 'maxres_fallback' in thumbnail_urls:
                url = thumbnail_urls['maxres_fallback']
            elif 'standard_fallback' in thumbnail_urls:
                url = thumbnail_urls['standard_fallback']
            elif 'high' in thumbnail_urls:
                url = thumbnail_urls['high']
            elif thumbnail_urls:
                url = list(thumbnail_urls.values())[0]
            
            if not url:
                logger.error("Aucune URL de thumbnail disponible")
                return None
            
            # Téléchargement
            image_path = self.download_thumbnail(url, filename)
            if not image_path:
                return None
            
            # Ajout des métadonnées IPTC
            self.add_iptc_metadata(image_path, video_data)
            
            # Création du fichier XMP
            xmp_created = self.create_xmp_sidecar(image_path, video_data)
            xmp_path = os.path.splitext(image_path)[0] + '.xmp' if xmp_created else None
            
            logger.info(f"Thumbnail traité avec succès: {image_path}")
            return (image_path, xmp_path)
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du thumbnail: {str(e)}")
            return None
    
    def get_thumbnail_info(self, image_path: str) -> Dict:
        """
        Récupère les informations d'un thumbnail.
        
        Args:
            image_path (str): Chemin de l'image
        
        Returns:
            dict: Informations de l'image
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'path': image_path,
                    'size': img.size,
                    'format': img.format,
                    'mode': img.mode,
                    'file_size': os.path.getsize(image_path)
                }
                
                # Métadonnées EXIF si disponibles
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    info['exif'] = {TAGS.get(k, k): v for k, v in exif.items()}
                
                return info
        
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des informations: {str(e)}")
            return {'path': image_path, 'error': str(e)}