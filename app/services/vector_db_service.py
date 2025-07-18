from typing import Any

import psycopg2
from app.config import Config
from psycopg2.extras import RealDictCursor


class VectorDBService:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.db_params = self.config.DB_PARAMS
        self.default_page_limit = self.config.DEFAULT_PAGE_LIMIT
        self.default_min_similarity = self.config.DEFAULT_MIN_SIMILARITY

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

    def setup(self):
        conn = self.get_connection()
        cur = conn.cursor()

        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    url TEXT,
                    filename TEXT,
                    duration REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    height INTEGER NOT NULL,
                    width INTEGER NOT NULL
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS video_segments (
                    id SERIAL PRIMARY KEY,
                    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
                    modality TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    embedding vector(1024)
                );
                """
            )
            conn.commit()
            print("Database setup complete!")
        except Exception as e:
            print("Error during setup:", e)
        finally:
            cur.close()
            conn.close()

    def store(self, video_metadata, video_segments):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            video_id = self._insert_video(cursor, video_metadata)
            self._insert_video_segments(cursor, video_id, video_segments)
            conn.commit()
            print(f"Stored video and {len(video_segments)} embeddings.")

        except Exception as e:
            print("Error storing embedding:", e)
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

    def fetch_videos(self, page, limit):
        conn = self.get_connection()
        params = [limit, page]

        try:
            query = f"""
                SELECT * 
                FROM videos 
                LIMIT %s 
                OFFSET %s
            """

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()

            conn.close()
            return results

        except Exception as e:
            print(f"Error searching database with batch: {e}")
            raise e

    def _insert_video(self, cursor, metadata: dict) -> int:
        cursor.execute(
            """
            INSERT INTO videos (title, url, filename, duration, height, width, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """,
            (
                metadata.get("title"),
                metadata["url"],
                metadata["filename"],
                metadata["duration"],
                metadata["height"],
                metadata["width"],
            ),
        )
        return cursor.fetchone()[0]

    def _insert_video_segments(self, cursor, video_id: int, segments: list[dict]):
        data_to_insert = [
            (
                video_id,
                segment["modality"],
                segment["scope"],
                segment["start_time"],
                segment["end_time"],
                segment["embedding"],
            )
            for segment in segments
        ]

        cursor.executemany(
            """
            INSERT INTO video_segments (
                video_id,
                modality,
                scope,
                start_time,
                end_time,
                embedding
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            data_to_insert,
        )

    def find_similar(
        self,
        embedding,
        filter=None,
        page_limit=None,
        min_similarity=None,
    ) -> list[dict[str, Any]]:
        page_limit = page_limit or self.default_page_limit
        min_similarity = min_similarity or self.default_min_similarity

        query_parts = []
        query_params = []

        query_parts.append(
            f"""
            SELECT
                videos.id,
                videos.title,
                videos.url,
                videos.filename,
                videos.duration,
                videos.created_at,
                videos.updated_at,
                videos.height,
                videos.width,
                video_segments.id,
                video_segments.modality,
                video_segments.scope,
                video_segments.start_time,
                video_segments.end_time,
                1 - (video_segments.embedding <=> %s::vector) AS similarity
            FROM videos
            INNER JOIN video_segments ON videos.id = video_segments.video_id
            WHERE (1 - (video_segments.embedding <=> %s::vector)) > %s
            """
        )
        query_params.extend([embedding, embedding, min_similarity])

        if filter and "scope" in filter:
            query_parts.append(f"AND scope = %s")
            query_params.append(filter["scope"])
        if filter and "modality" in filter:
            query_parts.append(f"AND modality = %s")
            query_params.append(filter["modality"])

        query_parts.append("ORDER BY similarity DESC LIMIT %s")
        query_params.append(page_limit)

        try:
            conn = self.get_connection()
            query = "\n".join(query_parts)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, query_params)
                results = cur.fetchall()

            conn.close()
            return results

        except Exception as e:
            print(f"Error searching database: {e}")
            raise e

    # TODO: This function has to return the same data as find_similar
    def find_similar_batch(
        self, embeddings, page_limit=None, min_similarity=None
    ) -> list[dict[str, Any]]:
        page_limit = page_limit or self.default_page_limit
        min_similarity = min_similarity or self.default_min_similarity

        try:
            conn = self.get_connection()

            query_parts = []
            params = []

            for i, embedding in enumerate(embeddings):
                query_parts.append(
                    f"""
                    SELECT
                        id,
                        video_id,
                        modality,
                        scope,
                        start_time,
                        end_time,
                        1 - (embedding <=> %s::vector) AS similarity,
                        {i} AS query_index
                    FROM video_segments
                    WHERE (1 - (embedding <=> %s::vector)) > %s
                """
                )
                params.extend([embedding, embedding, min_similarity])

            full_query = f"""
                WITH combined_results AS (
                    {" UNION ALL ".join(query_parts)}
                )
                SELECT * FROM combined_results
                ORDER BY similarity DESC
                LIMIT %s;
            """
            params.append(page_limit)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(full_query, params)
                results = cur.fetchall()

            conn.close()
            return results

        except Exception as e:
            print(f"Error searching database with batch: {e}")
            raise e
