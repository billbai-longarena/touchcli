"""
Database query performance benchmark for S-005
Measures p99 latency for common queries: customers, opportunities, messages

Usage:
    python -m agent_service.s005_db_benchmark [--iterations=50]
"""

import time
import logging
import sys
from statistics import mean, median, quantiles
from typing import List, Dict
from uuid import uuid4

try:
    from .db import SessionLocal
    from .models import Customer, Opportunity, Message, Conversation, User
except ImportError:
    from db import SessionLocal
    from models import Customer, Opportunity, Message, Conversation, User

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def benchmark_query(query_name: str, query_func, iterations: int = 50) -> Dict[str, float]:
    """
    Run a query multiple times and measure latencies

    Args:
        query_name: Name of the query for logging
        query_func: Function that executes the query
        iterations: Number of times to run the query

    Returns:
        Dictionary with latency statistics (p50, p95, p99, avg, min, max)
    """
    latencies: List[float] = []

    logger.info(f"Benchmarking {query_name}...")

    for i in range(iterations):
        start_time = time.time() * 1000  # milliseconds

        try:
            query_func()
            end_time = time.time() * 1000
            latency_ms = end_time - start_time
            latencies.append(latency_ms)

            if (i + 1) % 10 == 0:
                logger.debug(f"  {query_name}: {i + 1}/{iterations} iterations")
        except Exception as e:
            logger.error(f"  Query failed: {e}")
            continue

    if not latencies:
        logger.error(f"  No successful queries for {query_name}")
        return {}

    # Calculate statistics
    sorted_vals = sorted(latencies)

    try:
        quants = quantiles(sorted_vals, n=100)
        stats = {
            "p50": quants[49],
            "p95": quants[94],
            "p99": quants[98],
        }
    except (ValueError, IndexError):
        stats = {
            "p50": sorted_vals[len(sorted_vals) // 2],
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
            "p99": sorted_vals[int(len(sorted_vals) * 0.99)],
        }

    stats.update({
        "avg": mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "count": len(latencies),
    })

    return stats


def benchmark_all(iterations: int = 50):
    """Run all database benchmarks"""
    db = SessionLocal()
    results: Dict[str, Dict[str, float]] = {}

    try:
        # Ensure we have test data
        if db.query(Customer).count() == 0:
            logger.warning("Database is empty. Seeding test data...")
            seed_test_data(db)

        # 1. Query: Get all customers
        def query_all_customers():
            db.query(Customer).all()

        results["customers_list"] = benchmark_query(
            "Query: Get all customers",
            query_all_customers,
            iterations
        )

        # 2. Query: Get customer by ID
        customer_id = db.query(Customer.id).first()[0]

        def query_customer_by_id():
            db.query(Customer).filter(Customer.id == customer_id).first()

        results["customer_by_id"] = benchmark_query(
            "Query: Get customer by ID",
            query_customer_by_id,
            iterations
        )

        # 3. Query: Get opportunities for customer
        def query_customer_opportunities():
            db.query(Opportunity).filter(
                Opportunity.customer_id == customer_id
            ).all()

        results["opportunities_by_customer"] = benchmark_query(
            "Query: Get opportunities by customer",
            query_customer_opportunities,
            iterations
        )

        # 4. Query: Get all opportunities
        def query_all_opportunities():
            db.query(Opportunity).all()

        results["opportunities_list"] = benchmark_query(
            "Query: Get all opportunities",
            query_all_opportunities,
            iterations
        )

        # 5. Query: Get opportunities by stage
        def query_opportunities_by_stage():
            db.query(Opportunity).filter(Opportunity.status == "proposal").all()

        results["opportunities_by_stage"] = benchmark_query(
            "Query: Get opportunities by stage",
            query_opportunities_by_stage,
            iterations
        )

        # 6. Query: Get conversation messages
        conversation_id = db.query(Conversation.id).first()
        if conversation_id:
            conversation_id = conversation_id[0]

            def query_conversation_messages():
                db.query(Message).filter(
                    Message.conversation_id == conversation_id
                ).all()

            results["messages_by_conversation"] = benchmark_query(
                "Query: Get messages by conversation",
                query_conversation_messages,
                iterations
            )

        # 7. Query: Complex query - Customer with opportunities and conversations
        def query_customer_full():
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                opps = db.query(Opportunity).filter(
                    Opportunity.customer_id == customer.id
                ).all()
                convs = db.query(Conversation).filter(
                    Conversation.customer_id == customer.id
                ).all()

        results["customer_full_context"] = benchmark_query(
            "Query: Customer with opportunities and conversations",
            query_customer_full,
            iterations
        )

    finally:
        db.close()

    return results


def seed_test_data(db):
    """Create minimal test data for benchmarking"""
    from datetime import datetime, timedelta

    logger.info("Creating test data...")

    # Create user
    user = User(
        id=uuid4(),
        name="Benchmark User",
        email=f"bench-{uuid4()}@test.local",
        role="salesperson",
        is_active=True
    )
    db.add(user)
    db.flush()

    # Create customers
    for i in range(10):
        customer = Customer(
            id=uuid4(),
            name=f"Benchmark Customer {i}",
            customer_type="company",
            email=f"customer{i}@test.local",
            industry="Technology"
        )
        db.add(customer)
        db.flush()

        # Create opportunities for each customer
        for j in range(3):
            opportunity = Opportunity(
                id=uuid4(),
                customer_id=customer.id,
                name=f"Opportunity {j} - Customer {i}",
                amount=50000.00 * (j + 1),
                status=["discovery", "proposal", "negotiation"][j % 3],
                probability=0.5 + (j * 0.1)
            )
            db.add(opportunity)
            db.flush()

        # Create conversation for customer
        conversation = Conversation(
            id=uuid4(),
            user_id=user.id,
            customer_id=customer.id,
            title=f"Conversation {i}",
            type="sales",
            status="active"
        )
        db.add(conversation)
        db.flush()

        # Create messages for conversation
        for k in range(5):
            message = Message(
                id=uuid4(),
                conversation_id=conversation.id,
                sender_id=user.id,
                sender_role="user" if k % 2 == 0 else "agent",
                content=f"Sample message {k}"
            )
            db.add(message)
            db.flush()

    db.commit()
    logger.info("✓ Test data created")


def print_results(results: Dict[str, Dict[str, float]]):
    """Pretty print benchmark results"""
    logger.info("")
    logger.info("=" * 80)
    logger.info("Database Query Performance Benchmark Results")
    logger.info("=" * 80)

    for query_name, stats in results.items():
        if not stats:
            continue

        logger.info("")
        logger.info(f"{query_name}:")
        logger.info(f"  Samples:  {stats.get('count', 0)}")
        logger.info(f"  Min:      {stats.get('min', 0):.3f}ms")
        logger.info(f"  p50:      {stats.get('p50', 0):.3f}ms")
        logger.info(f"  p95:      {stats.get('p95', 0):.3f}ms")
        logger.info(f"  p99:      {stats.get('p99', 0):.3f}ms")
        logger.info(f"  Avg:      {stats.get('avg', 0):.3f}ms")
        logger.info(f"  Max:      {stats.get('max', 0):.3f}ms")

        # Check SLA compliance (p99 < 50ms target)
        p99 = stats.get("p99", 0)
        if p99 < 50:
            logger.info(f"  Status:   ✓ Within SLA (p99 < 50ms)")
        else:
            logger.info(f"  Status:   ✗ Exceeds SLA (p99 >= 50ms)")

    # Summary
    logger.info("")
    logger.info("=" * 80)

    all_p99_compliant = all(
        stats.get("p99", float("inf")) < 50
        for stats in results.values()
        if stats
    )

    if all_p99_compliant:
        logger.info("✓ All queries within SLA (p99 < 50ms)")
        return 0
    else:
        logger.info("✗ Some queries exceed SLA (p99 >= 50ms)")
        return 1


def main():
    """Run database benchmark"""
    import argparse

    parser = argparse.ArgumentParser(description="Database query performance benchmark for S-005")
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of iterations per query (default: 50)"
    )

    args = parser.parse_args()

    try:
        results = benchmark_all(iterations=args.iterations)
        return print_results(results)
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
