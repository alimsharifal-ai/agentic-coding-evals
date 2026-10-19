# Validation performed

Created as a new sample project on 2026-10-19.

| Validation | Observed result |
| --- | --- |
| Python reference | 19 of 19 behavioral checks passed |
| Python intentionally flawed baseline | 8 of 19 passed; 11 deliberate failures detected |
| Go reference | 13 of 13 behavioral checks passed |
| Go intentionally flawed baseline | 8 of 13 passed; 5 deliberate failures detected |
| Go race detector | `go test -race ./...` passed |
| Harness checks | 3 passed: differentiation, import errors, timeout handling |
| Python pairwise comparison | Identified all 11 changed checks |

Go was formatted with gofmt and validated with Go 1.27.2. The Go tests include
1,000 concurrent in-process session operations. The Python concurrency check
uses 16 worker threads for 1,000 distinct sessions. Neither is a production
capacity benchmark or a distributed deployment test.

The reports under `examples/verified-runs` are actual local runs of handcrafted
fixtures, not an evaluation of a named AI model. Human review remains pending.
