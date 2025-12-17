from __future__ import annotations

from rest_framework.permissions import BasePermission
from django.conf import settings


class ImportApiKeyPermission(BasePermission):
    """
    Permission for CSV import endpoints without requiring frontend login.

    Behavior:
    - If `IMPORT_API_KEY` is set: require `X-API-KEY` header to match.
    - If not set and `DEBUG=True`: allow (local development convenience).
    - Otherwise: deny.
    """

    message = "Import is not allowed. Provide X-API-KEY or configure IMPORT_API_KEY."

    def has_permission(self, request, view) -> bool:
        key = getattr(settings, "IMPORT_API_KEY", "")
        if key:
            provided = request.headers.get("X-API-KEY") or request.headers.get("X-Api-Key")
            return bool(provided) and provided == key
        return bool(getattr(settings, "DEBUG", False))

