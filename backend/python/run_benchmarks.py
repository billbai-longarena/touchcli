"""
Comprehensive benchmark runner for TouchCLI performance SLA validation.
Runs all benchmark suites and generates a consolidated report.
"""

import json
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run_database_benchmarks():
    """Run database performance benchmarks"""
    logger.info("Starting database benchmarks...")
    
    try:
        from agent_service.benchmarks import run_all_benchmarks
        report = run_all_benchmarks()
        logger.info(f"✓ Database benchmarks complete - {len(report.get('results', {}))} tests")
        return report
    except Exception as e:
        logger.error(f"Database benchmarks failed: {e}")
        return {"error": str(e)}


async def run_websocket_benchmarks(ws_url: str = "ws://localhost:8080/ws"):
    """Run WebSocket performance benchmarks"""
    logger.info(f"Starting WebSocket benchmarks ({ws_url})...")
    
    try:
        from agent_service.websocket_benchmark import run_websocket_benchmarks
        report = await run_websocket_benchmarks(ws_url)
        logger.info(f"✓ WebSocket benchmarks complete")
        return report
    except Exception as e:
        logger.error(f"WebSocket benchmarks failed: {e}")
        return {"error": str(e)}


def main():
    """Run all benchmarks and generate report"""
    logger.info("=" * 70)
    logger.info("TouchCLI Performance Benchmark Suite")
    logger.info("=" * 70)
    
    ws_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8080/ws"
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "benchmarks": {
            "database": run_database_benchmarks(),
            "websocket": asyncio.run(run_websocket_benchmarks(ws_url))
        }
    }
    
    # Check overall SLA status
    db_passed = report["benchmarks"]["database"].get("sla_check", [True])[0]
    ws_passed = report["benchmarks"]["websocket"].get("sla_check", {}).get("passed", False)
    
    report["overall_sla_passed"] = db_passed and ws_passed
    
    # Print summary
    logger.info("=" * 70)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 70)
    
    if "error" not in report["benchmarks"]["database"]:
        db_results = report["benchmarks"]["database"].get("results", {})
        logger.info(f"\nDatabase Benchmarks: {len(db_results)} tests")
        for test_name, metrics in db_results.items():
            if "error" not in metrics:
                logger.info(
                    f"  {test_name}: p99={metrics.get('p99_ms', 0):.1f}ms "
                    f"(mean={metrics.get('mean_ms', 0):.1f}ms, "
                    f"samples={metrics.get('samples', 0)})"
                )
    
    ws_results = report["benchmarks"]["websocket"].get("results", {})
    logger.info(f"\nWebSocket Benchmarks: {len(ws_results)} tests")
    for test_name, metrics in ws_results.items():
        if "error" not in metrics:
            logger.info(
                f"  {test_name}: p99={metrics.get('p99_ms', 0):.1f}ms "
                f"(mean={metrics.get('mean_ms', 0):.1f}ms, "
                f"samples={metrics.get('samples', 0)})"
            )
    
    logger.info("=" * 70)
    sla_status = "✅ PASSED" if report["overall_sla_passed"] else "❌ FAILED"
    logger.info(f"Overall SLA Status: {sla_status}")
    logger.info("=" * 70)
    
    # Output JSON for parsing
    print(json.dumps(report, indent=2))
    
    return 0 if report["overall_sla_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
