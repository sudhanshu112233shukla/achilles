class CompilationError(Exception):
    """Raised when C++ compilation fails."""
    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors
