from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor


class VectorDBService:
    def __init__(self, db_params, default_page_limit, default_min_similarity):
        self.db_params = db_params
        self.default_page_limit = default_page_limit
        self.default_min_similarity = default_min_similarity

    def get_connection(self):
        return psycopg2.connect(**self.db_params)

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
                videos.title,
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

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, query_params)
                results = cur.fetchall()

            conn.close()
            return self._normalize_find_similar_results(results)

        except Exception as e:
            print(f"Error searching database: {e}")
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
                        videos.title,
                        videos.url,
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

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(full_query, query_params)
                results = cur.fetchall()

            conn.close()
            return self._normalize_find_similar_results(results)

        except Exception as e:
            print(f"Error searching database with batch: {e}")
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
                    "title": raw_result["title"],
                    "s3_bucket": raw_result["s3_bucket"],
                    "s3_key": raw_result["s3_key"],
                    "filename": raw_result["filename"],
                    "duration": raw_result["duration"],
                    "created_at": (
                        raw_result["created_at"].isoformat()
                        if raw_result["created_at"]
                        else None
                    ),
                    "updated_at": (
                        raw_result["updated_at"].isoformat()
                        if raw_result["updated_at"]
                        else None
                    ),
                    "height": raw_result["height"],
                    "width": raw_result["width"],
                },
            }
            for raw_result in raw_results
        ]
