import os
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


def search(embedding, limit=5):
    """Search using vector similarity."""
    try:
        # Connect to the database
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Execute the similarity search
            cur.execute(
                """
            SELECT
                *,
                1 - (embedding <=> %s::vector) as similarity
            FROM video_embeddings
            WHERE 1 - (embedding <=> %s::vector) > 0.4
            ORDER BY similarity DESC
            LIMIT %s
            """,
                (embedding, embedding, limit),
            )

            # Fetch and return the results
            results = cur.fetchall()

        conn.close()

        return results

    except Exception as e:
        print(f"Error searching embeddings: {e}")
        raise e


def find_similar(embedding, limit=5):
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
            ORDER BY similarity DESC
            LIMIT %s;
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (embedding, limit))
            results = cur.fetchall()

        conn.close()
        return results

    except Exception as e:
        print(f"Error searching activities: {e}")
        raise e
