from abc import ABC, abstractmethod

from PIL import Image


class BaseOCR(ABC):
    """Recognizes text from an already-cropped region image. Implementations are
    selected at runtime; callers depend only on this interface."""

    @abstractmethod
    def recognize(self, image: Image.Image, lang: str) -> str:
        """Return the recognized text, or an empty string if none was found.

        `lang` is the source language hint ("auto", "en", "ja")."""
