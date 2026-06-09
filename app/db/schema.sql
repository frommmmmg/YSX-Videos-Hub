CREATE TABLE IF NOT EXISTS source_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT,
    file_size INTEGER,
    duration REAL,
    width INTEGER,
    height INTEGER,
    resolution TEXT,
    fps REAL,
    codec TEXT,
    bitrate INTEGER,
    orientation TEXT,
    has_audio INTEGER DEFAULT 0,
    imported_at TEXT,
    status TEXT DEFAULT 'active',
    note TEXT
);

CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_video_id INTEGER NOT NULL,
    clip_path TEXT NOT NULL,
    thumbnail_path TEXT,
    source_start_time REAL NOT NULL,
    source_end_time REAL NOT NULL,
    clip_duration REAL,
    scene_group_id TEXT,
    prev_clip_id INTEGER,
    next_clip_id INTEGER,
    description TEXT,
    quality_score REAL DEFAULT 0,
    status TEXT DEFAULT 'active',
    favorite INTEGER DEFAULT 0,
    used_count INTEGER DEFAULT 0,
    last_used_at TEXT,
    note TEXT,
    created_at TEXT,
    FOREIGN KEY (source_video_id) REFERENCES source_videos(id)
);

CREATE TABLE IF NOT EXISTS clip_keyframes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER NOT NULL,
    frame_order INTEGER NOT NULL,
    frame_role TEXT,
    frame_time_in_clip REAL,
    frame_time_in_source REAL,
    frame_path TEXT NOT NULL,
    FOREIGN KEY (clip_id) REFERENCES clips(id)
);

CREATE TABLE IF NOT EXISTS clip_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER NOT NULL,
    tag_type TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (clip_id) REFERENCES clips(id)
);

CREATE TABLE IF NOT EXISTS clip_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER NOT NULL,
    source_video_id INTEGER NOT NULL,
    export_path TEXT NOT NULL,
    export_start_time REAL NOT NULL,
    export_end_time REAL NOT NULL,
    export_duration REAL,
    export_type TEXT,
    created_at TEXT,
    FOREIGN KEY (clip_id) REFERENCES clips(id),
    FOREIGN KEY (source_video_id) REFERENCES source_videos(id)
);

CREATE INDEX IF NOT EXISTS idx_source_videos_hash ON source_videos(file_hash);
CREATE INDEX IF NOT EXISTS idx_clips_source_video_id ON clips(source_video_id);
CREATE INDEX IF NOT EXISTS idx_clips_start_time ON clips(source_start_time);
CREATE INDEX IF NOT EXISTS idx_clips_duration ON clips(clip_duration);
CREATE INDEX IF NOT EXISTS idx_clips_status ON clips(status);
CREATE INDEX IF NOT EXISTS idx_clips_favorite ON clips(favorite);
CREATE INDEX IF NOT EXISTS idx_clip_tags_type_value ON clip_tags(tag_type, tag_value);
CREATE INDEX IF NOT EXISTS idx_clip_tags_value ON clip_tags(tag_value);
CREATE INDEX IF NOT EXISTS idx_keyframes_clip_id ON clip_keyframes(clip_id);
