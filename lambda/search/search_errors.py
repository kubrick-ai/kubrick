"""
Search-related exception classes for the search service.

This module defines a hierarchy of custom exceptions that provide structured
error handling with error codes and contextual details for debugging.
"""


class SearchError(Exception):
    """Base exception for all search-related errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code or "SEARCH_ERROR"
        self.details = details or {}


class SearchRequestError(SearchError):
    """Errors related to invalid search requests"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "INVALID_REQUEST", details)


class EmbeddingError(SearchError):
    """Errors during embedding extraction"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "EMBEDDING_ERROR", details)


class DatabaseError(SearchError):
    """Errors from vector database operations"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "DATABASE_ERROR", details)


class MediaProcessingError(SearchError):
    """Errors processing media files/URLs"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "MEDIA_PROCESSING_ERROR", details)