from abc import ABC, abstractmethod
from typing import List, Dict, Any


class VectorStorageInterface(ABC):
    """Abstract interface for vector storage backends"""

    @abstractmethod
    def store_vector(self, vector: List[float], metadata: Dict[str, Any]) -> str:
        """
        Store a vector with metadata and return its ID

        Args:
            vector: The embedding vector as a list of floats
            metadata: Dictionary containing metadata about the vector

        Returns:
            str: Unique identifier for the stored vector
        """
        pass

    @abstractmethod
    def search_similar(
        self, query_vector: List[float], limit: int = 5, min_similarity: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_vector: The query embedding vector
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dictionaries containing search results with similarity scores
        """
        pass

    @abstractmethod
    def search_similar_batch(
        self,
        query_vectors: List[List[float]],
        limit: int = 5,
        min_similarity: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors using multiple query vectors

        Args:
            query_vectors: List of query embedding vectors
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dictionaries containing search results with similarity scores
        """
        pass

    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector by its ID

        Args:
            vector_id: The unique identifier of the vector to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def delete_vectors_by_metadata(self, metadata_filter: Dict[str, Any]) -> int:
        """
        Delete vectors matching metadata criteria

        Args:
            metadata_filter: Dictionary of metadata key-value pairs to match

        Returns:
            int: Number of vectors deleted
        """
        pass

    @abstractmethod
    def get_vector_count(self) -> int:
        """
        Get the total number of vectors in storage

        Returns:
            int: Total number of vectors
        """
        pass

