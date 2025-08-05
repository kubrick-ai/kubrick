BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

-- Function to update `updated_at` on row update
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS videos (
  id SERIAL PRIMARY KEY,
  filename TEXT NOT NULL,
  s3_bucket TEXT NOT NULL,
  s3_key TEXT NOT NULL,
  duration REAL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  height INTEGER,
  width INTEGER
);

CREATE UNIQUE INDEX unique_s3_object ON videos (s3_bucket, s3_key);

-- Trigger for videos
DROP TRIGGER IF EXISTS trg_update_videos_updated_at ON videos;
CREATE TRIGGER trg_update_videos_updated_at
BEFORE UPDATE ON videos
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TABLE IF NOT EXISTS video_segments (
  id SERIAL PRIMARY KEY,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  modality TEXT NOT NULL,
  scope TEXT NOT NULL,
  start_time REAL NOT NULL,
  end_time REAL NOT NULL,
  embedding vector(1024)
);

CREATE INDEX IF NOT EXISTS video_segments_embedding_ann_idx
  ON video_segments
  USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  sqs_message_id TEXT,
  s3_bucket TEXT NOT NULL,
  s3_key TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  status TEXT NOT NULL
);

-- Trigger for tasks
DROP TRIGGER IF EXISTS trg_update_tasks_updated_at ON tasks;
CREATE TRIGGER trg_update_tasks_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;
