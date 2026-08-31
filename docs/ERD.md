# ERD, hermes-vacuum

> Not a real RDBMS, state is stored as JSON in `$HERMES_HOME/hermes-vacuum/` like `disk-cleanup` (`tracked.json`, `cleanup.log`). This ERD is a logical model to keep behavior consistent.

## 1. Mermaid ER Diagram

```mermaid
erDiagram
    CLEANUP_JOB ||--o{ SCANNED_FILE : contains
    CLEANUP_JOB ||--o{ SKIPPED_FILE : skipped
    CLEANUP_JOB ||--o{ CLEANUP_LOG : writes
    ALLOWLIST_RULE ||--o{ SCANNED_FILE : matches
    SCANNED_FILE ||--o| CLEANUP_LOG : deleted_as

    CLEANUP_JOB {
        string job_id PK "uuid, e.g. 20260830_131800_a1b2c3"
        datetime started_at
        datetime finished_at
        string mode "dry-run | quick | deep | status"
        string os "windows | macos | linux"
        bool is_admin
        string[] with_flags "npm,thumb,..."
        int total_scanned
        int total_deleted
        int total_skipped
        int bytes_reclaimed
        string status "preview | success | partial | blocked_no_admin"
    }

    ALLOWLIST_RULE {
        string rule_id PK "windows_user_temp, mac_caches, ..."
        string os
        string path_template "e.g. %TEMP%, ~/Library/Caches"
        string resolved_path "canonical realpath"
        string tier "quick | deep | optin"
        string category "temp | cache | dev | thumb | system_update"
        bool requires_admin
        string native_tool "e.g. npm cache clean, cleanmgr"
    }

    SCANNED_FILE {
        string file_id PK "hash(path+mtime)"
        string job_id FK
        string rule_id FK
        string path
        int size_bytes
        datetime mtime
        int age_days
        string tier
        string action "preview | deleted | skipped | confirm_needed"
        bool over_threshold ">500MB or >30d"
    }

    SKIPPED_FILE {
        string file_id FK
        string job_id FK
        string path
        string reason "LOCKED | ACCESS_DENIED | PATH_TOO_LONG | IN_USE"
        string error_class "PermissionError, OSError"
        datetime skipped_at
    }

    CLEANUP_LOG {
        string log_id PK "append-only line"
        string job_id FK
        datetime timestamp
        string level "TRACK | DELETE | SKIP | REJECT | BLOCK"
        string path
        string category
        int size_bytes
        string message
    }
```

## 2. File State Mapping (physical)

```
$HERMES_HOME/hermes-vacuum/
├── tracked.json          # array<SCANNED_FILE> + latest CLEANUP_JOB
│   {
│     "jobs": [ CLEANUP_JOB ],
│     "last_scan": { "at": "2026-08-30T13:18:00", "total": 842, "reclaimable": 1234567890 }
│   }
├── tracked.json.bak      # atomic write backup (like disk-cleanup)
└── cleanup.log           # append-only CLEANUP_LOG
    2026-08-30T13:18:00 DELETE /Temp/tmp_abc 12345 temp
    2026-08-30T13:18:01 SKIP   /Temp/locked.db 0 LOCKED PermissionError
```

## 3. Important Relations

- `CLEANUP_JOB 1-N SCANNED_FILE`, one scan job can produce thousands of files
- `ALLOWLIST_RULE 1-N SCANNED_FILE`, each file must trace to exactly one allowlist rule (audit)
- `SCANNED_FILE 1-0/1 SKIPPED_FILE`, if `action=skipped`, there is one skipped row with a reason
- `CLEANUP_LOG` is append-only, every `DELETE`/`SKIP`/`REJECT` writes a log line, never overwritten

## 4. Constraints (ponytail)

- `SCANNED_FILE.path` must satisfy `is_safe_path()==True`, if false do not insert into `SCANNED_FILE`, write a `REJECT` log directly
- `CLEANUP_JOB.is_admin==false` plus `mode==deep` plus `rule.requires_admin==true` results in `status=blocked_no_admin`, zero files deleted
- `SCANNED_FILE.over_threshold==true` plus `mode==quick` results in `action=confirm_needed`, never `deleted`
- `SKIPPED_FILE.reason` is a closed enum, never free text, so it can be aggregated ("37 LOCKED" not 37 different messages)

## 5. Example Queries (for `status`)

```python
# top 10 largest
sorted(scanned, key=lambda f: f.size_bytes, reverse=True)[:10]
# breakdown per category
group_by(scanned, lambda f: f.category) | sum(size)
# skipped summary
counter(skipped, key=lambda s: s.reason)  # {"LOCKED": 30, "ACCESS_DENIED": 7}
```
