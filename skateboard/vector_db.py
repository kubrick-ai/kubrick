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
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
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


def store(video_filepath, embedding):
    # Connect to Postgres
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Store in Postgres with all required columns
        cursor.execute(
            "INSERT INTO video_embeddings (source, type, start_time, end_time, embedding) VALUES (%s, %s, %s, %s, %s)",
            (video_filepath, embedding.embedding_option, embedding.start_offset_sec, embedding.end_offset_sec, embedding.embeddings_float),
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
                start_time,
                end_time,
                1 - (embedding <=> %s::vector) AS similarity
            FROM video_embeddings
            ORDER BY similarity DESC
            LIMIT %s;
        """
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (embedding, limit))
            results = cur.fetchall()

        conn.close()
        
        # Convert to list of dictionaries with ordered fields
        formatted_results = []
        for row in results:
            formatted_results.append({
                'id': row['id'],
                'source': row['source'],
                'type': row['type'],
                'start_time': row['start_time'],
                'end_time': row['end_time'],
                'similarity': row['similarity']
            })
        
        return formatted_results

    except Exception as e:
        print(f"Error searching activities: {e}")
        raise e


def print_video_embeddings():
    try:
        # Connect to the database
        conn = get_connection()
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all records from video_embeddings table
            cur.execute("""
                SELECT id, source, type, start_time, end_time, 
                       CASE WHEN embedding IS NOT NULL THEN 'Present' ELSE 'NULL' END as embedding_status
                FROM video_embeddings
                ORDER BY id;
            """)
            
            results = cur.fetchall()
            
            if not results:
                print("No records found in video_embeddings table.")
                return
            
            print(f"\nVideo Embeddings Table Contents ({len(results)} records):")
            print("-" * 85)
            print(f"{'ID':<5} {'Source':<35} {'Type':<15} {'Start':<8} {'End':<8} {'Embedding':<10}")
            print("-" * 85)
            
            for row in results:
                source_display = row['source'][:34] if len(row['source']) > 34 else row['source']
                print(f"{row['id']:<5} {source_display:<35} {row['type']:<15} "
                      f"{row['start_time']:<8.2f} {row['end_time']:<8.2f} {row['embedding_status']:<10}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error printing video embeddings: {e}")
        raise e
