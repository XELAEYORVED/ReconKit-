"""Metadata extraction module.

Finds public documents/images linked from the target homepage and extracts
embedded metadata (author, software, GPS, creation dates) from a small sample.
Uses optional libraries (pypdf, Pillow, python-docx) when installed; reports
the document inventory regardless. Passive: fetches already-public files.
"""

from __future__ import annotations

import io
import re

from ..models import TargetType
from .base import BaseModule, ModuleResult, make_client

_LINK_RE = re.compile(r'href=["\']([^"\']+\.(?:pdf|docx?|xlsx?|pptx?|jpe?g|png))["\']', re.I)
_MAX_FILES = 5


class MetadataExtractModule(BaseModule):
    name = "metadata"
    description = "Extract embedded metadata (author, software, GPS) from public documents/images."
    rate_limit = 1.0
    supported_types = (TargetType.DOMAIN,)
    category = "identity"

    def _pdf_meta(self, blob: bytes) -> dict:
        try:
            from pypdf import PdfReader
        except Exception:
            return {"_note": "pypdf not installed"}
        try:
            reader = PdfReader(io.BytesIO(blob))
            info = reader.metadata or {}
            return {k.lstrip("/"): str(v) for k, v in info.items()}
        except Exception as exc:
            return {"_error": str(exc)}

    def _image_meta(self, blob: bytes) -> dict:
        try:
            from PIL import ExifTags, Image
        except Exception:
            return {"_note": "Pillow not installed"}
        try:
            img = Image.open(io.BytesIO(blob))
            exif = img.getexif()
            out = {}
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                out[tag] = str(value)[:120]
            return out
        except Exception as exc:
            return {"_error": str(exc)}

    def _docx_meta(self, blob: bytes) -> dict:
        try:
            import docx
        except Exception:
            return {"_note": "python-docx not installed"}
        try:
            d = docx.Document(io.BytesIO(blob))
            cp = d.core_properties
            return {
                "author": cp.author,
                "last_modified_by": cp.last_modified_by,
                "created": str(cp.created),
                "title": cp.title,
            }
        except Exception as exc:
            return {"_error": str(exc)}

    async def run(self, target: str) -> ModuleResult:
        async with make_client(timeout=20.0) as client:
            links: list[str] = []
            for scheme in ("https", "http"):
                try:
                    await self._rate_limited("metadata")
                    resp = await client.get(f"{scheme}://{target}")
                    base = str(resp.url)
                    for m in _LINK_RE.findall(resp.text):
                        full = m if m.startswith("http") else base.rstrip("/") + "/" + m.lstrip("/")
                        links.append(full)
                    break
                except Exception:
                    continue

            links = list(dict.fromkeys(links))
            extracted = []
            authors: set[str] = set()
            software: set[str] = set()
            for link in links[:_MAX_FILES]:
                try:
                    await self._rate_limited("metadata")
                    r = await client.get(link)
                    blob = r.content[:5_000_000]
                except Exception:
                    continue
                low = link.lower()
                if low.endswith(".pdf"):
                    meta = self._pdf_meta(blob)
                elif low.endswith((".jpg", ".jpeg", ".png")):
                    meta = self._image_meta(blob)
                elif low.endswith((".docx", ".doc")):
                    meta = self._docx_meta(blob)
                else:
                    meta = {}
                for k in ("Author", "author", "Creator"):
                    if meta.get(k):
                        authors.add(str(meta[k]))
                for k in ("Producer", "software", "Software"):
                    if meta.get(k):
                        software.add(str(meta[k]))
                extracted.append({"url": link, "metadata": meta})

        data = {
            "documents_found": len(links),
            "document_links": links[:100],
            "extracted": extracted,
            "authors": sorted(authors),
            "software": sorted(software),
        }
        conf = 0.7 if extracted else 0.4
        return self.ok(target, data, confidence=conf, tags=["identity", "metadata"])
