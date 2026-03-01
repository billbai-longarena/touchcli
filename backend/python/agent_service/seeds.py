"""
Database seeding script for development and testing.
Populates the database with sample data (users, customers, opportunities).

Run with: python -m agent_service.seeds
"""

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

try:
    from .db import SessionLocal, engine, init_db
    from .models import Base, User, Customer, Opportunity, Conversation
except ImportError:
    from db import SessionLocal, engine, init_db
    from models import Base, User, Customer, Opportunity, Conversation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_users(db: Session) -> dict:
    """Create sample users."""
    users = [
        User(
            id=uuid4(),
            name="Alice Salesperson",
            email="alice@touchcli.demo",
            role="salesperson",
            is_active=True
        ),
        User(
            id=uuid4(),
            name="Bob Sales Manager",
            email="bob@touchcli.demo",
            role="manager",
            is_active=True
        ),
        User(
            id=uuid4(),
            name="Carol Admin",
            email="carol@touchcli.demo",
            role="admin",
            is_active=True
        ),
    ]

    for user in users:
        existing = db.query(User).filter(User.email == user.email).first()
        if not existing:
            db.add(user)
            logger.info(f"✓ Created user: {user.name} ({user.role})")
        else:
            logger.info(f"⊘ User already exists: {user.email}")

    db.commit()

    # Return dict for reference in other seed functions
    return {user.email: user for user in users if not db.query(User).filter(User.email == user.email).first()}


def seed_customers(db: Session) -> dict:
    """Create sample customers."""
    customers = [
        Customer(
            id=uuid4(),
            name="Acme Corporation",
            customer_type="company",
            industry="Technology",
            email="contact@acme.demo",
            phone="+1-555-0100",
            company_size="500-1000",
            website="https://acme.demo",
            metadata={"source": "inbound", "priority": "high"}
        ),
        Customer(
            id=uuid4(),
            name="John Smith",
            customer_type="individual",
            industry="Finance",
            email="john.smith@finance.demo",
            phone="+1-555-0101",
            company_size=None,
            website=None,
            metadata={"source": "referral", "priority": "medium"}
        ),
        Customer(
            id=uuid4(),
            name="Tech Innovations Ltd",
            customer_type="company",
            industry="Software",
            email="sales@techinnovations.demo",
            phone="+1-555-0102",
            company_size="50-100",
            website="https://techinnovations.demo",
            metadata={"source": "cold_outreach", "priority": "low"}
        ),
    ]

    for customer in customers:
        existing = db.query(Customer).filter(Customer.email == customer.email).first()
        if not existing:
            db.add(customer)
            logger.info(f"✓ Created customer: {customer.name}")
        else:
            logger.info(f"⊘ Customer already exists: {customer.email}")

    db.commit()

    return {customer.email: customer for customer in customers}


def seed_opportunities(db: Session, customers: dict) -> dict:
    """Create sample opportunities linked to customers."""
    opportunities = []

    for email, customer in customers.items():
        opps = [
            Opportunity(
                id=uuid4(),
                customer_id=customer.id,
                name=f"Enterprise Solution - {customer.name}",
                description=f"Custom enterprise solution implementation",
                amount=50000.00,
                currency="USD",
                status="discovery",
                probability=0.3,
                expected_close_date=datetime.utcnow() + timedelta(days=60),
                metadata={"deal_type": "new", "decision_maker": "CEO"}
            ),
            Opportunity(
                id=uuid4(),
                customer_id=customer.id,
                name=f"Expansion - {customer.name}",
                description=f"Expansion of existing services",
                amount=25000.00,
                currency="USD",
                status="proposal",
                probability=0.6,
                expected_close_date=datetime.utcnow() + timedelta(days=30),
                metadata={"deal_type": "expansion", "decision_maker": "CTO"}
            ),
        ]
        opportunities.extend(opps)

    for opp in opportunities:
        existing = db.query(Opportunity).filter(
            Opportunity.customer_id == opp.customer_id,
            Opportunity.name == opp.name
        ).first()
        if not existing:
            db.add(opp)
            logger.info(f"✓ Created opportunity: {opp.name} (${opp.amount:,.2f})")
        else:
            logger.info(f"⊘ Opportunity already exists: {opp.name}")

    db.commit()

    return {opp.name: opp for opp in opportunities}


def seed_conversations(db: Session, users: dict, customers: dict, opportunities: dict) -> None:
    """Create sample conversations for testing."""
    # Get first user (Alice) for conversations
    alice = db.query(User).filter(User.email == "alice@touchcli.demo").first()
    if not alice:
        logger.warning("⊘ Alice user not found, skipping conversations")
        return

    # Get first customer and opportunity
    first_customer = next(iter(customers.values())) if customers else None
    first_opp = next(iter(opportunities.values())) if opportunities else None

    if not first_customer:
        logger.warning("⊘ No customers found, skipping conversations")
        return

    conversations = [
        Conversation(
            id=uuid4(),
            user_id=alice.id,
            customer_id=first_customer.id,
            opportunity_id=first_opp.id if first_opp else None,
            title=f"Discovery call - {first_customer.name}",
            type="sales",
            status="active",
            metadata={"started_by": "alice", "channel": "phone"}
        ),
    ]

    for conv in conversations:
        existing = db.query(Conversation).filter(
            Conversation.user_id == conv.user_id,
            Conversation.customer_id == conv.customer_id,
            Conversation.title == conv.title
        ).first()
        if not existing:
            db.add(conv)
            logger.info(f"✓ Created conversation: {conv.title}")
        else:
            logger.info(f"⊘ Conversation already exists: {conv.title}")

    db.commit()


def seed_database():
    """Run all seeding functions."""
    logger.info("Starting database seeding...")

    # Initialize tables
    try:
        init_db()
        logger.info("✓ Database tables initialized")
    except Exception as e:
        logger.warning(f"⊘ Database tables may already exist: {e}")

    db = SessionLocal()

    try:
        logger.info("\n--- Seeding Users ---")
        users = seed_users(db)
        logger.info(f"Completed: {len(users)} users")

        logger.info("\n--- Seeding Customers ---")
        customers = seed_customers(db)
        logger.info(f"Completed: {len(customers)} customers")

        logger.info("\n--- Seeding Opportunities ---")
        opportunities = seed_opportunities(db, customers)
        logger.info(f"Completed: {len(opportunities)} opportunities")

        logger.info("\n--- Seeding Conversations ---")
        seed_conversations(db, users, customers, opportunities)
        logger.info("Completed: conversations")

        logger.info("\n✅ Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}", exc_info=True)
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
