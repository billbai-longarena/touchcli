"""
Celery task definitions for async job processing
Handles long-running operations like message processing, exports, and syncs
"""

import os
from celery import Celery
from celery.utils.log import get_task_logger
from datetime import datetime
from uuid import UUID

# Initialize Celery app
celery_app = Celery(
    "touchcli",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit (for cleanup)
    broker_connection_retry_on_startup=True,
    # Task routing
    task_routes={
        "agent_service.tasks.process_message": {"queue": "messages"},
        "agent_service.tasks.export_data": {"queue": "exports"},
        "agent_service.tasks.sync_external_system": {"queue": "sync"},
    },
)

logger = get_task_logger(__name__)


# ============================================================================
# Message Processing Tasks
# ============================================================================

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=60,  # Retry after 60 seconds
)
def process_message(
    self,
    conversation_id: str,
    user_id: str,
    message_content: str,
    customer_id: str = None,
    opportunity_id: str = None,
):
    """
    Process user message through agent workflow.

    Args:
        conversation_id: Conversation UUID
        user_id: User UUID
        message_content: Message text content
        customer_id: Optional customer context
        opportunity_id: Optional opportunity context

    Returns:
        Result with agent response and actions
    """
    try:
        logger.info(f"Processing message in conversation {conversation_id}")

        # Import here to avoid circular imports
        from agent_service.db import SessionLocal
        from agent_service.workflow import ConversationWorkflow

        db = SessionLocal()

        try:
            workflow = ConversationWorkflow(db)
            result = workflow.process_message(
                conversation_id=UUID(conversation_id),
                user_id=UUID(user_id),
                message=message_content,
                customer_id=UUID(customer_id) if customer_id else None,
                opportunity_id=UUID(opportunity_id) if opportunity_id else None,
            )

            logger.info(f"Message processing completed: {result}")
            return result

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        # Celery will retry due to autoretry_for
        raise


# ============================================================================
# Data Export Tasks
# ============================================================================

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2},
    default_retry_delay=120,
)
def export_data(self, export_type: str, user_id: str, filters: dict = None):
    """
    Export data to CSV or PDF.

    Args:
        export_type: Type of export (customers, opportunities, conversations)
        user_id: User requesting export
        filters: Optional filtering criteria

    Returns:
        Export file path or URL
    """
    try:
        logger.info(f"Starting {export_type} export for user {user_id}")

        from agent_service.db import SessionLocal

        db = SessionLocal()

        try:
            if export_type == "customers":
                return _export_customers(db, filters)
            elif export_type == "opportunities":
                return _export_opportunities(db, filters)
            elif export_type == "conversations":
                return _export_conversations(db, filters)
            else:
                raise ValueError(f"Unknown export type: {export_type}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise


def _export_customers(db, filters):
    """Export customer data"""
    from agent_service.models import Customer
    import csv
    import tempfile

    customers = db.query(Customer).all()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Name', 'Type', 'Email', 'Phone', 'Created At'])

        for customer in customers:
            writer.writerow([
                str(customer.id),
                customer.name,
                customer.type,
                customer.email,
                customer.phone,
                customer.created_at.isoformat(),
            ])

        return f.name


def _export_opportunities(db, filters):
    """Export opportunity data"""
    from agent_service.models import Opportunity
    import csv
    import tempfile

    opportunities = db.query(Opportunity).all()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Customer', 'Name', 'Amount', 'Status', 'Probability', 'Expected Close'])

        for opp in opportunities:
            writer.writerow([
                str(opp.id),
                opp.customer.name if opp.customer else '',
                opp.name,
                opp.amount,
                opp.status,
                opp.probability,
                opp.expected_close_date.isoformat() if opp.expected_close_date else '',
            ])

        return f.name


def _export_conversations(db, filters):
    """Export conversation data"""
    from agent_service.models import Conversation
    import csv
    import tempfile

    conversations = db.query(Conversation).all()

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'User', 'Customer', 'Status', 'Mode', 'Created At', 'Message Count'])

        for conv in conversations:
            writer.writerow([
                str(conv.id),
                conv.user.name if conv.user else '',
                conv.customer.name if conv.customer else '',
                conv.status,
                conv.mode,
                conv.created_at.isoformat(),
                len(conv.messages) if conv.messages else 0,
            ])

        return f.name


# ============================================================================
# Sync Tasks
# ============================================================================

@celery_app.task(bind=True, default_retry_delay=300)
def sync_external_system(self, system_name: str):
    """
    Sync data with external CRM systems.

    Args:
        system_name: Name of external system (salesforce, hubspot, etc.)

    Returns:
        Sync status and record count
    """
    try:
        logger.info(f"Starting sync with {system_name}")

        # TODO: Implement external system sync
        # This would integrate with APIs like Salesforce, HubSpot, etc.

        result = {
            "system": system_name,
            "status": "completed",
            "records_synced": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(f"Sync completed: {result}")
        return result

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        # Celery will retry
        raise


# ============================================================================
# Notification Tasks
# ============================================================================

@celery_app.task(bind=True, default_retry_delay=60)
def send_notification(self, notification_type: str, user_id: str, data: dict):
    """
    Send notifications (email, SMS, push).

    Args:
        notification_type: Type of notification (email, sms, push)
        user_id: Target user UUID
        data: Notification data (subject, body, etc.)

    Returns:
        Delivery status
    """
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}")

        # TODO: Implement actual notification sending
        # For now, just log
        logger.info(f"Notification data: {data}")

        return {
            "status": "sent",
            "type": notification_type,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Notification sending failed: {e}")
        raise


# ============================================================================
# Utility Tasks
# ============================================================================

@celery_app.task
def health_check():
    """Health check task to verify Celery is operational"""
    logger.info("Health check - Celery is operational")
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
