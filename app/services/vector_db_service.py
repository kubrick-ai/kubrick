from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config import Config


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
                CREATE TABLE IF NOT EXISTS video_embeddings (
                    id SERIAL PRIMARY KEY,
                    source TEXT NOT NULL,
                    type TEXT NOT NULL,
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

    def store(
        self, video_filepath, embedding_type, scope, start_time, end_time, embedding
    ):
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO video_embeddings (
                    source,
                    type,
                    scope,
                    start_time,
                    end_time,
                    embedding
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    video_filepath,
                    embedding_type,
                    scope,
                    start_time,
                    end_time,
                    embedding,
                ),
            )
            conn.commit()

        except Exception as e:
            print("Error storing embedding:", e)

        finally:
            cursor.close()
            conn.close()

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
                    type,
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
                        type,
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
