from response_utils import ErrorCode


class SearchError(Exception):
    """Base exception for all search-related errors"""

    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.INTERNAL_ERROR):
        super().__init__(message)
        self.error_code = error_code


class SearchRequestError(SearchError):
    """Errors related to invalid search requests"""

    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_REQUEST)


class EmbeddingError(SearchError):
    """Errors during embedding extraction"""

    def __init__(self, message: str):
        super().__init__(message, ErrorCode.EMBEDDING_ERROR)


class DatabaseError(SearchError):
    """Errors from vector database operations"""

    def __init__(self, message: str):
        super().__init__(message, ErrorCode.DATABASE_ERROR)


class MediaProcessingError(SearchError):
    """Errors processing media files/URLs"""

    def __init__(self, message: str):
        super().__init__(message, ErrorCode.MEDIA_PROCESSING_ERROR)
