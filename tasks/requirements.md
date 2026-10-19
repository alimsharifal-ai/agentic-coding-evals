# Coding task contracts

Repair the supplied baseline. Keep public names and signatures unchanged.
Use only the standard library. Do not alter evaluation code, remove tests,
hard-code test answers, or access the reference implementation. Explain the
root cause and list the commands actually run. If a command cannot be run,
say so. Submit the updated `solution.py` or `solution.go` plus your explanation.

## Python: profile update merger

Implement `merge_updates(updates)` for valid records containing string
`user_id`, nonnegative integer `revision`, and dictionary `changes`.
Values are JSON-like and dictionary keys are strings.

- Deduplicate by `(user_id, revision)`, keeping the entire last occurrence.
- Apply remaining updates per user in ascending revision order.
- A `None` value deletes a top-level field. Deleting a missing field is harmless.
- All other values replace the field, including nested dictionaries.
- Retain an empty dictionary for a user whose fields were all removed.
- Return `{}` for empty input. Do not mutate input or share mutable values
  between input and output. Invalid record validation is out of scope.

## Python and Go: retry delay

Python interface: `retry_delay(failure_number, base=1, cap=60) -> int`.
Go interface: `RetryDelay(failure, base, cap int) (int, error)`.

- Failure 1 returns 0 seconds.
- Later failures return `min(base * 2^(failure-2), cap)` seconds.
- Failure must be a positive integer; base and cap must be nonnegative integers.
- Python rejects booleans and noninteger parameters with `ValueError`.
  Go returns an error for invalid integer parameters.
- Zero base or cap means zero delay. Very large failure counts should reach
  the cap efficiently, without overflow or building enormous powers.

## Python and Go: session store

Python interface: `SessionStore(clock)` with `put(id, data, ttl)`, `get(id)`
and `delete(id)`. Clock returns seconds, TTL is finite positive seconds,
and data is a JSON-like value. Missing or expired reads return `None`.

Go interface: `NewSessionStore(clock func() time.Time) *SessionStore`,
`Put(id string, value map[string]string, ttl time.Duration) error`,
`Get(id string) (map[string]string, bool)`, and `Delete(id string) bool`.
A nil Go clock uses `time.Now`. A nil Go map is accepted as an empty map.

- Reject empty/nonstring IDs in Python and empty IDs in Go when writing.
- Reject nonpositive TTLs; Python also rejects booleans, infinity and NaN.
- A session is expired when `now >= creation time + ttl`.
- Writing an existing session replaces its value and resets its expiry.
- Copy data on write and read so callers cannot alter stored state indirectly.
- Delete returns whether an entry existed, including an expired unread entry.
- Support concurrent method calls without corrupting data. Callers must not
  concurrently mutate an input map while Put copies it. Supplied clocks must
  themselves be safe to call. This is a local store, not a distributed service.
