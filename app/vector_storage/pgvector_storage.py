from .interface import VectorStorageInterface


class PgVectorStorage(VectorStorageInterface):
    """PostgreSQL with pgvector extension storage backend"""

    def __init__(self, db_session):
        self.db = db_session
