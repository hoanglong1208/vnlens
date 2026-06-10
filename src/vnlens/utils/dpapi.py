import base64
import ctypes
from ctypes import wintypes


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes) -> _DataBlob:
    buf = ctypes.create_string_buffer(data, len(data))
    return _DataBlob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))


def _blob_to_bytes(blob: _DataBlob) -> bytes:
    return ctypes.string_at(blob.pbData, blob.cbData)


def encrypt(plaintext: str) -> str:
    """Encrypt with the current Windows user account (DPAPI) and return base64.

    The result can only be decrypted by the same Windows user, so an API key
    stays unreadable if the config file is copied elsewhere."""
    blob_in = _blob(plaintext.encode("utf-8"))
    blob_out = _DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise OSError("DPAPI CryptProtectData failed")
    try:
        return base64.b64encode(_blob_to_bytes(blob_out)).decode("ascii")
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def decrypt(ciphertext: str) -> str:
    blob_in = _blob(base64.b64decode(ciphertext))
    blob_out = _DataBlob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        raise OSError("DPAPI CryptUnprotectData failed")
    try:
        return _blob_to_bytes(blob_out).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
