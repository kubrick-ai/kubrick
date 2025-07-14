import os
from typing import Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


DATABASE_NAME = os.getenv("DATABASE_NAME")

# Database connection parameters
DB_PARAMS = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "database": DATABASE_NAME,
}

# Default search parameters
DEFAULT_PAGE_LIMIT = 5
DEFAULT_MIN_SIMILARITY = 0.2


def get_connection():
    return psycopg2.connect(**DB_PARAMS)


def setup():
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS video_embeddings (
                id SERIAL PRIMARY KEY,
                source TEXT NOT NULL,
                type TEXT NOT NULL,
                start_offset REAL NOT NULL,
                end_offset REAL NOT NULL,
                embedding vector(1024)
            );
        """)
        conn.commit()
        print("Database setup complete!")
    except Exception as e:
        print("Error during setup:", e)
    finally:
        cur.close()
        conn.close()


def store(video_filepath, embedding_type, start_offset, end_offset, embedding):
    # Connect to Postgres
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Store in Postgres (convert to list first)
        cursor.execute(
            """
            INSERT INTO video_embeddings (
                source,
                type,
                start_offset,
                end_offset,
                embedding
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (video_filepath, embedding_type, start_offset, end_offset, embedding),
        )
        conn.commit()

    except Exception as e:
        print("Error storing embedding:", e)

    finally:
        cursor.close()
        conn.close()


def find_similar(
    embedding, page_limit=DEFAULT_PAGE_LIMIT, min_similarity=DEFAULT_MIN_SIMILARITY
) -> list[dict[str, Any]]:
    try:
        # Connect to the database
        conn = get_connection()

        query = """
            SELECT
                id,
                source,
                type,
                start_offset,
                end_offset,
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
    embeddings, page_limit=DEFAULT_PAGE_LIMIT, min_similarity=DEFAULT_MIN_SIMILARITY
) -> list[dict[str, Any]]:
    try:
        # Connect to the database
        conn = get_connection()

        # Create a UNION query for multiple embeddings
        query_parts = []
        params = []

        for i, embedding in enumerate(embeddings):
            query_parts.append(f"""
                SELECT
                    id,
                    source,
                    type,
                    start_offset,
                    end_offset,
                    1 - (embedding <=> %s::vector) AS similarity,
                    {i} AS query_index
                FROM video_embeddings
                WHERE (1 - (embedding <=> %s::vector)) > %s
            """)
            params.extend([embedding, embedding, min_similarity])

        # Combine all queries with UNION and order by similarity
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
