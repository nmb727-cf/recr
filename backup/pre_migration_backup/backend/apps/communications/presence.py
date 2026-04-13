"""
Presence Management Service
===========================
Tracks online/offline status and last-seen timestamps using Redis.
Integrates with the RealtimePublisher to broadcast status changes.
"""
import json
import logging
import time
from typing import Optional, List, Dict

from django.conf import settings
import redis

logger = logging.getLogger(__name__)

# Redis keys
PRESENCE_KEY_PREFIX = 'presence:'  # presence:{user_id} -> status string (online/offline)
LAST_SEEN_KEY_PREFIX = 'last_seen:' # last_seen:{user_id} -> timestamp
USER_CONNECTIONS_PREFIX = 'user_conns:' # user_conns:{user_id} -> set of connection IDs

class PresenceService:
    _redis_client = None

    @classmethod
    def get_redis(cls):
        if cls._redis_client is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            cls._redis_client = redis.from_url(redis_url, decode_responses=True)
        return cls._redis_client

    @classmethod
    def user_connected(cls, user_id: str, connection_id: str):
        """Mark a user connection as active."""
        r = cls.get_redis()
        conn_key = f"{USER_CONNECTIONS_PREFIX}{user_id}"
        
        # Add connection to set
        r.sadd(conn_key, connection_id)
        # Set expiry for connection set to prevent leaks (1 day)
        r.expire(conn_key, 86400)

        # If it's the first connection, they just went online
        is_first = r.scard(conn_key) == 1
        if is_first:
            cls.set_status(user_id, 'online')

    @classmethod
    def user_disconnected(cls, user_id: str, connection_id: str):
        """Handle user disconnection."""
        r = cls.get_redis()
        conn_key = f"{USER_CONNECTIONS_PREFIX}{user_id}"
        
        # Remove connection from set
        r.srem(conn_key, connection_id)
        
        # If no more connections, they are offline
        if r.scard(conn_key) == 0:
            cls.set_status(user_id, 'offline')
            cls.update_last_seen(user_id)

    @classmethod
    def set_status(cls, user_id: str, status: str):
        """Set user status and broadcast event."""
        r = cls.get_redis()
        r.set(f"{PRESENCE_KEY_PREFIX}{user_id}", status)
        
        # Broadcast via RealtimePublisher
        from apps.communications.realtime import RealtimePublisher
        RealtimePublisher.publish_presence(user_id=user_id, status=status)

    @classmethod
    def get_status(cls, user_id: str) -> str:
        """Get current status of a user."""
        r = cls.get_redis()
        return r.get(f"{PRESENCE_KEY_PREFIX}{user_id}") or 'offline'

    @classmethod
    def update_last_seen(cls, user_id: str):
        """Update last seen timestamp."""
        r = cls.get_redis()
        r.set(f"{LAST_SEEN_KEY_PREFIX}{user_id}", int(time.time()))

    @classmethod
    def get_last_seen(cls, user_id: str) -> Optional[int]:
        """Get last seen timestamp."""
        r = cls.get_redis()
        val = r.get(f"{LAST_SEEN_KEY_PREFIX}{user_id}")
        return int(val) if val else None

    @classmethod
    def get_users_presence(cls, user_ids: List[str]) -> Dict[str, dict]:
        """Get presence info for multiple users at once."""
        r = cls.get_redis()
        pipe = r.pipeline()
        for uid in user_ids:
            pipe.get(f"{PRESENCE_KEY_PREFIX}{uid}")
            pipe.get(f"{LAST_SEEN_KEY_PREFIX}{uid}")
        
        results = pipe.execute()
        presence_map = {}
        for i, uid in enumerate(user_ids):
            status = results[i*2] or 'offline'
            last_seen = int(results[i*2 + 1]) if results[i*2 + 1] else None
            presence_map[uid] = {
                'status': status,
                'last_seen': last_seen
            }
        return presence_map
