"""
Modelos de datos para la API de Openfiles.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field


class BagResponse(BaseModel):
    """Modelo de respuesta para operaciones de bag."""

    bag_id: str


class ValidationError(BaseModel):
    """Modelo de error de validación."""

    loc: List[Union[str, int]] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class HTTPValidationError(BaseModel):
    """Modelo de error de validación HTTP."""

    detail: Optional[List[ValidationError]] = Field(None, title="Detail")


class FileInfoResponse(BaseModel):
    """Modelo de respuesta de información de archivo."""

    filename: str
    size: int
    uploaded_at: float
    description: str
    bag_id: str


class UserResponse(BaseModel):
    """Modelo de respuesta de información de usuario."""

    uid: str
    space_left: float
    capacity: float
