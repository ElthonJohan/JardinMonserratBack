import logging
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CloudinaryUploadException(Exception):
    pass

class CloudinaryDeleteException(Exception):
    pass

class CloudinaryReplaceException(Exception):
    pass

def upload_image(file: Any, folder: str) -> Dict[str, str]:
    """
    Subir una imagen a Cloudinary.
    """
    try:
        response = cloudinary.uploader.upload(file, folder=folder)
        return {
            "url": response.get("secure_url"),
            "public_id": response.get("public_id")
        }
    except Exception as e:
        logger.exception("Error al subir imagen a Cloudinary")
        raise CloudinaryUploadException(f"Error al subir imagen a Cloudinary: {str(e)}")

def delete_image(public_id: str) -> None:
    """
    Eliminar una imagen de Cloudinary por su public_id.
    """
    if not public_id:
        return
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        logger.exception(f"Error al eliminar imagen en Cloudinary (public_id={public_id})")
        raise CloudinaryDeleteException(f"Error al eliminar imagen en Cloudinary: {str(e)}")

def replace_image(file: Any, public_id: str, folder: str) -> Dict[str, str]:
    """
    Reemplazar una imagen existente subiendo la nueva y eliminando la anterior.
    Nunca se elimina la imagen original antes de subir la nueva.
    """
    try:
        nueva = upload_image(file, folder)
    except CloudinaryUploadException as e:
        raise CloudinaryReplaceException(f"Fallo el reemplazo al subir la nueva imagen: {str(e)}")

    if public_id:
        try:
            delete_image(public_id)
        except CloudinaryDeleteException:
            logger.warning(f"Se reemplazó la imagen pero falló el borrado de la anterior ({public_id}).")

    return nueva
