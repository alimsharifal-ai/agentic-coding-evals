"""Reference implementations for three small coding evaluation tasks."""
from copy import deepcopy
from threading import RLock


def merge_updates(updates):
    """Last duplicate wins; apply increasing revisions; never alias input data."""
    latest = {}
    for update in updates:
        latest[(update['user_id'], update['revision'])] = update
    profiles = {}
    for update in sorted(latest.values(), key=lambda row: row['revision']):
        profile = profiles.setdefault(update['user_id'], {})
        for key, value in update['changes'].items():
            if value is None:
                profile.pop(key, None)
            else:
                profile[key] = deepcopy(value)
    return profiles


def retry_delay(failure_number, base=1, cap=60):
    """First failure is immediate; later delays double up to cap."""
    if type(failure_number) is not int or failure_number < 1:
        raise ValueError('failure_number must be a positive integer')
    if type(base) is not int or type(cap) is not int or base < 0 or cap < 0:
        raise ValueError('base and cap must be nonnegative integers')
    if failure_number == 1 or base == 0 or cap == 0:
        return 0
    exponent = failure_number - 2
    if exponent >= cap.bit_length():
        return cap
    return min(base * (2 ** exponent), cap)


class SessionStore:
    """Thread-safe in-process TTL store with copy isolation; not distributed."""
    def __init__(self, clock):
        self.clock = clock
        self.sessions = {}
        self.lock = RLock()

    def put(self, session_id, data, ttl):
        if not isinstance(session_id, str) or not session_id:
            raise ValueError('session_id must be a nonempty string')
        if type(ttl) not in (int, float) or not 0 < ttl < float('inf'):
            raise ValueError('ttl must be finite and positive')
        with self.lock:
            self.sessions[session_id] = (self.clock() + ttl, deepcopy(data))

    def get(self, session_id):
        with self.lock:
            entry = self.sessions.get(session_id)
            if entry is None:
                return None
            expires, value = entry
            if self.clock() >= expires:
                del self.sessions[session_id]
                return None
            return deepcopy(value)

    def delete(self, session_id):
        with self.lock:
            return self.sessions.pop(session_id, None) is not None
