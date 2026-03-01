"""
WebSocket RTT latency probe for S-005 performance SLA
Measures round-trip time for protocol ping/pong via WebSocket

Usage:
    python -m agent_service.s005_websocket_probe [--samples=50] [--url=ws://localhost:8080/ws]
"""

import asyncio
import time
import logging
import sys
from statistics import mean, median, quantiles
from typing import List, Tuple

try:
    import websockets
except ImportError:
    print("Error: websockets library required. Install with: pip install websockets")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def probe_websocket_rtt(
    url: str,
    samples: int = 50,
    timeout: float = 5.0
) -> Tuple[int, int, List[float]]:
    """
    Measure WebSocket RTT latency via heartbeat messages

    Args:
        url: WebSocket URL (e.g., ws://localhost:8080/ws)
        samples: Number of RTT measurements to take
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (success_count, failure_count, latency_list_ms)
    """
    latencies: List[float] = []
    success = 0
    failure = 0

    for i in range(samples):
        try:
            start_time = time.perf_counter() * 1000
            async with websockets.connect(url, open_timeout=timeout, close_timeout=timeout) as websocket:
                # Measure protocol-level RTT using ping/pong.
                pong_waiter = await websocket.ping()
                await asyncio.wait_for(pong_waiter, timeout=timeout)
            end_time = time.perf_counter() * 1000
            rtt_ms = end_time - start_time
            latencies.append(rtt_ms)
            success += 1

            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{samples} samples")

        except (asyncio.TimeoutError, TimeoutError):
            failure += 1
        except Exception as e:
            logger.debug(f"Sample {i + 1} failed: {e}")
            failure += 1

    return success, failure, latencies


def calculate_percentiles(values: List[float]) -> dict:
    """Calculate latency percentiles"""
    if not values:
        return {"p50": float("nan"), "p95": float("nan"), "p99": float("nan")}

    sorted_vals = sorted(values)

    try:
        # Python 3.8+ has quantiles
        quants = quantiles(sorted_vals, n=100)
        return {
            "p50": quants[49],  # 50th percentile
            "p95": quants[94],  # 95th percentile
            "p99": quants[98],  # 99th percentile
        }
    except (ValueError, IndexError):
        # Fallback for small samples
        return {
            "p50": sorted_vals[len(sorted_vals) // 2],
            "p95": sorted_vals[int(len(sorted_vals) * 0.95)],
            "p99": sorted_vals[int(len(sorted_vals) * 0.99)],
        }


async def main():
    """Run WebSocket RTT probe"""
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket RTT latency probe for S-005")
    parser.add_argument(
        "--samples",
        type=int,
        default=50,
        help="Number of RTT samples (default: 50)"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="ws://localhost:8080/ws",
        help="WebSocket URL (default: ws://localhost:8080/ws)"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Connection timeout in seconds (default: 5.0)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("S-005 WebSocket RTT Probe")
    logger.info("=" * 60)
    logger.info(f"URL: {args.url}")
    logger.info(f"Samples: {args.samples}")
    logger.info(f"Timeout: {args.timeout}s")
    logger.info("")

    try:
        success, failure, latencies = await probe_websocket_rtt(
            url=args.url,
            samples=args.samples,
            timeout=args.timeout
        )

        if success == 0:
            logger.error("No successful samples collected")
            return 1

        # Calculate statistics
        avg_ms = mean(latencies)
        median_ms = median(latencies)
        percentiles = calculate_percentiles(latencies)
        min_ms = min(latencies)
        max_ms = max(latencies)

        # Output results
        logger.info("")
        logger.info("Results:")
        logger.info(f"  Success: {success}/{args.samples}")
        logger.info(f"  Failure: {failure}/{args.samples}")
        logger.info("")
        logger.info("Latency Statistics (ms):")
        logger.info(f"  Min:  {min_ms:.3f}")
        logger.info(f"  p50:  {percentiles['p50']:.3f}")
        logger.info(f"  p95:  {percentiles['p95']:.3f}")
        logger.info(f"  p99:  {percentiles['p99']:.3f}")
        logger.info(f"  Avg:  {avg_ms:.3f}")
        logger.info(f"  Max:  {max_ms:.3f}")
        logger.info("")

        # Check SLA compliance (p99 < 100ms target)
        sla_target = 100
        print(
            f"websocket_rtt success={success} failure={failure} "
            f"p50_ms={percentiles['p50']:.3f} p95_ms={percentiles['p95']:.3f} "
            f"p99_ms={percentiles['p99']:.3f} avg_ms={avg_ms:.3f}"
        )
        if percentiles["p99"] < sla_target:
            logger.info(f"✓ WebSocket RTT within SLA (p99={percentiles['p99']:.3f}ms < {sla_target}ms)")
            return 0
        else:
            logger.warning(
                f"✗ WebSocket RTT exceeds SLA (p99={percentiles['p99']:.3f}ms >= {sla_target}ms)"
            )
            return 1

    except Exception as e:
        logger.error(f"Probe failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
