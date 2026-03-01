"""
WebSocket performance benchmark for TouchCLI.
Measures round-trip time (RTT) for WebSocket message exchanges.
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Dict, List, Tuple
from uuid import uuid4

import websockets
from websockets.client import WebSocketClientProtocol


class WebSocketBenchmark:
    """WebSocket performance benchmarking"""
    
    def __init__(self, ws_url: str = "ws://localhost:8080/ws"):
        """Initialize WebSocket benchmark"""
        self.ws_url = ws_url
        self.results: Dict[str, List[float]] = {}
    
    async def measure_rtt(self, ws: WebSocketClientProtocol, payload: str) -> float:
        """Measure round-trip time for a message"""
        start = time.perf_counter()
        
        # Send message
        await ws.send(payload)
        
        # Wait for echo or response (simple echo test)
        response = await ws.recv()
        
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        return elapsed
    
    async def benchmark_message_rtt(self, iterations: int = 100) -> Dict:
        """Benchmark WebSocket message round-trip time"""
        name = "websocket_message_rtt"
        self.results[name] = []
        
        try:
            async with websockets.connect(self.ws_url) as ws:
                for i in range(iterations):
                    payload = json.dumps({
                        "type": "message",
                        "id": f"bench-{uuid4()}",
                        "conversation_id": str(uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "payload": {"content": f"Benchmark message {i}"}
                    })
                    
                    try:
                        rtt = await asyncio.wait_for(
                            self.measure_rtt(ws, payload),
                            timeout=5.0
                        )
                        self.results[name].append(rtt)
                    except asyncio.TimeoutError:
                        # Timeout counts as high latency
                        self.results[name].append(5000.0)
        except Exception as e:
            return {
                "error": f"WebSocket connection failed: {e}",
                "url": self.ws_url
            }
        
        return self._summarize(name)
    
    async def benchmark_concurrent_messages(self, concurrent_count: int = 10, messages_per: int = 10) -> Dict:
        """Benchmark concurrent WebSocket messages"""
        name = f"websocket_concurrent_{concurrent_count}"
        self.results[name] = []
        
        async def send_and_measure(ws: WebSocketClientProtocol):
            """Send multiple messages from one connection"""
            timings = []
            for i in range(messages_per):
                payload = json.dumps({
                    "type": "message",
                    "id": f"bench-concurrent-{uuid4()}",
                    "conversation_id": str(uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {"content": f"Concurrent message {i}"}
                })
                
                try:
                    rtt = await asyncio.wait_for(
                        self.measure_rtt(ws, payload),
                        timeout=5.0
                    )
                    timings.append(rtt)
                except asyncio.TimeoutError:
                    timings.append(5000.0)
            
            return timings
        
        try:
            tasks = []
            async with websockets.connect(self.ws_url) as ws:
                # Note: Real concurrency would need multiple connections
                # This is a simplified version that sends messages concurrently
                for i in range(concurrent_count):
                    task = send_and_measure(ws)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        self.results[name].extend(result)
        except Exception as e:
            return {
                "error": f"WebSocket benchmark failed: {e}",
                "url": self.ws_url
            }
        
        return self._summarize(name)
    
    async def benchmark_connection_setup(self, iterations: int = 100) -> Dict:
        """Benchmark WebSocket connection setup time"""
        name = "websocket_connection_setup"
        self.results[name] = []
        
        for i in range(iterations):
            start = time.perf_counter()
            try:
                async with websockets.connect(self.ws_url) as ws:
                    elapsed = (time.perf_counter() - start) * 1000
                    self.results[name].append(elapsed)
            except Exception as e:
                self.results[name].append(5000.0)
        
        return self._summarize(name)
    
    def _get_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from list of values"""
        if not values:
            return 0
        sorted_vals = sorted(values)
        index = int(len(sorted_vals) * percentile / 100)
        return sorted_vals[min(index, len(sorted_vals) - 1)]
    
    def _summarize(self, name: str) -> Dict:
        """Summarize benchmark results"""
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
    
    async def run_all_benchmarks(self) -> Dict:
        """Run complete WebSocket benchmark suite"""
        results = {
            "connection_setup": await self.benchmark_connection_setup(50),
            "message_rtt": await self.benchmark_message_rtt(100),
            "concurrent_messages": await self.benchmark_concurrent_messages(5, 10),
        }
        
        # Check SLA targets
        sla_targets = {
            "websocket_message_rtt": 100,  # p99 < 100ms
            "websocket_connection_setup": 200,  # p99 < 200ms
        }
        
        failures = {}
        for test_name, max_p99 in sla_targets.items():
            if test_name in results:
                p99 = results[test_name].get("p99_ms", 0)
                if p99 > max_p99:
                    failures[test_name] = f"p99={p99:.1f}ms exceeds {max_p99}ms"
        
        passed = len(failures) == 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "url": self.ws_url,
            "results": results,
            "sla_check": {
                "passed": passed,
                "failures": failures
            }
        }


async def run_websocket_benchmarks(ws_url: str = "ws://localhost:8080/ws") -> Dict:
    """Run WebSocket benchmarks"""
    benchmark = WebSocketBenchmark(ws_url)
    return await benchmark.run_all_benchmarks()


if __name__ == "__main__":
    import sys
    
    ws_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8080/ws"
    
    report = asyncio.run(run_websocket_benchmarks(ws_url))
    
    import json
    print(json.dumps(report, indent=2))
