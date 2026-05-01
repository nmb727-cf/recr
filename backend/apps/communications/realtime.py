"""
Real-time Event Publisher
==========================
Publishes real-time events to Redis pub/sub channels.

Frontend clients subscribe to:
  - notifications:{user_id}         → new notification events, unread count
  - thread:{thread_id}              → new message events

When Django Channels is installed and the WebSocket consumers are connected,
these pub/sub messages are broadcast to the relevant WebSocket connections.

If Redis is unavailable this degrades gracefully without raising exceptions.
"""
import json
import logging

logger = logging.getLogger(__name__)

# Channel name patterns
USER_CHANNEL = 'user_{user_id}'
THREAD_CHANNEL = 'thread_{thread_id}'
TENANT_CHANNEL = 'tenant_{tenant_id}'


class RealtimePublisher:

    # ── Event Handler Services (Requested) ──────────────────────────────────

    @staticmethod
    def send_user_event(user_id: str, event: dict):
        """Send an arbitrary event to a specific user's private channel."""
        RealtimePublisher._publish(
            channel=USER_CHANNEL.format(user_id=user_id),
            group_name=f'user_{user_id}',
            event=event,
        )

    @staticmethod
    def send_thread_event(thread_id: str, event: dict):
        """Send an arbitrary event to all participants of a thread."""
        RealtimePublisher._publish(
            channel=THREAD_CHANNEL.format(thread_id=thread_id),
            group_name=f'thread_{thread_id}',
            event=event,
        )

    @staticmethod
    def send_tenant_event(tenant_id: str, event: dict):
        """Send a broadcast event to all users within a tenant."""
        RealtimePublisher._publish(
            channel=TENANT_CHANNEL.format(tenant_id=tenant_id),
            group_name=f'tenant_{tenant_id}',
            event=event,
        )

    # ── High-level Messaging Events ────────────────────────────────────────

    @staticmethod
    def publish_notification(*, user_id: str, notification_id: str):
        """Push a 'notification.new' event to the user's channel."""
        RealtimePublisher.send_user_event(user_id, {
            'type': 'notification.new',
            'notification_id': notification_id,
            'user_id': user_id,
        })
        RealtimePublisher.publish_unread_count(user_id=user_id)

    @staticmethod
    def publish_notification_read(*, user_id: str, notification_id: str):
        """Push a 'notification.read' event."""
        RealtimePublisher.send_user_event(user_id, {
            'type': 'notification.read',
            'notification_id': notification_id,
            'user_id': user_id,
        })
        RealtimePublisher.publish_unread_count(user_id=user_id)

    @staticmethod
    def publish_unread_count(*, user_id: str):
        """Push updated unread count to the user's channel."""
        try:
            from apps.communications.notification_service import NotificationService
            count = NotificationService.get_unread_count(user_id=user_id)
        except Exception:
            count = None

        RealtimePublisher.send_user_event(user_id, {
            'type': 'notification.count.updated',
            'user_id': user_id,
            'unread_count': count,
        })

    @staticmethod
    def publish_message(*, thread_id: str, message_id: str):
        """Push a 'message.new' event to the thread's channel."""
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'message.new',
            'thread_id': thread_id,
            'message_id': message_id,
        })
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'thread.updated',
            'thread_id': thread_id,
        })

    @staticmethod
    def publish_message_updated(*, thread_id: str, message_id: str):
        """Push a 'message.updated' event."""
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'message.updated',
            'thread_id': thread_id,
            'message_id': message_id,
        })

    @staticmethod
    def publish_message_deleted(*, thread_id: str, message_id: str):
        """Push a 'message.deleted' event."""
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'message.deleted',
            'thread_id': thread_id,
            'message_id': message_id,
        })

    @staticmethod
    def publish_presence(*, user_id: str, status: str):
        """Broadcast user presence change."""
        # For presence, we might want to notify anyone who has this user in their view.
        # Often this is pushed to the tenant channel so all online users see it.
        # But we'll also push to the user's own channel for multi-device sync.
        event = {
            'type': 'user.presence',
            'user_id': user_id,
            'status': status,
        }
        RealtimePublisher.send_user_event(user_id, event)

    @staticmethod
    def publish_typing(*, thread_id: str, user_id: str, is_typing: bool):
        """Push typing indicator event to a thread."""
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'typing.indicator',
            'thread_id': thread_id,
            'user_id': user_id,
            'is_typing': is_typing,
        })

    @staticmethod
    def publish_read_receipt(*, thread_id: str, user_id: str, last_read_at: str):
        """Broadcast that a user has read messages in a thread."""
        RealtimePublisher.send_thread_event(thread_id, {
            'type': 'message.read',
            'thread_id': thread_id,
            'user_id': user_id,
            'last_read_at': last_read_at,
        })

    @staticmethod
    def _publish(*, channel: str, event: dict, group_name: str = None):
        """
        Publish the event.
        - If Django Channels is installed and group_name provided, use group_send.
        - Otherwise, publish to Redis pub/sub.
        Silently swallows errors to ensure messaging flow never crashes.
        """
        # Try Django Channels group_send (modern way)
        if group_name:
            try:
                from asgiref.sync import async_to_sync
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Channels requires a 'type' field which maps to the consumer method name.
                    # We ensure event['type'] exists and uses dot notation (e.g. notification.new
                    # maps to consumer.notification_new).
                    msg_event = event.copy()
                    if 'type' in msg_event:
                        msg_event['type'] = msg_event['type'].replace('.', '_')
                    async_to_sync(channel_layer.group_send)(group_name, msg_event)
                    return  # Success
            except Exception:
                pass  # Fallback to Redis pub/sub

        # Fallback to Redis pub/sub (low-level way)
        try:
            import redis
            from django.conf import settings
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379')
            r = redis.from_url(redis_url)
            r.publish(channel, json.dumps(event))
        except Exception as exc:
            logger.debug('RealtimePublisher: failed to publish to %s: %s', channel, exc)


# ---------------------------------------------------------------------------
# WebSocket consumer (Django Channels)
# ---------------------------------------------------------------------------
# These consumers are only active when `channels` is installed.
# Install with: pip install channels channels-redis

try:
    from channels.generic.websocket import AsyncJsonWebsocketConsumer
    import asyncio

    class UserConsumer(AsyncJsonWebsocketConsumer):
        """
        Per-user private stream (notifications, presence, count).
        Frontend connects to: ws://.../ws/user/
        """

        async def connect(self):
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                await self.close(code=4401)
                return

            self.user_id = str(user.id)
            self.group_name = f'user_{self.user_id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            # Mark user as online
            try:
                from apps.communications.presence import PresenceService
                PresenceService.user_connected(self.user_id, self.channel_name)
            except Exception:
                pass

        async def disconnect(self, close_code):
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(self.group_name, self.channel_name)
                # Mark user as offline
                try:
                    from apps.communications.presence import PresenceService
                    PresenceService.user_disconnected(self.user_id, self.channel_name)
                except Exception:
                    pass

        async def receive_json(self, content):
            action = content.get('action')
            if action == 'ping':
                await self.send_json({'type': 'pong'})
            elif action == 'get_presence':
                user_ids = content.get('user_ids', [])
                if user_ids:
                    try:
                        from apps.communications.presence import PresenceService
                        presence_data = PresenceService.get_users_presence(user_ids)
                        await self.send_json({
                            'type': 'presence.batch',
                            'presence': presence_data
                        })
                    except Exception:
                        pass

        async def notification_new(self, event):
            await self.send_json(event)

        async def notification_read(self, event):
            await self.send_json(event)

        async def notification_count_updated(self, event):
            await self.send_json(event)

        async def user_presence(self, event):
            await self.send_json(event)

    class ThreadConsumer(AsyncJsonWebsocketConsumer):
        """
        Per-thread message stream.
        Frontend connects to: ws://.../ws/threads/{thread_id}/
        """

        async def connect(self):
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                await self.close(code=4401)
                return

            self.user_id = str(user.id)
            self.thread_id = self.scope['url_route']['kwargs']['thread_id']
            # Validate participant
            has_access = await self._check_participant(user, self.thread_id)
            if not has_access:
                await self.close(code=4403)
                return

            self.group_name = f'thread_{self.thread_id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

        async def disconnect(self, close_code):
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(self.group_name, self.channel_name)

        async def receive_json(self, content):
            action = content.get('action')
            if action == 'ping':
                await self.send_json({'type': 'pong'})
            elif action == 'typing':
                is_typing = bool(content.get('is_typing', False))
                RealtimePublisher.publish_typing(
                    thread_id=self.thread_id,
                    user_id=self.user_id,
                    is_typing=is_typing
                )

        async def message_new(self, event):
            await self.send_json(event)

        async def message_updated(self, event):
            await self.send_json(event)

        async def message_deleted(self, event):
            await self.send_json(event)

        async def thread_updated(self, event):
            await self.send_json(event)

        async def typing_indicator(self, event):
            await self.send_json(event)

        async def message_read(self, event):
            await self.send_json(event)

        @staticmethod
        async def _check_participant(user, thread_id) -> bool:
            from channels.db import database_sync_to_async
            from apps.communications.models import ThreadParticipant, MessageThread

            @database_sync_to_async
            def check():
                try:
                    thread = MessageThread.objects.get(
                        id=thread_id,
                        tenant_id=user.tenant_id,
                        is_deleted=False,
                    )
                    return (
                        ThreadParticipant.objects.filter(
                            thread=thread,
                            user_id=user.id,
                            is_active=True,
                        ).exists()
                        or str(user.id) in (thread.participant_ids or [])
                    )
                except MessageThread.DoesNotExist:
                    return False

            return await check()

    class TenantConsumer(AsyncJsonWebsocketConsumer):
        """
        Global broadcast stream for a tenant.
        Frontend connects to: ws://.../ws/tenant/
        """

        async def connect(self):
            user = self.scope.get('user')
            if not user or not user.is_authenticated:
                await self.close(code=4401)
                return

            self.tenant_id = str(user.tenant_id)
            self.group_name = f'tenant_{self.tenant_id}'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

        async def disconnect(self, close_code):
            if hasattr(self, 'group_name'):
                await self.channel_layer.group_discard(self.group_name, self.channel_name)

        async def tenant_broadcast(self, event):
            await self.send_json(event)

        async def user_presence(self, event):
            """Presence updates can optionally be broadcast to entire tenant."""
            await self.send_json(event)

    CHANNELS_AVAILABLE = True

except ImportError:
    CHANNELS_AVAILABLE = False
    logger.info(
        'Django Channels not installed. WebSocket consumers disabled. '
        'Install with: pip install channels channels-redis'
    )
