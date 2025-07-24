from typing import Any
import os
import time

from logging import getLogger
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection

DEFAULT_PAGE_LIMIT = os.getenv("DEFAULT_PAGE_LIMIT", 10)
DEFAULT_MIN_SIMILARITY = os.getenv("DEFAULT_MIN_SIMILARITY", 0.2)


class VectorDBService:
    def __init__(
        self,
        db_params,
        page_limit=DEFAULT_PAGE_LIMIT,
        min_similarity=DEFAULT_MIN_SIMILARITY,
        logger=getLogger(),
    ):
        self.db_params = db_params
        self.default_page_limit = page_limit
        self.default_min_similarity = min_similarity
        self.logger = logger
        self.conn = self.get_connection()

    def get_connection(self, max_retries=3) -> connection:
        attempt = 0
        while True:
            try:
                self.logger.info("Connecting to database...")
                return psycopg2.connect(**self.db_params)
            except psycopg2.OperationalError as e:
                attempt += 1
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"Failed to connect to database after {attempt + 1} attempts: {e}"
                    )
                    raise
                self.logger.warning(
                    f"Database connection attempt {attempt + 1} failed. Retrying..."
                )
                time.sleep(2**attempt)

    def fetch_videos(self, page, limit):
        # Assumes page is 0-indexed
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                offset = page * limit
                query = """
                    SELECT *
                    FROM videos
                    LIMIT %s
                    OFFSET %s
                    """
                cursor.execute(query, (limit, offset))
                raw_results = cursor.fetchall()

            return [
                {
                    "id": video["id"],
                    "s3_bucket": video["s3_bucket"],
                    "s3_key": video["s3_key"],
                    "filename": video["filename"],
                    "duration": video["duration"],
                    "created_at": video["created_at"],
                    "updated_at": video["updated_at"],
                    "height": video["height"],
                    "width": video["width"],
                }
                for video in raw_results
            ]

        except Exception as e:
            self.logger.error(f"Error searching video in database: {e}")
            raise e

    def store(self, video_metadata, video_segments):
        with self.conn.cursor() as cursor:
            try:
                video_id = self._insert_video(video_metadata)
                self._insert_video_segments(cursor, video_id, video_segments)
                self.conn.commit()
                self.logger.info(f"Stored video and {len(video_segments)} embeddings.")

            except Exception as e:
                self.logger.error("Error storing embedding:", e)
                self.conn.rollback()

            finally:
                cursor.close()

    def _insert_video(self, metadata: dict) -> int:
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                INSERT INTO videos (s3_bucket, s3_key, filename, duration, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING id
                """,
                (
                    metadata["s3_bucket"],
                    metadata["s3_key"],
                    metadata["filename"],
                    metadata["duration"],
                ),
            )
            result = cursor.fetchone()
            if result is None:
                raise Exception(f"Error during process of storing video: {metadata}")
            return result["id"]

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
            """
            SELECT
                videos.id AS video_id,
                videos.s3_bucket,
                videos.s3_key,
                videos.filename,
                videos.duration,
                videos.created_at,
                videos.updated_at,
                videos.height,
                videos.width,
                video_segments.id AS segment_id,
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
            query_parts.append("AND scope = %s")
            query_params.append(filter["scope"])
        if filter and "modality" in filter:
            query_parts.append("AND modality = %s")
            query_params.append(filter["modality"])

        query_parts.append("ORDER BY similarity DESC LIMIT %s")
        query_params.append(page_limit)

        try:
            conn = self.get_connection()
            query = "\n".join(query_parts)

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, query_params)
                results = cursor.fetchall()

            conn.close()
            return self._normalize_find_similar_results(results)

        except Exception as e:
            self.logger.error(f"Error searching database: {e}")
            raise e

    def find_similar_batch(
        self, embeddings, filter=None, page_limit=None, min_similarity=None
    ) -> list[dict[str, Any]]:
        page_limit = page_limit or self.default_page_limit
        min_similarity = min_similarity or self.default_min_similarity

        try:
            conn = self.get_connection()

            query_parts = []
            query_params = []

            for i, embedding in enumerate(embeddings):
                sub_query = f"""
                    SELECT
                        videos.id AS video_id,
                        videos.s3_bucket,
                        videos.s3_key,
                        videos.filename,
                        videos.duration,
                        videos.created_at,
                        videos.updated_at,
                        videos.height,
                        videos.width,
                        video_segments.id AS segment_id,
                        video_segments.modality,
                        video_segments.scope,
                        video_segments.start_time,
                        video_segments.end_time,
                        1 - (video_segments.embedding <=> %s::vector) AS similarity,
                        {i} AS query_index
                    FROM videos
                    INNER JOIN video_segments ON videos.id = video_segments.video_id
                    WHERE (1 - (video_segments.embedding <=> %s::vector)) > %s
                """
                query_params.extend([embedding, embedding, min_similarity])

                if filter:
                    if "scope" in filter:
                        sub_query += "\nAND scope = %s"
                        query_params.append(filter["scope"])
                    if "modality" in filter:
                        sub_query += "\nAND modality = %s"
                        query_params.append(filter["modality"])
                query_parts.append(sub_query)

            full_query = f"""
                WITH combined_results AS (
                    {" UNION ALL ".join(query_parts)}
                )
                SELECT * FROM combined_results
                ORDER BY similarity DESC
                LIMIT %s;
            """
            query_params.append(page_limit)

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(full_query, query_params)
                results = cursor.fetchall()

            conn.close()
            return self._normalize_find_similar_results(results)

        except Exception as e:
            self.logger.error(f"Error searching database with batch: {e}")
            raise e

    def _normalize_find_similar_results(self, raw_results):
        return [
            {
                "id": raw_result["segment_id"],
                "modality": raw_result["modality"],
                "scope": raw_result["scope"],
                "start_time": raw_result["start_time"],
                "end_time": raw_result["end_time"],
                "similarity": raw_result["similarity"],
                "video": {
                    "id": raw_result["video_id"],
                    "s3_bucket": raw_result["s3_bucket"],
                    "s3_key": raw_result["s3_key"],
                    "filename": raw_result["filename"],
                    "duration": raw_result["duration"],
                    "created_at": raw_result["created_at"],
                    "updated_at": raw_result["updated_at"],
                    "height": raw_result["height"],
                    "width": raw_result["width"],
                },
            }
            for raw_result in raw_results
        ]
