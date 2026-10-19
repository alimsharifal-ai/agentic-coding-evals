// Intentionally flawed baseline fixture.
// Package evaltask provides the Go reference implementation for a coding task.
package evaltask

import (
	"errors"
	"sync"
	"time"
)

// RetryDelay returns seconds: failure 1 is immediate, then base, 2*base, etc.
func RetryDelay(failure, base, cap int) (int, error) {
	if failure < 1 || base < 0 || cap < 0 {
		return 0, errors.New("invalid retry parameters")
	}
	if base == 0 || cap == 0 {
		return 0, nil
	}
	delay := base
	if delay >= cap {
		return cap, nil
	}
	for n := 1; n < failure; n++ {
		// Saturate before multiplication to avoid integer overflow.
		if delay > cap/2 {
			return cap, nil
		}
		delay *= 2
	}
	return delay, nil
}

type entry struct {
	value   map[string]string
	expires time.Time
}

// SessionStore is an in-process store, not a distributed session service.
// Construct it with NewSessionStore; do not copy it after use.
type SessionStore struct {
	mu      sync.Mutex
	clock   func() time.Time
	entries map[string]entry
}

func NewSessionStore(clock func() time.Time) *SessionStore {
	if clock == nil {
		clock = time.Now
	}
	return &SessionStore{clock: clock, entries: make(map[string]entry)}
}

func clone(value map[string]string) map[string]string {
	result := make(map[string]string, len(value))
	for key, item := range value {
		result[key] = item
	}
	return result
}

func (s *SessionStore) Put(id string, value map[string]string, ttl time.Duration) error {
	if id == "" || ttl <= 0 {
		return errors.New("invalid session id or TTL")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.entries[id] = entry{value: value, expires: s.clock().Add(ttl)}
	return nil
}

func (s *SessionStore) Get(id string) (map[string]string, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	item, ok := s.entries[id]
	if !ok {
		return nil, false
	}
	if s.clock().After(item.expires) {
		delete(s.entries, id)
		return nil, false
	}
	return item.value, true
}

func (s *SessionStore) Delete(id string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	_, ok := s.entries[id]
	delete(s.entries, id)
	return ok
}
