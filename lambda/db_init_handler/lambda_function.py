from config import load_config, get_secret, setup_logging, get_db_config
import psycopg2


def lambda_handler():
    logger = setup_logging()
    config = load_config()
    SECRET = get_secret(config)
    DB_CONFIG = get_db_config(SECRET)

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:

            with open("schema.sql", "r") as f:
                sql_script = f.read()

            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
                logger.info("Database initialization SQL script executed successfully.")

    except Exception as e:
        print(f"Error connecting to or executing bootstrap SQL on database: {e}")
        raise
