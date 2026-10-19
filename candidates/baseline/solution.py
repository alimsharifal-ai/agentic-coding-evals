"""Intentionally flawed starting point. These bugs are evaluation fixtures."""


def merge_updates(updates):
    profiles = {}
    for update in updates:
        profiles.setdefault(update['user_id'], {}).update(update['changes'])
    return profiles


def retry_delay(failure_number, base=1, cap=60):
    return min(base * 2 ** (failure_number - 1), cap)


class SessionStore:
    def __init__(self, clock):
        self.clock = clock
        self.sessions = {}

    def put(self, session_id, data, ttl):
        self.sessions[session_id] = (self.clock() + ttl, data)

    def get(self, session_id):
        entry = self.sessions.get(session_id)
        if entry is None or self.clock() > entry[0]:
            return None
        return entry[1]

    def delete(self, session_id):
        return self.sessions.pop(session_id, None) is not None
