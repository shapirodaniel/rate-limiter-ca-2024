from collections import defaultdict


class Request:
    def __init__(self, source_ip: str, timestamp: int):
        self.source_ip = source_ip
        self.timestamp = timestamp


class RateLimiter:
    # history = { source_ip: { timestamp: total_requests }}
    history = defaultdict(lambda: defaultdict(int))

    def __init__(self, max_requests: int, max_requests_per_ip: int, window_size: int):
        self.max_requests = max_requests
        self.max_requests_per_ip = max_requests_per_ip
        self.window_size = window_size

    def getRequestsByIp(self, start: int, source_ip: str):
        total = 0
        for time in range(start, start + self.window_size + 1):
            total += self.history[source_ip][time] or 0
        return total

    def handle(self, request: Request):
        source_ip = request.source_ip
        timestamp = request.timestamp

        # optimistically update source_ip's request count
        self.history[source_ip][timestamp] += 1

        start = timestamp - self.window_size + 1
        per_ip_total = self.getRequestsByIp(start, source_ip)

        aggregate_total = 0
        for ip in self.history:
            aggregate_total += self.getRequestsByIp(start, ip)

        ok = (
            per_ip_total <= self.max_requests_per_ip
            and aggregate_total <= self.max_requests
        )

        # if request should be rate limited, remove from source_ip history
        if not ok:
            self.history[source_ip][timestamp] -= 1

        return ok


r = RateLimiter(10, 3, 2)

assert r.handle(Request("a", 10)) == True
assert r.handle(Request("b", 10)) == True
assert r.handle(Request("b", 10)) == True
assert r.handle(Request("b", 10)) == True
# 4th per IP request from 'b'
assert r.handle(Request("b", 10)) == False
assert r.handle(Request("c", 10)) == True
assert r.handle(Request("c", 10)) == True
assert r.handle(Request("c", 10)) == True
assert r.handle(Request("a", 10)) == True
assert r.handle(Request("a", 10)) == True
# 4th per IP request from 'a'
assert r.handle(Request("a", 11)) == False
assert r.handle(Request("a", 12)) == True
assert r.handle(Request("b", 12)) == True
assert r.handle(Request("c", 12)) == True
assert r.handle(Request("d", 12)) == True
assert r.handle(Request("e", 12)) == True
assert r.handle(Request("f", 12)) == True
assert r.handle(Request("g", 12)) == True
assert r.handle(Request("h", 12)) == True
assert r.handle(Request("j", 12)) == True
assert r.handle(Request("k", 12)) == True
# 11th aggregate request from timestamps 11-12
assert r.handle(Request("l", 12)) == False
