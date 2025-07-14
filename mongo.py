import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoVectorStore:
    def __init__(self):
        MONGODB_URI = os.getenv("MONGODB_URI")
        MONGODB_DB = os.getenv("MONGODB_DB")
        MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")

        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.collection = self.db[MONGODB_COLLECTION]


    def transform_segments(self, segments, filepath):
        transformed = []
        for seg in segments:
            seg_id = f"{filepath}_{seg.start_offset_sec}_{seg.embedding_option}"
            doc = {
                "segment_id": seg_id,
                "filepath": filepath,
                "embedding": seg.embeddings_float,
                "type": seg.embedding_option,
                "embedding_scope": seg.embedding_scope,
                "start_offset": seg.start_offset_sec,
                "end_offset": seg.end_offset_sec,
            }
            transformed.append(doc)
        return transformed


    def store(self, filepath, segments):
        transformed = self.transform_segments(segments, filepath)
        self.collection.insert_many(transformed)
        num_embeddings = self.collection.count_documents({})
        print(f"Inserted {num_embeddings} embeddings into MongoDB.")


    def search(self, query_embedding, top_k=5, candidates=100):
        search_results = self.collection.aggregate([
            {
                "$vectorSearch": {
                    "queryVector": query_embedding,
                    "path": "embedding",
                    "numCandidates": candidates,
                    "index": "vector_index",
                    "limit": top_k
                }
            },
            {
                "$project": {
                    "score": {"$meta": "vectorSearchScore"},
                    "filepath": 1,
                    "type": 1,
                    "start_offset": 1,
                    "end_offset": 1
                }
            }
        ])

        return list(search_results)
