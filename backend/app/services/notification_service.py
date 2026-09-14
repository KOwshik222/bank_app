"""
Notification service — simulated email/SMS notifications for banking events.
"""

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.events import Event, get_event_bus

logger = logging.getLogger(__name__)


# In-memory notification store for the simulation
_notifications: list[dict] = []


class NotificationService:
    """Simulates banking notifications (email, SMS, push)."""

    def __init__(self):
        self.event_bus = get_event_bus()

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        correlation_id: str | None = None,
    ) -> dict:
        """Simulate sending an email notification."""
        notification = {
            "id": str(uuid4()),
            "type": "EMAIL",
            "to": to,
            "subject": subject,
            "body": body,
            "status": "SENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }
        _notifications.append(notification)
        logger.info(f"Email sent to {to}: {subject}")

        await self.event_bus.publish(
            Event(
                topic="notification.sent",
                payload=notification,
                correlation_id=correlation_id,
                source_service="notification-service",
            )
        )
        return notification

    async def send_sms(
        self,
        to: str,
        message: str,
        correlation_id: str | None = None,
    ) -> dict:
        """Simulate sending an SMS notification."""
        notification = {
            "id": str(uuid4()),
            "type": "SMS",
            "to": to,
            "message": message,
            "status": "SENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
        }
        _notifications.append(notification)
        logger.info(f"SMS sent to {to}: {message[:50]}...")

        await self.event_bus.publish(
            Event(
                topic="notification.sent",
                payload=notification,
                correlation_id=correlation_id,
                source_service="notification-service",
            )
        )
        return notification

    async def send_incident_alert(
        self,
        incident_number: str,
        severity: str,
        title: str,
        affected_service: str,
    ) -> dict:
        """Send incident alert to the operations team."""
        subject = f"[{severity}] Incident {incident_number}: {title}"
        body = (
            f"A {severity} incident has been reported.\n\n"
            f"Incident: {incident_number}\n"
            f"Title: {title}\n"
            f"Affected Service: {affected_service}\n\n"
            f"AI investigation has been initiated."
        )
        return await self.send_email(
            to="ops-team@bankops.ai",
            subject=subject,
            body=body,
            correlation_id=incident_number,
        )

    @staticmethod
    def get_notifications(limit: int = 50) -> list[dict]:
        """Retrieve recent notifications."""
        return _notifications[-limit:]
