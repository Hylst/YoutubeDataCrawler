-- Schema de base de données pour YouTube Data Analyzer
-- SQLite3 Database Schema

-- Table pour stocker les informations des vidéos
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration TEXT,
    published_at DATETIME,
    channel_id TEXT,
    channel_title TEXT,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    tags TEXT, -- JSON array as string
    category_id TEXT,
    language TEXT,
    thumbnail_url TEXT,
    
    -- Extended video information
    definition TEXT, -- hd, sd
    caption TEXT, -- true, false
    licensed_content BOOLEAN DEFAULT 0,
    dimension TEXT, -- 2d, 3d
    projection TEXT, -- rectangular, 360
    privacy_status TEXT, -- public, private, unlisted
    upload_status TEXT, -- processed, uploaded, etc.
    license TEXT, -- youtube, creativeCommon
    embeddable BOOLEAN DEFAULT 1,
    public_stats_viewable BOOLEAN DEFAULT 1,
    topic_categories TEXT, -- JSON array as string
    relevant_topic_ids TEXT, -- JSON array as string
    default_audio_language TEXT,
    live_broadcast_content TEXT, -- live, none, upcoming
    thumbnails_standard TEXT,
    thumbnails_maxres TEXT,
    
    -- Live streaming details
    actual_start_time DATETIME,
    actual_end_time DATETIME,
    scheduled_start_time DATETIME,
    concurrent_viewers INTEGER DEFAULT 0,
    
    -- Recording details
    recording_date DATETIME,
    location_description TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les informations des chaînes
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    subscriber_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    published_at DATETIME,
    thumbnail_url TEXT,
    country TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les informations des playlists
CREATE TABLE IF NOT EXISTS playlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    channel_id TEXT,
    channel_title TEXT,
    item_count INTEGER DEFAULT 0,
    published_at DATETIME,
    thumbnail_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les clés API
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL, -- 'youtube', 'openai', 'claude', etc.
    api_key TEXT NOT NULL,
    model_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les presets
CREATE TABLE IF NOT EXISTS presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    content_type TEXT, -- 'video', 'playlist', 'channel'
    filters TEXT, -- JSON object as string
    llm_model TEXT,
    image_model TEXT,
    export_format TEXT,
    ui_template TEXT,
    is_default BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker l'historique des exports
CREATE TABLE IF NOT EXISTS exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_type TEXT NOT NULL, -- 'json', 'markdown', 'text', 'database'
    file_path TEXT,
    preset_id INTEGER,
    item_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);

-- Table pour stocker les relations playlist-vidéo
CREATE TABLE IF NOT EXISTS playlist_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    playlist_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    position INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(playlist_id, video_id)
);

-- Index pour améliorer les performances
CREATE INDEX IF NOT EXISTS idx_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at);
CREATE INDEX IF NOT EXISTS idx_channels_channel_id ON channels(channel_id);
CREATE INDEX IF NOT EXISTS idx_playlists_channel_id ON playlists(channel_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_provider ON api_keys(provider);
CREATE INDEX IF NOT EXISTS idx_presets_content_type ON presets(content_type);