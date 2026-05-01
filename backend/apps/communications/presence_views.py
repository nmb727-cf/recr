"""
Presence API Views
==================
Endpoints for fetching user presence and last-seen status.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.communications.presence import PresenceService
from apps.core.responses import success_response, error_response

class UserPresenceView(APIView):
    """
    GET /api/v1/communications/presence/?user_ids=uuid1,uuid2
    
    Returns current online status and last seen timestamp for requested users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_ids_str = request.query_params.get('user_ids', '')
        if not user_ids_str:
            return error_response("user_ids query parameter is required.")
        
        user_ids = [uid.strip() for uid in user_ids_str.split(',') if uid.strip()]
        if not user_ids:
            return error_response("No valid user_ids provided.")
            
        try:
            presence_data = PresenceService.get_users_presence(user_ids)
            return success_response(
                data={'presence': presence_data},
                message="Presence data retrieved."
            )
        except Exception as exc:
            return error_response(str(exc))
