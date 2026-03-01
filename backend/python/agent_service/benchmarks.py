"""
Performance benchmarking module for TouchCLI Agent Service.
Measures database query latencies and API endpoint response times.
"""

import time
import asyncio
import statistics
from typing import Dict, List, Tuple
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text

# Import models
try:
    from .models import User, Customer, Opportunity, Conversation, Message
    from .db import SessionLocal
except ImportError:
    from models import User, Customer, Opportunity, Conversation, Message
    from db import SessionLocal


class PerformanceBenchmark:
    """Benchmarking suite for TouchCLI performance SLAs"""
    
    def __init__(self, db_session: Session = None):
        """Initialize benchmark with optional database session"""
        self.db = db_session or SessionLocal()
        self.results: Dict[str, List[float]] = {}
    
    def _measure(self, name: str, func, *args, **kwargs) -> float:
        """Measure execution time of a function in milliseconds"""
        start = time.perf_counter()
        try:
            func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            if name not in self.results:
                self.results[name] = []
            self.results[name].append(elapsed)
            return elapsed
    
    def _get_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0
        sorted_vals = sorted(values)
        index = int(len(sorted_vals) * percentile / 100)
        return sorted_vals[min(index, len(sorted_vals) - 1)]
    
    # ========================================================================
    # Database Query Benchmarks
    # ========================================================================
    
    def benchmark_user_insert(self, iterations: int = 100) -> Dict:
        """Benchmark user table insertion"""
        name = "user_insert"
        
        for i in range(iterations):
            def insert_user():
                user = User(
                    email=f"bench-user-{uuid4().hex[:8]}@test.local",
                    name=f"Benchmark User {i}",
                    role="salesperson"
                )
                self.db.add(user)
                self.db.commit()
            
            self._measure(name, insert_user)
        
        return self._summarize(name)
    
    def benchmark_user_query_by_id(self, iterations: int = 100) -> Dict:
        """Benchmark user lookup by ID"""
        name = "user_query_by_id"
        
        # Create a test user first
        test_user = User(
            email=f"bench-lookup-{uuid4().hex[:8]}@test.local",
            name="Benchmark Lookup Test",
            role="salesperson"
        )
        self.db.add(test_user)
        self.db.commit()
        user_id = test_user.id
        
        for i in range(iterations):
            def query_user():
                self.db.query(User).filter(User.id == user_id).first()
            
            self._measure(name, query_user)
        
        # Cleanup
        self.db.query(User).filter(User.id == user_id).delete()
        self.db.commit()
        
        return self._summarize(name)
    
    def benchmark_customer_bulk_insert(self, iterations: int = 50) -> Dict:
        """Benchmark bulk customer insertion"""
        name = "customer_bulk_insert"
        
        for i in range(iterations):
            def insert_customers():
                customers = [
                    Customer(
                        name=f"Customer {i}-{j}",
                        email=f"customer-{uuid4().hex[:8]}@test.local",
                        company=f"Company {i}-{j}",
                        industry="Technology"
                    )
                    for j in range(10)
                ]
                self.db.add_all(customers)
                self.db.commit()
            
            self._measure(name, insert_customers)
        
        return self._summarize(name)
    
    def benchmark_conversation_with_messages(self, iterations: int = 50) -> Dict:
        """Benchmark creating conversation with messages"""
        name = "conversation_with_messages"
        
        # Create test user and customer
        user = User(
            email=f"bench-user-{uuid4().hex[:8]}@test.local",
            name="Benchmark User",
            role="salesperson"
        )
        customer = Customer(
            name="Benchmark Customer",
            email=f"bench-customer-{uuid4().hex[:8]}@test.local",
            company="Benchmark Corp"
        )
        self.db.add(user)
        self.db.add(customer)
        self.db.commit()
        
        for i in range(iterations):
            def create_with_messages():
                conv = Conversation(
                    user_id=user.id,
                    customer_id=customer.id,
                    title=f"Benchmark Conversation {i}",
                    type="sales"
                )
                self.db.add(conv)
                self.db.flush()
                
                messages = [
                    Message(
                        conversation_id=conv.id,
                        sender="user",
                        content=f"Message {j}",
                        role="user"
                    )
                    for j in range(5)
                ]
                self.db.add_all(messages)
                self.db.commit()
            
            self._measure(name, create_with_messages)
        
        return self._summarize(name)
    
    def benchmark_complex_query(self, iterations: int = 100) -> Dict:
        """Benchmark complex query with joins and filtering"""
        name = "complex_query_with_joins"
        
        for i in range(iterations):
            def complex_query():
                self.db.query(Conversation).join(
                    User, Conversation.user_id == User.id
                ).join(
                    Customer, Conversation.customer_id == Customer.id
                ).filter(
                    Conversation.status == "active"
                ).limit(10).all()
            
            self._measure(name, complex_query)
        
        return self._summarize(name)
    
    def benchmark_full_text_search(self, iterations: int = 50) -> Dict:
        """Benchmark full-text search (if supported)"""
        name = "full_text_search"
        
        # Create some test messages first
        user = User(
            email=f"bench-search-{uuid4().hex[:8]}@test.local",
            name="Search User",
            role="salesperson"
        )
        customer = Customer(
            name="Search Customer",
            email=f"search-{uuid4().hex[:8]}@test.local",
            company="Search Corp"
        )
        self.db.add(user)
        self.db.add(customer)
        self.db.commit()
        
        conv = Conversation(
            user_id=user.id,
            customer_id=customer.id,
            title="Search Test",
            type="sales"
        )
        self.db.add(conv)
        self.db.flush()
        
        for i in range(5):
            msg = Message(
                conversation_id=conv.id,
                sender="user",
                content=f"Test message {i} with benchmark keywords",
                role="user"
            )
            self.db.add(msg)
        self.db.commit()
        
        for i in range(iterations):
            def fts_query():
                # Simple LIKE query (full-text search would be PostgreSQL specific)
                self.db.query(Message).filter(
                    Message.content.ilike("%benchmark%")
                ).all()
            
            self._measure(name, fts_query)
        
        return self._summarize(name)
    
    def benchmark_pagination(self, iterations: int = 100) -> Dict:
        """Benchmark paginated queries"""
        name = "pagination_query"
        
        for i in range(iterations):
            def paginate_query():
                page = i % 10  # Cycle through pages 0-9
                self.db.query(User).limit(20).offset(page * 20).all()
            
            self._measure(name, paginate_query)
        
        return self._summarize(name)
    
    # ========================================================================
    # Reporting
    # ========================================================================
    
    def _summarize(self, name: str) -> Dict:
        """Summarize benchmark results for a specific test"""
        if name not in self.results or not self.results[name]:
            return {"error": "no data"}
        
        values = self.results[name]
        return {
            "test": name,
            "samples": len(values),
            "min_ms": min(values),
            "max_ms": max(values),
            "mean_ms": statistics.mean(values),
            "median_ms": statistics.median(values),
            "p95_ms": self._get_percentile(values, 95),
            "p99_ms": self._get_percentile(values, 99),
            "stdev_ms": statistics.stdev(values) if len(values) > 1 else 0,
        }
    
    def report(self) -> Dict:
        """Generate comprehensive benchmark report"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "results": {name: self._summarize(name) for name in self.results.keys()}
        }
    
    def check_sla(self, sla_targets: Dict[str, int]) -> Tuple[bool, Dict]:
        """
        Check if benchmark results meet SLA targets.
        
        Args:
            sla_targets: Dict mapping test names to max p99 latency in ms
        
        Returns:
            (passed: bool, details: Dict with failures)
        """
        failures = {}
        
        for test_name, max_p99 in sla_targets.items():
            if test_name not in self.results:
                failures[test_name] = "test not run"
                continue
            
            summary = self._summarize(test_name)
            p99 = summary["p99_ms"]
            
            if p99 > max_p99:
                failures[test_name] = f"p99={p99:.1f}ms exceeds {max_p99}ms"
        
        passed = len(failures) == 0
        return passed, failures
    
    def cleanup(self):
        """Clean up test data from database"""
        try:
            # Clean up test data
            self.db.query(Message).filter(
                Message.content.like("%Benchmark%") | 
                Message.content.like("%benchmark%")
            ).delete()
            self.db.query(Conversation).filter(
                Conversation.title.like("%Benchmark%") |
                Conversation.title.like("%benchmark%")
            ).delete()
            self.db.query(User).filter(
                User.email.like("%bench-%")
            ).delete()
            self.db.query(Customer).filter(
                Customer.email.like("%bench-%")
            ).delete()
            self.db.commit()
        except Exception as e:
            print(f"Cleanup warning: {e}")
        finally:
            self.db.close()


def run_all_benchmarks() -> Dict:
    """Run complete benchmark suite"""
    benchmark = PerformanceBenchmark()
    
    try:
        results = {
            "user_insert": benchmark.benchmark_user_insert(100),
            "user_query_by_id": benchmark.benchmark_user_query_by_id(100),
            "customer_bulk_insert": benchmark.benchmark_customer_bulk_insert(50),
            "conversation_with_messages": benchmark.benchmark_conversation_with_messages(50),
            "complex_query": benchmark.benchmark_complex_query(100),
            "full_text_search": benchmark.benchmark_full_text_search(50),
            "pagination": benchmark.benchmark_pagination(100),
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "sla_check": benchmark.check_sla({
                "user_insert": 50,
                "user_query_by_id": 50,
                "customer_bulk_insert": 100,
                "conversation_with_messages": 200,
                "complex_query": 100,
                "full_text_search": 100,
                "pagination": 50,
            })
        }
    finally:
        benchmark.cleanup()


if __name__ == "__main__":
    import json
    report = run_all_benchmarks()
    print(json.dumps(report, indent=2))
