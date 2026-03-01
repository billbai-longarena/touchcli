"""
Database seeding - Initialize development/testing data
Usage: python -m agent_service.seeds [--clean]
"""

import asyncio
import logging
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import models
try:
    from .models import Base, User, Customer, Opportunity, Conversation, Message, AgentState
    from .db import SessionLocal, engine
except ImportError:
    from models import Base, User, Customer, Opportunity, Conversation, Message, AgentState
    from db import SessionLocal, engine

logger = logging.getLogger(__name__)


def create_test_data(db: Session):
    """Create sample data for development/testing"""
    
    # Check if data already exists
    existing_users = db.query(User).count()
    if existing_users > 0:
        logger.info(f"Database already seeded ({existing_users} users). Skipping.")
        return
    
    logger.info("Creating test data...")
    
    # Create test users (sales team)
    users = [
        User(
            id=uuid4(),
            email="alice.smith@touchcli.local",
            name="Alice Smith",
            role="salesperson",
            preferred_locale="en-US",
            phone_number="+1-555-0101",
        ),
        User(
            id=uuid4(),
            email="bob.johnson@touchcli.local",
            name="Bob Johnson",
            role="salesperson",
            preferred_locale="en-US",
            phone_number="+1-555-0102",
        ),
        User(
            id=uuid4(),
            email="carol.martinez@touchcli.local",
            name="Carol Martinez",
            role="sales_manager",
            preferred_locale="zh-CN",
            phone_number="+1-555-0103",
        ),
    ]
    
    db.add_all(users)
    db.commit()
    logger.info(f"✓ Created {len(users)} users")
    
    # Create test customers
    customers = [
        Customer(
            id=uuid4(),
            name="Acme Corporation",
            email="contact@acme-corp.com",
            phone="555-1000",
            company="Acme Corp",
            industry="Software",
            metadata={"tier": "enterprise", "location": "San Francisco"},
        ),
        Customer(
            id=uuid4(),
            name="TechStart Inc.",
            email="sales@techstart.io",
            phone="555-1001",
            company="TechStart",
            industry="AI/ML",
            metadata={"tier": "growth", "location": "Austin, TX"},
        ),
        Customer(
            id=uuid4(),
            name="Global Finance Ltd.",
            email="partnerships@globalfinance.com",
            phone="555-1002",
            company="Global Finance",
            industry="Financial Services",
            metadata={"tier": "enterprise", "location": "New York"},
        ),
    ]
    
    db.add_all(customers)
    db.commit()
    logger.info(f"✓ Created {len(customers)} customers")
    
    # Create opportunities
    opportunities = [
        Opportunity(
            id=uuid4(),
            customer_id=customers[0].id,
            title="Enterprise Platform License - Year 1",
            stage="negotiation",
            value=150000.00,
            close_date=datetime.utcnow() + timedelta(days=30),
            notes="Multi-year partnership. High priority.",
            metadata={"deal_size": "large", "contact": "John Doe"},
        ),
        Opportunity(
            id=uuid4(),
            customer_id=customers[1].id,
            title="API Integration Services",
            stage="proposal",
            value=45000.00,
            close_date=datetime.utcnow() + timedelta(days=14),
            notes="Custom API development for data pipeline.",
            metadata={"deal_size": "medium", "contact": "Sarah Chen"},
        ),
        Opportunity(
            id=uuid4(),
            customer_id=customers[2].id,
            title="Compliance & Security Audit",
            stage="prospecting",
            value=25000.00,
            close_date=datetime.utcnow() + timedelta(days=60),
            notes="Initial discovery call scheduled for next week.",
            metadata={"deal_size": "small", "contact": "Michael Lee"},
        ),
    ]
    
    db.add_all(opportunities)
    db.commit()
    logger.info(f"✓ Created {len(opportunities)} opportunities")
    
    # Create conversations
    conversations = [
        Conversation(
            id=uuid4(),
            user_id=users[0].id,
            customer_id=customers[0].id,
            opportunity_id=opportunities[0].id,
            title="Enterprise deal discussion",
            mode="text",
            type="sales",
            locale=users[0].preferred_locale,
            status="active",
            metadata={"agent_count": 3, "context": "Follow-up on proposal", "locale": users[0].preferred_locale},
        ),
        Conversation(
            id=uuid4(),
            user_id=users[1].id,
            customer_id=customers[1].id,
            opportunity_id=opportunities[1].id,
            title="Technical requirements gathering",
            mode="text",
            type="sales",
            locale=users[1].preferred_locale,
            status="active",
            metadata={"agent_count": 2, "context": "API integration scope", "locale": users[1].preferred_locale},
        ),
    ]
    
    db.add_all(conversations)
    db.commit()
    logger.info(f"✓ Created {len(conversations)} conversations")
    
    # Create sample messages
    messages = [
        Message(
            id=uuid4(),
            conversation_id=conversations[0].id,
            sender="user",
            content="Hi, I'd like to discuss the licensing terms for your platform.",
            role="user",
            metadata={"sentiment": "neutral"},
        ),
        Message(
            id=uuid4(),
            conversation_id=conversations[0].id,
            sender="agent",
            content="I'd be happy to help! Let me pull up the standard enterprise licensing options for you. Are you interested in 1-year or multi-year terms?",
            role="assistant",
            metadata={"agent": "sales_agent", "confidence": 0.95},
        ),
        Message(
            id=uuid4(),
            conversation_id=conversations[1].id,
            sender="user",
            content="Can you explain the API rate limits?",
            role="user",
            metadata={"sentiment": "neutral"},
        ),
        Message(
            id=uuid4(),
            conversation_id=conversations[1].id,
            sender="agent",
            content="Our API supports 10,000 requests per minute on the enterprise plan. Would you like to see performance benchmarks?",
            role="assistant",
            metadata={"agent": "data_agent", "confidence": 0.98},
        ),
    ]
    
    db.add_all(messages)
    db.commit()
    logger.info(f"✓ Created {len(messages)} messages")
    
    logger.info("✅ Database seeding complete!")


def clean_database():
    """Drop all tables and recreate schema"""
    logger.warning("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("Creating fresh schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database cleaned and recreated")


def main():
    """Seed database with test data"""
    import sys
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Clean if --clean flag provided
    if "--clean" in sys.argv:
        clean_database()
    
    # Create test data
    db = SessionLocal()
    try:
        create_test_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    main()
