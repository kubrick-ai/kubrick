import os
import re
import uuid
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

class PineconeVectorStore:
    def __init__(self):
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME")

        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def sanitize_vector_id(self, s: str):
        sanitized = (
            s.encode('ascii', 'ignore').decode()                # Remove non-ASCII characters
            .replace(" ", "_")                                  # Replace spaces with underscores
        )
        sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "_", sanitized)  # Replace special characters with underscores
        sanitized = re.sub(r"_+", "_", sanitized)               # Collapse multiple underscores
        return sanitized


    def transform_segments(self, segments, filepath):
        """Convert segment objects into Pinecone vector tuples."""
        vectors = []
        for seg in segments:
            seg_id = f"{filepath}_{seg.start_offset_sec}_{seg.embedding_option}_{uuid.uuid4().hex}"
            metadata = {
                "filepath": filepath,
                "type": seg.embedding_option,
                "embedding_scope": seg.embedding_scope,
                "start_offset": seg.start_offset_sec,
                "end_offset": seg.end_offset_sec,
            }
            vectors.append({
                "id": self.sanitize_vector_id(seg_id),
                "values": seg.embeddings_float,
                "metadata": metadata
            })
        return vectors

    def store(self, filepath, segments):
        vectors = self.transform_segments(segments, filepath)
        self.index.upsert(vectors=vectors)
        print(f"Inserted {len(vectors)} vectors into Pinecone.")

    def search(self, query_embedding, top_k=5, filter_metadata=None):
        response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_metadata or {}
        )

        results = []
        for match in response["matches"]:
            results.append({
                "score": match["score"],
                "filepath": match["metadata"].get("filepath"),
                "type": match["metadata"].get("type"),
                "start_offset": match["metadata"].get("start_offset"),
                "end_offset": match["metadata"].get("end_offset")
            })
        return results
