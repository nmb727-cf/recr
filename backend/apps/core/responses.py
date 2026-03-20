from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK, meta=None):
    response_data = {
        "success": True,
        "data": data,
        "message": message,
    }
    if meta:
        response_data["meta"] = meta
    return Response(response_data, status=status_code)


def error_response(message="Error", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    response_data = {
        "success": False,
        "data": None,
        "message": message,
    }
    if errors:
        response_data["errors"] = errors
    return Response(response_data, status=status_code)