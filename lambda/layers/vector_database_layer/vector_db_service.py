import os
import time
import psycopg2
from logging import getLogger
from typing import Any, NamedTuple
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection


class PaginatedResult(NamedTuple):
    items: list[dict[str, Any]]
    total: int


DEFAULT_PAGE_LIMIT = os.getenv("DEFAULT_PAGE_LIMIT", 10)
DEFAULT_MIN_SIMILARITY = os.getenv("DEFAULT_MIN_SIMILARITY", 0.2)


# TODO: Refactor this class to only handle operations related to vectors
# TODO: Create a new class to handle video metadata, tasks and query records
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

    def fetch_videos(self, page, limit) -> PaginatedResult:
        # Assumes page is 0-indexed
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                offset = page * limit

                video_query = """
                    SELECT *
                    FROM videos
                    LIMIT %s
                    OFFSET %s
                    """
                cursor.execute(video_query, (limit, offset))
                rows = cursor.fetchall()

                videos_data = [
                    {
                        "id": video.get("id"),
                        "filename": video.get("filename"),
                        "s3_bucket": video.get("s3_bucket"),
                        "s3_key": video.get("s3_key"),
                        "duration": video.get("duration"),
                        "created_at": (
                            (created_at := video.get("created_at"))
                            and created_at.isoformat()
                        ),
                        "updated_at": (
                            (updated_at := video.get("updated_at"))
                            and updated_at.isoformat()
                        ),
                        "height": video.get("height"),
                        "width": video.get("width"),
                    }
                    for video in rows
                ]

                # Query to get the total count of videos
                count_query = """
                    SELECT COUNT(*) AS total_count
                    FROM videos
                    """
                cursor.execute(count_query)
                total_count_result = cursor.fetchone()
                total_videos = (
                    total_count_result["total_count"] if total_count_result else 0
                )

            return PaginatedResult(items=videos_data, total=total_videos)

        except Exception as e:
            self.logger.error(f"Error searching video in database: {e}")
            raise e

    def store(self, video_metadata, video_segments):
        try:
            video_id = self._insert_video(video_metadata)
            self._insert_video_segments(video_id, video_segments)
            self.conn.commit()
            self.logger.info(f"Stored video and {len(video_segments)} embeddings.")

        except Exception as e:
            self.logger.error("Error storing embedding:", e)
            self.conn.rollback()

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

    def _insert_video_segments(self, video_id: int, segments: list[dict]):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
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

        query_parts.append("ORDER BY similarity DESC, videos.id ASC LIMIT %s")
        query_params.append(page_limit)

        try:
            query = "\n".join(query_parts)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, query_params)
                results = cursor.fetchall()

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
                ORDER BY
                    similarity DESC,
                    videos.id ASC
                LIMIT %s;
            """
            query_params.append(page_limit)

            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(full_query, query_params)
                results = cursor.fetchall()

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
                    "created_at": raw_result["created_at"].isoformat(),
                    "updated_at": raw_result["updated_at"].isoformat(),
                    "height": raw_result["height"],
                    "width": raw_result["width"],
                },
            }
            for raw_result in raw_results
        ]

    def store_task(self, task_data):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO tasks (sqs_message_id, s3_bucket, s3_key, status)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        task_data["sqs_message_id"],
                        task_data["s3_bucket"],
                        task_data["s3_key"],
                        task_data["status"],
                    ),
                )
                self.conn.commit()
                self.logger.info(
                    f"Task stored for SQS message ID: {task_data['sqs_message_id']}, "
                    f"s3 bucket: {task_data['s3_bucket']} and s3 key: {task_data['s3_key']}."
                )
            except Exception as e:
                self.logger.error(f"Error storing task: {e}")
                self.conn.rollback()

    def update_task_status(self, sqs_message_id, new_status):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE tasks SET status = %s WHERE sqs_message_id = %s
                    """,
                    (new_status, sqs_message_id),
                )
                self.conn.commit()
                self.logger.info(
                    f"Task for SQS message ID: {sqs_message_id} has been updated with new status: {new_status}."
                )
            except Exception as e:
                self.logger.exception(f"Error updating task: {e}")
                self.conn.rollback()

    def fetch_tasks(self, page, limit) -> PaginatedResult:
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                offset = page * limit

                # Query to get tasks with pagination
                tasks_query = """
                    SELECT id, sqs_message_id, s3_bucket, s3_key, created_at, updated_at, status
                    FROM tasks
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(tasks_query, (limit, offset))
                raw_results = cursor.fetchall()

                # Query to get the total count of tasks
                count_query = """
                    SELECT COUNT(*) AS total_count
                    FROM tasks
                """
                cursor.execute(count_query)
                total_count_result = cursor.fetchone()
                total_tasks = (
                    total_count_result["total_count"] if total_count_result else 0
                )

            tasks_data = [
                {
                    "id": task.get("id"),
                    "sqs_message_id": task.get("sqs_message_id"),
                    "s3_bucket": task.get("s3_bucket"),
                    "s3_key": task.get("s3_key"),
                    "created_at": (
                        (created_at := task.get("created_at"))
                        and created_at.isoformat()
                    ),
                    "updated_at": (
                        (updated_at := task.get("updated_at"))
                        and updated_at.isoformat()
                    ),
                    "status": task.get("status"),
                }
                for task in raw_results
            ]
            return PaginatedResult(items=tasks_data, total=total_tasks)

        except Exception as e:
            self.logger.error(f"Error fetching tasks from database: {e}")
            raise

    def fetch_video(self, bucket, key):
        query = """
            SELECT * FROM videos
            WHERE s3_bucket = %s AND s3_key = %s
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (bucket, key))
                results = cursor.fetchall()

                if results:
                    self.logger.info(
                        f"Fetched {len(results)} row(s) for video [bucket: {bucket}, key: {key}]"
                    )
                else:
                    self.logger.warning(
                        f"No video found for [bucket: {bucket}, key: {key}]"
                    )

                return results
        except Exception as e:
            self.logger.exception(
                f"Database error while fetching video [bucket: {bucket}, key: {key}]"
            )
            raise

    def delete_video(self, bucket, key):
        query = """
            DELETE FROM videos
            WHERE s3_bucket = %s AND s3_key = %s
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (bucket, key))
                if cursor.rowcount > 0:
                    self.logger.info(
                        f"Deleted {cursor.rowcount} row(s) for video [bucket: {bucket}, key: {key}]"
                    )
                    self.conn.commit()
                    return True
                else:
                    self.logger.warning(
                        f"No matching video found for deletion [bucket: {bucket}, key: {key}]"
                    )
                    return False
        except Exception as e:
            self.logger.exception(
                f"Failed to delete video from database [bucket: {bucket}, key: {key}]"
            )
            raise
