"""
Cliente Asíncrono de la API de Openfiles
"""

import os
import aiohttp
import aiofiles
import asyncio
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import tempfile
import zipfile
import re

from .exceptions import (
    OpenfilesAPIError,
    OpenfilesHTTPError,
    OpenfilesValidationError,
)

from .models import BagResponse, FileInfoResponse, UserResponse, HTTPValidationError


class AsyncOpenfilesClient:
    """
    Cliente asíncrono para interactuar con la API de Openfiles.
    """

    BASE_URL = "https://app.openfiles.xyz"  # URL base por defecto

    def __init__(self, api_token: Optional[str] = None, base_url: Optional[str] = None):
        """
        Inicializar el cliente asíncrono de Openfiles.

        Args:
            api_token: Token de API para autenticación. Si no se proporciona,
                      intentará obtenerlo de la variable de entorno OPENFILES_API_TOKEN.
            base_url: URL base personalizada opcional para la API
        """
        self.api_token = api_token or os.environ.get("OPENFILES_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "El token de API debe proporcionarse como parámetro o "
                "a través de la variable de entorno OPENFILES_API_TOKEN"
            )
        self.base_url = base_url or self.BASE_URL
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Entrada del context manager asíncrono."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Salida del context manager asíncrono."""
        await self.close()

    async def _ensure_session(self):
        """Asegurar que la sesión esté inicializada."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self):
        """Cerrar la sesión HTTP."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self) -> Dict[str, str]:
        """
        Obtener las cabeceras para las peticiones de API.

        Returns:
            Dict con cabeceras de autorización
        """
        return {"X-Authorization": self.api_token}

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Any:
        """
        Manejar la respuesta de la API.

        Args:
            response: Objeto de respuesta de aiohttp

        Returns:
            Datos de respuesta parseados

        Raises:
            OpenfilesValidationError: Para errores de validación
            OpenfilesAPIError: Para errores de API con respuesta JSON
            OpenfilesHTTPError: Para otros errores HTTP
        """
        # Verificar si la respuesta indica un error
        if not response.ok:
            try:
                error_data = await response.json()

                # Si la respuesta contiene estructura de error de validación
                if "detail" in error_data:
                    # Verificar si detail es un string (mensaje de error simple)
                    if isinstance(error_data["detail"], str):
                        # Mensaje de error simple
                        raise OpenfilesAPIError(response.status, error_data)
                    # Caso contrario, intentar parsear como error de validación (lista de errores)
                    try:
                        validation_error = HTTPValidationError(**error_data)
                        raise OpenfilesValidationError(validation_error)
                    except Exception:
                        # Si el parseo del error de validación falla, usar error genérico de API
                        raise OpenfilesAPIError(response.status, error_data)

                # Otras respuestas de error JSON
                raise OpenfilesAPIError(response.status, error_data)

            except (ValueError, TypeError):
                # Si no es JSON o no coincide con nuestro modelo de error
                text = await response.text()
                raise OpenfilesHTTPError(response.status, text)

        # Si llegamos aquí, la respuesta fue exitosa
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return await response.json()

        return await response.read()

    def _format_validation_errors(self, validation_error: HTTPValidationError) -> str:
        """
        Formatear errores de validación para mejor legibilidad.

        Args:
            validation_error: El objeto HTTPValidationError

        Returns:
            Un string formateado con errores de validación
        """
        if not validation_error.detail:
            return "Error de validación desconocido"

        errors = []
        for error in validation_error.detail:
            location = " -> ".join(str(loc) for loc in error.loc)
            errors.append(f"{location}: {error.msg} ({error.type})")

        return "\n".join(errors)

    async def upload_file(self, file_path: Union[str, Path], description: str) -> BagResponse:
        """
        Subir un archivo al almacenamiento TON.

        Args:
            file_path: Ruta al archivo a subir
            description: Descripción del archivo

        Returns:
            BagResponse con el bag_id
        """
        await self._ensure_session()
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        url = f"{self.base_url}/api/files/upload"

        async with aiofiles.open(file_path, "rb") as file:
            file_content = await file.read()
            
            data = aiohttp.FormData()
            data.add_field("file", file_content, filename=file_path.name)
            data.add_field("description", description)

            async with self._session.post(
                url, headers=self._get_headers(), data=data
            ) as response:
                response_data = await self._handle_response(response)
                return BagResponse(**response_data)

    async def upload_folder(
        self, folder_path: Union[str, Path], description: str
    ) -> BagResponse:
        """
        Subir una carpeta al almacenamiento TON.

        Args:
            folder_path: Ruta a la carpeta a subir
            description: Descripción de la carpeta

        Returns:
            BagResponse con el bag_id
        """
        await self._ensure_session()
        
        folder_path = Path(folder_path)
        if not folder_path.exists() or not folder_path.is_dir():
            raise FileNotFoundError(f"Carpeta no encontrada: {folder_path}")

        # Crear un archivo zip temporal de la carpeta
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Crear el archivo zip en un executor para no bloquear el loop de eventos
            await asyncio.get_event_loop().run_in_executor(
                None, self._create_zip, folder_path, temp_path
            )

            url = f"{self.base_url}/api/folders/upload"

            async with aiofiles.open(temp_path, "rb") as file:
                file_content = await file.read()
                
                data = aiohttp.FormData()
                data.add_field("file", file_content, filename=folder_path.name + ".zip")
                data.add_field("description", description)

                async with self._session.post(
                    url, headers=self._get_headers(), data=data
                ) as response:
                    response_data = await self._handle_response(response)
                    return BagResponse(**response_data)
        finally:
            # Limpiar el archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def _create_zip(self, folder_path: Path, temp_path: str):
        """
        Crear un archivo zip de manera síncrona (para ejecutar en executor).
        
        Args:
            folder_path: Ruta de la carpeta a comprimir
            temp_path: Ruta del archivo temporal zip
        """
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname)

    async def delete_file(self, bag_id: str) -> None:
        """
        Eliminar un archivo del almacenamiento TON.

        Args:
            bag_id: ID del bag a eliminar
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/bag"

        data = aiohttp.FormData()
        data.add_field("bag_id", bag_id)

        async with self._session.delete(
            url, headers=self._get_headers(), data=data
        ) as response:
            await self._handle_response(response)

    async def download_file(
        self, bag_id: str, destination: Optional[Union[str, Path]] = None
    ) -> Union[bytes, str]:
        """
        Descargar un archivo del almacenamiento TON.

        Args:
            bag_id: ID del bag a descargar
            destination: Ruta opcional para guardar el archivo.
                        Si es None, guarda con nombre original en directorio actual.
                        Si es un directorio, guarda con nombre original en ese directorio.
                        Si es ruta completa, guarda con ese nombre específico.

        Returns:
            Ruta al archivo guardado (siempre guarda el archivo)
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/bag/download/{bag_id}"

        async with self._session.get(
            url, headers=self._get_headers()
        ) as response:
            content = await self._handle_response(response)

            # Obtener nombre original del archivo
            original_filename = self._get_filename_from_headers(dict(response.headers))

            if destination is None:
                # Si no se especifica destination, usar nombre original en directorio actual
                destination = Path(original_filename)
            else:
                destination = Path(destination)
                
                # Si destination es un directorio, usar el nombre de archivo del header
                if destination.is_dir():
                    destination = destination / original_filename

            async with aiofiles.open(destination, "wb") as f:
                if isinstance(content, bytes):
                    await f.write(content)
                else:
                    await f.write(content.encode())

            return str(destination)

    async def download_file_content(self, bag_id: str) -> bytes:
        """
        Descargar contenido de un archivo en memoria (sin guardarlo).

        Args:
            bag_id: ID del bag a descargar

        Returns:
            Contenido del archivo como bytes
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/bag/download/{bag_id}"

        async with self._session.get(
            url, headers=self._get_headers()
        ) as response:
            content = await self._handle_response(response)
            return content if isinstance(content, bytes) else content.encode()

    def _get_filename_from_headers(self, headers: Dict[str, str]) -> str:
        """
        Extraer nombre de archivo del header Content-Disposition.

        Args:
            headers: Headers de respuesta

        Returns:
            Nombre de archivo extraído o nombre por defecto
        """
        content_disposition = headers.get("Content-Disposition", "")

        if "filename=" in content_disposition:
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                return filename_match.group(1)

        return "downloaded_file"

    async def get_user_info(self) -> UserResponse:
        """
        Obtener información del usuario.

        Returns:
            UserResponse con información del usuario
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/user"

        async with self._session.get(
            url, headers=self._get_headers()
        ) as response:
            response_data = await self._handle_response(response)
            return UserResponse(**response_data)

    async def get_user_files_list(self) -> List[FileInfoResponse]:
        """
        Obtener la lista de archivos del usuario.

        Returns:
            Lista de objetos FileInfoResponse
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/user/files_list"

        async with self._session.get(
            url, headers=self._get_headers()
        ) as response:
            response_data = await self._handle_response(response)
            return [FileInfoResponse(**item) for item in response_data]

    async def add_by_bag_id(self, bag_id: str) -> None:
        """
        Agregar un archivo por bag ID.

        Args:
            bag_id: ID del bag a usar
        """
        await self._ensure_session()
        
        url = f"{self.base_url}/api/bag/add_by_id"

        data = aiohttp.FormData()
        data.add_field("bag_id", bag_id)

        async with self._session.post(
            url, headers=self._get_headers(), data=data
        ) as response:
            await self._handle_response(response)
