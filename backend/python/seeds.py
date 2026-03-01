#!/usr/bin/env python3
"""
Database Seed Script for TouchCLI

Purpose: Populate database with demo/test data
Usage: python -m agent_service.seeds [--env development|staging|production]

This script creates:
- Demo users
- Demo customers
- Demo opportunities
- Demo conversations
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

# Import models (adjust based on your actual model structure)
try:
    from agent_service.models import (
        User,
        Customer,
        Opportunity,
        Conversation,
        Message,
    )
    from agent_service.models import Base
except ImportError:
    print("Error: Could not import models. Ensure models.py exists.")
    sys.exit(1)


class DatabaseSeeder:
    """Database seeding utility"""

    def __init__(self, database_url: str):
        """Initialize seeder with database connection"""
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session: Session = Session()

    def clear_data(self, confirm: bool = False) -> None:
        """Clear all seed data from database"""
        if not confirm:
            print("⚠️  Clear data requires confirmation")
            response = input("Clear all seed data? (yes/no): ")
            if response.lower() != "yes":
                print("Cancelled")
                return

        try:
            # Delete in reverse order of dependencies
            self.session.query(Message).delete()
            self.session.query(Conversation).delete()
            self.session.query(Opportunity).delete()
            self.session.query(Customer).delete()
            self.session.query(User).delete()
            self.session.commit()
            print("✓ Database cleared successfully")
        except Exception as e:
            self.session.rollback()
            print(f"✗ Error clearing data: {e}")

    def seed_users(self) -> list[User]:
        """Create demo users"""
        print("\n📝 Seeding users...")

        users = [
            User(
                id="user-demo-001",
                name="Alice Johnson",
                email="alice@example.com",
                role="admin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            User(
                id="user-demo-002",
                name="Bob Smith",
                email="bob@example.com",
                role="salesperson",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
            User(
                id="user-demo-003",
                name="Carol White",
                email="carol@example.com",
                role="salesperson",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]

        for user in users:
            try:
                self.session.add(user)
                self.session.commit()
                print(f"  ✓ User: {user.name}")
            except IntegrityError:
                self.session.rollback()
                print(f"  - User already exists: {user.name}")

        return users

    def seed_customers(self, users: list[User]) -> list[Customer]:
        """Create demo customers"""
        print("\n👥 Seeding customers...")

        customers = [
            Customer(
                id="cust-demo-001",
                user_id=users[0].id,
                name="Acme Corporation",
                email="contact@acme.com",
                phone="+1-555-0100",
                company_size="large",
                industry="Technology",
                created_at=datetime.utcnow() - timedelta(days=30),
                updated_at=datetime.utcnow(),
            ),
            Customer(
                id="cust-demo-002",
                user_id=users[1].id,
                name="TechStart Inc",
                email="hello@techstart.com",
                phone="+1-555-0101",
                company_size="small",
                industry="Software",
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow(),
            ),
            Customer(
                id="cust-demo-003",
                user_id=users[1].id,
                name="Global Solutions Ltd",
                email="info@globalsol.com",
                phone="+1-555-0102",
                company_size="medium",
                industry="Consulting",
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow(),
            ),
            Customer(
                id="cust-demo-004",
                user_id=users[2].id,
                name="Innovation Labs",
                email="contact@innovate.com",
                phone="+1-555-0103",
                company_size="medium",
                industry="Research & Development",
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow(),
            ),
        ]

        for customer in customers:
            try:
                self.session.add(customer)
                self.session.commit()
                print(f"  ✓ Customer: {customer.name}")
            except IntegrityError:
                self.session.rollback()
                print(f"  - Customer already exists: {customer.name}")

        return customers

    def seed_opportunities(self, customers: list[Customer]) -> list[Opportunity]:
        """Create demo opportunities"""
        print("\n💼 Seeding opportunities...")

        opportunities = [
            Opportunity(
                id="opp-demo-001",
                customer_id=customers[0].id,
                title="Enterprise License Deal",
                description="Annual enterprise software license for 500+ users",
                amount=250000,
                stage="Proposal",
                expected_close_date=datetime.utcnow() + timedelta(days=30),
                created_at=datetime.utcnow() - timedelta(days=20),
                updated_at=datetime.utcnow(),
            ),
            Opportunity(
                id="opp-demo-002",
                customer_id=customers[1].id,
                title="Startup Growth Package",
                description="Growth package for early-stage SaaS company",
                amount=50000,
                stage="Negotiation",
                expected_close_date=datetime.utcnow() + timedelta(days=14),
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow(),
            ),
            Opportunity(
                id="opp-demo-003",
                customer_id=customers[2].id,
                title="Multi-year Consulting Services",
                description="3-year consulting engagement",
                amount=500000,
                stage="Prospecting",
                expected_close_date=datetime.utcnow() + timedelta(days=60),
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow(),
            ),
            Opportunity(
                id="opp-demo-004",
                customer_id=customers[3].id,
                title="Research Collaboration",
                description="Joint research and development initiative",
                amount=150000,
                stage="Closed Won",
                expected_close_date=datetime.utcnow() - timedelta(days=5),
                created_at=datetime.utcnow() - timedelta(days=45),
                updated_at=datetime.utcnow() - timedelta(days=5),
            ),
        ]

        for opp in opportunities:
            try:
                self.session.add(opp)
                self.session.commit()
                print(f"  ✓ Opportunity: {opp.title} (${opp.amount:,})")
            except IntegrityError:
                self.session.rollback()
                print(f"  - Opportunity already exists: {opp.title}")

        return opportunities

    def seed_conversations(self, customers: list[Customer]) -> list[Conversation]:
        """Create demo conversations"""
        print("\n💬 Seeding conversations...")

        conversations = [
            Conversation(
                id="conv-demo-001",
                user_id="user-demo-001",
                customer_id=customers[0].id,
                title="Initial Discovery Call - Acme",
                status="active",
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow(),
            ),
            Conversation(
                id="conv-demo-002",
                user_id="user-demo-002",
                customer_id=customers[1].id,
                title="Technical Requirements Review",
                status="active",
                created_at=datetime.utcnow() - timedelta(days=5),
                updated_at=datetime.utcnow(),
            ),
            Conversation(
                id="conv-demo-003",
                user_id="user-demo-002",
                customer_id=customers[2].id,
                title="Proposal Discussion",
                status="closed",
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow() - timedelta(days=7),
            ),
        ]

        for conv in conversations:
            try:
                self.session.add(conv)
                self.session.commit()
                print(f"  ✓ Conversation: {conv.title}")
            except IntegrityError:
                self.session.rollback()
                print(f"  - Conversation already exists: {conv.title}")

        return conversations

    def seed_messages(self, conversations: list[Conversation]) -> None:
        """Create demo messages"""
        print("\n✉️  Seeding messages...")

        messages = [
            Message(
                id="msg-demo-001",
                conversation_id=conversations[0].id,
                user_id="user-demo-001",
                content="Hi, thanks for scheduling this call. Let's discuss your needs.",
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow() - timedelta(days=10),
            ),
            Message(
                id="msg-demo-002",
                conversation_id=conversations[0].id,
                user_id="user-demo-001",
                content="We're looking for an enterprise solution for 500+ users.",
                created_at=datetime.utcnow() - timedelta(days=10, hours=1),
                updated_at=datetime.utcnow() - timedelta(days=10, hours=1),
            ),
            Message(
                id="msg-demo-003",
                conversation_id=conversations[1].id,
                user_id="user-demo-002",
                content="Let's review the technical requirements for your platform.",
                created_at=datetime.utcnow() - timedelta(days=5),
                updated_at=datetime.utcnow() - timedelta(days=5),
            ),
        ]

        for msg in messages:
            try:
                self.session.add(msg)
                self.session.commit()
                print(f"  ✓ Message in: {msg.conversation_id}")
            except IntegrityError:
                self.session.rollback()
                print(f"  - Message already exists in: {msg.conversation_id}")

    def run(self, clear_first: bool = False) -> None:
        """Run full seeding process"""
        try:
            print("=" * 50)
            print("TouchCLI Database Seeding")
            print("=" * 50)

            if clear_first:
                self.clear_data(confirm=True)

            # Seed in order of dependencies
            users = self.seed_users()
            customers = self.seed_customers(users)
            opportunities = self.seed_opportunities(customers)
            conversations = self.seed_conversations(customers)
            self.seed_messages(conversations)

            print("\n" + "=" * 50)
            print("✓ Seeding complete!")
            print("=" * 50)

            # Show summary
            print("\nDatabase Summary:")
            print(f"  Users: {self.session.query(User).count()}")
            print(f"  Customers: {self.session.query(Customer).count()}")
            print(f"  Opportunities: {self.session.query(Opportunity).count()}")
            print(f"  Conversations: {self.session.query(Conversation).count()}")
            print(f"  Messages: {self.session.query(Message).count()}")

        except Exception as e:
            print(f"\n✗ Seeding failed: {e}")
            self.session.rollback()
            sys.exit(1)
        finally:
            self.session.close()


def main():
    """Main entry point"""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Parse arguments
    clear_first = "--clear" in sys.argv
    env = "development"

    for arg in sys.argv[1:]:
        if arg.startswith("--env="):
            env = arg.split("=")[1]

    print(f"Environment: {env}")
    print(f"Database: {database_url}")

    # Create seeder and run
    seeder = DatabaseSeeder(database_url)
    seeder.run(clear_first=clear_first)


if __name__ == "__main__":
    main()
