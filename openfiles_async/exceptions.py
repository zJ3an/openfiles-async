from typing import Any, Dict
from .models import HTTPValidationError


class OpenfilesError(Exception):
    """Excepción base para todos los errores de la API de Openfiles."""

    pass


class OpenfilesValidationError(OpenfilesError):
    """Excepción lanzada cuando falla la validación de la API."""

    def __init__(self, validation_error: HTTPValidationError):
        self.validation_error = validation_error
        self.details = validation_error.detail
        message = self._format_message()
        super().__init__(message)

    def _format_message(self) -> str:
        """Formatear errores de validación para mejor legibilidad."""
        if not self.details:
            return "Error de validación desconocido"

        errors = []
        for error in self.details:
            location = " -> ".join(str(loc) for loc in error.loc)
            errors.append(f"{location}: {error.msg} ({error.type})")

        return "\n".join(errors)


class OpenfilesAPIError(OpenfilesError):
    """Excepción lanzada para errores de API con respuesta JSON."""

    def __init__(self, status_code: int, error_data: Dict[str, Any]):
        self.status_code = status_code
        self.error_data = error_data
        message = f"Error de API ({status_code}): {error_data}"
        super().__init__(message)


class OpenfilesHTTPError(OpenfilesError):
    """Excepción lanzada para errores HTTP generales."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Error HTTP ({status_code}): {message}")
