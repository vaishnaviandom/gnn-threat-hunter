# Phase 1 — macOS Native Telemetry (ESF Daemon)

This directory will contain the macOS Endpoint Security Framework (ESF) daemon
developed in **Phase 1**.

## What will be built here

A native macOS daemon (Swift or Rust) that:

1. Registers as an Endpoint Security client using Apple's ESF API
2. Subscribes to kernel-level events:
   - `ES_EVENT_TYPE_NOTIFY_EXEC` — process executions
   - `ES_EVENT_TYPE_NOTIFY_FORK` — process forks
   - `ES_EVENT_TYPE_NOTIFY_EXIT` — process terminations
   - `ES_EVENT_TYPE_NOTIFY_CREATE` — file creations
   - `ES_EVENT_TYPE_NOTIFY_WRITE` — file writes
   - `ES_EVENT_TYPE_NOTIFY_UNLINK` — file deletions
   - `ES_EVENT_TYPE_NOTIFY_OPEN` — file opens
3. Normalizes each event into the **OCSF v1.3 JSON format**
   (schema defined in `ingestion/src/schema/ocsf.rs` and `backend/ocsf/schemas.py`)
4. Produces each normalized event to Redpanda topic: `ocsf.telemetry.raw`

## Requirements (Phase 1)

- macOS 12.0+ (Monterey or later) — ESF requires Monterey+
- **System Extension entitlement** from Apple Developer Program
  (`com.apple.developer.endpoint-security.client`)
- Docker running (for Redpanda connection)

## Phase 0 Status

✅ OCSF schemas defined (Rust + Python)
✅ Redpanda topic configured in docker-compose.yml
✅ Ingestion Rust consumer ready to receive events
⏳ ESF daemon code — Phase 1

## Planned file structure

```
telemetry/
├── GNNTelemetryDaemon/        Swift package (ESF client)
│   ├── Package.swift
│   ├── Sources/
│   │   ├── ESFClient.swift    ESF event subscription
│   │   ├── OCSFNormalizer.swift  → OCSF JSON mapping
│   │   └── RedpandaProducer.swift  → Kafka producer
│   └── Tests/
└── README.md                  (this file)
```
