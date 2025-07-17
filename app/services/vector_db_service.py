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
                CREATE TABLE IF NOT EXISTS video_embeddings (
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
            self._insert_video_embeddings(cursor, video_id, video_segments)
            conn.commit()
            print(f"Stored video and {len(video_segments)} embeddings.")

        except Exception as e:
            print("Error storing embedding:", e)
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

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

    def _insert_video_embeddings(self, cursor, video_id: int, segments: list[dict]):
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
            INSERT INTO video_embeddings (
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
        self, embedding, page_limit=None, min_similarity=None
    ) -> list[dict[str, Any]]:
        page_limit = page_limit or self.default_page_limit
        min_similarity = min_similarity or self.default_min_similarity

        try:
            conn = self.get_connection()

            query = """
                SELECT
                    id,
                    source,
                    modality,
                    scope,
                    start_time,
                    end_time,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM video_embeddings
                WHERE (1 - (embedding <=> %s::vector)) > %s
                ORDER BY similarity DESC
                LIMIT %s;
            """
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (embedding, embedding, min_similarity, page_limit))
                results = cur.fetchall()

            conn.close()
            return results

        except Exception as e:
            print(f"Error searching database: {e}")
            raise e

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
                        source,
                        modality,
                        scope,
                        start_time,
                        end_time,
                        1 - (embedding <=> %s::vector) AS similarity,
                        {i} AS query_index
                    FROM video_embeddings
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
