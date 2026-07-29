class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__("RESOURCE_NOT_FOUND", f"{resource} '{resource_id}' does not exist", 404)


class ConflictError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__("RESOURCE_CONFLICT", message, 409)
