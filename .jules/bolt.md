## 2026-01-28 - Git Subprocess Optimization
**Learning:** `subprocess.run` has significant overhead (~3-5ms). For thousands of files, N+1 git calls (e.g. `git log -1`) are a massive bottleneck.
**Action:** Always prefer batching git commands. Streaming `git log` output for multiple files in one pass yielded a ~44x speedup compared to individual calls. Ensure to handle path relativization correctly as `git log` uses repo-relative paths.
