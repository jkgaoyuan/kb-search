import argparse
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


BASE_URL = "http://localhost:8000"


def search_request(query: str) -> dict:
    start = time.time()
    try:
        resp = requests.get(f"{BASE_URL}/api/v1/search", params={"q": query}, timeout=10)
        duration = time.time() - start
        return {"status": resp.status_code, "duration": duration, "query": query}
    except Exception as e:
        return {"status": 0, "duration": time.time() - start, "error": str(e), "query": query}


def run_load_test(concurrent_users: int, total_requests: int, queries: list[str]):
    print(f"\n🚀 Starting load test: {concurrent_users} concurrent users, {total_requests} total requests\n")

    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = []
        for i in range(total_requests):
            q = queries[i % len(queries)]
            futures.append(executor.submit(search_request, q))

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 50 == 0 or completed == total_requests:
                print(f"  Progress: {completed}/{total_requests}")

    # Analysis
    durations = [r["duration"] for r in results if r["status"] == 200]
    errors = [r for r in results if r["status"] != 200]

    print("\n📊 Results:")
    print(f"  Total requests: {total_requests}")
    print(f"  Successful: {len(durations)}")
    print(f"  Errors: {len(errors)}")

    if durations:
        durations.sort()
        p50 = durations[int(len(durations) * 0.5)]
        p95 = durations[int(len(durations) * 0.95)]
        p99 = durations[int(len(durations) * 0.99)]
        avg = statistics.mean(durations)

        print(f"\n⏱️  Latency (seconds):")
        print(f"  Average: {avg:.3f}s")
        print(f"  P50:     {p50:.3f}s")
        print(f"  P95:     {p95:.3f}s")
        print(f"  P99:     {p99:.3f}s")
        print(f"  Min:     {durations[0]:.3f}s")
        print(f"  Max:     {durations[-1]:.3f}s")

        if p95 < 2.0:
            print("\n✅ P95 latency < 2s: PASS")
        else:
            print("\n❌ P95 latency >= 2s: FAIL")
    else:
        print("\n❌ No successful requests!")

    if errors:
        print(f"\n⚠️  Sample errors:")
        for e in errors[:5]:
            print(f"  {e.get('status')} | {e.get('error', 'Unknown')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KB Search Load Test")
    parser.add_argument("-u", "--users", type=int, default=20, help="Concurrent users")
    parser.add_argument("-n", "--requests", type=int, default=200, help="Total requests")
    parser.add_argument("--url", type=str, default=BASE_URL, help="Base URL")
    args = parser.parse_args()

    BASE_URL = args.url

    test_queries = [
        "Python",
        "部署",
        "Docker",
        "FastAPI",
        "数据库",
        "测试",
        "开发",
        "Linux",
        "监控",
        "日志",
    ]

    run_load_test(args.users, args.requests, test_queries)
