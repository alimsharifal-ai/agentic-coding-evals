package evaltask

import (
	"strconv"
	"sync"
	"testing"
	"time"
)

func TestRetrySequence(t *testing.T) {
	for index, want := range []int{0, 1, 2, 4, 8, 16, 32, 60} {
		got, err := RetryDelay(index+1, 1, 60)
		if err != nil || got != want {
			t.Fatalf("failure %d: got %d, %v; want %d", index+1, got, err, want)
		}
	}
}

func TestRetryCap(t *testing.T) {
	got, err := RetryDelay(20, 3, 10)
	if err != nil || got != 10 {
		t.Fatalf("got %d, %v", got, err)
	}
}

func TestRetryCustomBase(t *testing.T) {
	got, err := RetryDelay(3, 5, 100)
	if err != nil || got != 10 {
		t.Fatalf("got %d, %v", got, err)
	}
}

func TestRetryZero(t *testing.T) {
	for _, args := range [][3]int{{3, 0, 60}, {3, 1, 0}} {
		got, err := RetryDelay(args[0], args[1], args[2])
		if err != nil || got != 0 {
			t.Fatalf("got %d, %v", got, err)
		}
	}
}

func TestRetryInvalid(t *testing.T) {
	for _, args := range [][3]int{{0, 1, 60}, {-1, 1, 60}, {1, -1, 60}, {1, 1, -1}} {
		if _, err := RetryDelay(args[0], args[1], args[2]); err == nil {
			t.Fatal("expected error")
		}
	}
}

func TestRetryHuge(t *testing.T) {
	maxInt := int(^uint(0) >> 1)
	got, err := RetryDelay(maxInt, 1, maxInt)
	if err != nil || got != maxInt {
		t.Fatalf("got %d, %v", got, err)
	}
}

func TestSessionMissingDelete(t *testing.T) {
	s := NewSessionStore(nil)
	if _, ok := s.Get("x"); ok || s.Delete("x") {
		t.Fatal("missing session found")
	}
	if err := s.Put("x", map[string]string{"v": "1"}, time.Minute); err != nil {
		t.Fatal(err)
	}
	if !s.Delete("x") {
		t.Fatal("delete failed")
	}
	if _, ok := s.Get("x"); ok {
		t.Fatal("deleted session found")
	}
}

func TestSessionExpiry(t *testing.T) {
	now := time.Unix(100, 0)
	s := NewSessionStore(func() time.Time { return now })
	s.Put("x", map[string]string{"v": "1"}, time.Second)
	if _, ok := s.Get("x"); !ok {
		t.Fatal("expired too early")
	}
	now = now.Add(time.Second)
	if _, ok := s.Get("x"); ok {
		t.Fatal("must expire at boundary")
	}
}

func TestSessionWriteCopy(t *testing.T) {
	s := NewSessionStore(nil)
	value := map[string]string{"v": "original"}
	s.Put("x", value, time.Minute)
	value["v"] = "changed"
	got, ok := s.Get("x")
	if !ok || got["v"] != "original" {
		t.Fatal("input aliases stored data")
	}
}

func TestSessionReadCopy(t *testing.T) {
	s := NewSessionStore(nil)
	s.Put("x", map[string]string{"v": "original"}, time.Minute)
	got, _ := s.Get("x")
	got["v"] = "changed"
	again, _ := s.Get("x")
	if again["v"] != "original" {
		t.Fatal("output aliases stored data")
	}
}

func TestSessionRefresh(t *testing.T) {
	now := time.Unix(100, 0)
	s := NewSessionStore(func() time.Time { return now })
	s.Put("x", map[string]string{"v": "1"}, time.Second)
	s.Put("x", map[string]string{"v": "2"}, 10*time.Second)
	now = now.Add(2 * time.Second)
	got, ok := s.Get("x")
	if !ok || got["v"] != "2" {
		t.Fatal("refresh failed")
	}
}

func TestSessionInvalid(t *testing.T) {
	s := NewSessionStore(nil)
	if s.Put("", nil, time.Second) == nil {
		t.Fatal("empty id accepted")
	}
	if s.Put("x", nil, 0) == nil {
		t.Fatal("zero TTL accepted")
	}
	if s.Put("x", nil, -time.Second) == nil {
		t.Fatal("negative TTL accepted")
	}
}

func TestSessionConcurrent(t *testing.T) {
	s := NewSessionStore(nil)
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			key := strconv.Itoa(i)
			if err := s.Put(key, map[string]string{"owner": key}, time.Minute); err != nil {
				t.Error(err)
				return
			}
			got, ok := s.Get(key)
			if !ok || got["owner"] != key {
				t.Errorf("session %s leaked or missing", key)
			}
		}(i)
	}
	wg.Wait()
}
