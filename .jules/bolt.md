## 2025-01-30 - Double I/O in File Processing
**Learning:** The `process_file` function was reading the file twice (once for checksum, once for parsing). This is a common pattern when adding features (checksumming) without refactoring existing flows.
**Action:** When seeing multiple `open()` calls on the same file path in a function, check if the content can be shared.
