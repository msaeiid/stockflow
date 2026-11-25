from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError, RestrictedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """DRF's handler, plus clean 4xx answers for errors raised by the models.

    - Deleting a record that others still reference (PROTECT) -> 409 Conflict
      instead of a 500.
    - A Django ValidationError raised by model code -> 400 with its messages.
    """
    if isinstance(exc, ProtectedError | RestrictedError):
        return Response(
            {"detail": "This record is still in use by other records and cannot be deleted."},
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, DjangoValidationError):
        return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)
    return drf_exception_handler(exc, context)
