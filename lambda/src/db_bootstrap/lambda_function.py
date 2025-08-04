import os
from config import get_secret, setup_logging, get_db_config
import json
import psycopg2

# Environment variables
SECRET_NAME = os.getenv("SECRET_NAME", "kubrick_secret")


def lambda_handler(event, context):
    logger = setup_logging()
    SECRET = get_secret(SECRET_NAME)
    DB_CONFIG = get_db_config(SECRET)

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:

            with open("schema.sql", "r") as f:
                sql_script = f.read()

            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
                logger.info("Database initialization SQL script executed successfully.")

            return {
                "statusCode": 200,
                "body": json.dumps(
                    "Database initialization SQL script executed successfully."
                ),
            }

    except Exception as e:
        print(f"Error connecting to or executing bootstrap SQL on database: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps("Database initialization failed."),
        }
        # raise
