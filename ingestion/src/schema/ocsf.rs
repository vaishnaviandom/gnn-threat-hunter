//! OCSF (Open Cybersecurity Schema Framework) v1.3 data contracts.
//!
//! These structs define the canonical event format emitted by the macOS
//! ESF telemetry daemon (Phase 1) and consumed by the Rust ingestion engine
//! (Phase 3). All downstream components — graph builder, GNN trainer, XAI
//! triage — rely on this single source of truth.
//!
//! Reference: https://schema.ocsf.io/

use serde::{Deserialize, Serialize};

// ─────────────────────────────────────────────────────────────────────────────
// Shared sub-objects
// ─────────────────────────────────────────────────────────────────────────────

/// Represents a network endpoint (source or destination).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Endpoint {
    /// IP address (v4 or v6). Optional — file events may omit this.
    pub ip: Option<String>,
    /// Hostname / FQDN.
    pub hostname: Option<String>,
    /// Unique identifier for this host (e.g., macOS hardware UUID).
    pub uid: Option<String>,
    /// Operating system name.
    pub os_name: Option<String>,
}

/// Represents an OS process.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Process {
    /// Process ID.
    pub pid: u32,
    /// Parent process ID.
    pub parent_pid: Option<u32>,
    /// Name of the executable (e.g., "bash").
    pub name: String,
    /// Full path to the executable binary.
    pub exe: Option<String>,
    /// Command-line arguments.
    pub cmd_line: Option<String>,
    /// Unix user running the process.
    pub user: Option<String>,
    /// SHA-256 hash of the executable binary (for Node ID derivation).
    pub exe_hash_sha256: Option<String>,
}

/// Represents a file system object.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileObject {
    /// Absolute path to the file.
    pub path: String,
    /// File name without directory.
    pub name: String,
    /// MIME type, if determinable.
    pub mime_type: Option<String>,
    /// SHA-256 of file contents (populated on read/exec events).
    pub hash_sha256: Option<String>,
    /// File size in bytes.
    pub size: Option<u64>,
}

/// MITRE ATT&CK tactic/technique mapping (populated by threat intel — Phase 6).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MitreAttack {
    pub tactic: Option<String>,
    pub technique_id: Option<String>,
    pub technique_name: Option<String>,
}

// ─────────────────────────────────────────────────────────────────────────────
// OCSF Activity IDs
// (https://schema.ocsf.io/classes/process_activity)
// ─────────────────────────────────────────────────────────────────────────────

/// Numeric activity codes aligned to the OCSF standard.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ActivityId {
    Unknown = 0,
    Launch = 1,
    Terminate = 2,
    Open = 3,
    Read = 4,
    Write = 5,
    Delete = 6,
    Rename = 7,
    Execute = 8,
    NetworkConnect = 9,
    NetworkDisconnect = 10,
}

// ─────────────────────────────────────────────────────────────────────────────
// OCSF Class IDs
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ClassId {
    /// OCSF 4001 — Process Activity
    ProcessActivity = 4001,
    /// OCSF 4004 — File System Activity
    FileActivity = 4004,
    /// OCSF 4003 — Network Activity  
    NetworkActivity = 4003,
}

// ─────────────────────────────────────────────────────────────────────────────
// Root OCSF Event Envelope
// ─────────────────────────────────────────────────────────────────────────────

/// The canonical OCSF event envelope.
///
/// Every event produced by the macOS ESF daemon (Phase 1) and consumed
/// by the Rust ingestion engine (Phase 3) **must** conform to this schema.
///
/// # Example (JSON)
/// ```json
/// {
///   "class_uid": 4001,
///   "activity_id": 1,
///   "time": 1720000000000,
///   "message": "Process launched",
///   "src_endpoint": { "hostname": "macbook-pro.local", "uid": "ABC-123" },
///   "actor": { "process": { "pid": 1234, "name": "bash", "exe": "/bin/bash" } },
///   "metadata": { "version": "1.3.0", "product": "GNN-Threat-Hunter-ESF" }
/// }
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OcsfEvent {
    // ── Required OCSF fields ──────────────────────────────────────────────
    /// OCSF class UID (e.g., 4001 = Process Activity).
    pub class_uid: u32,
    /// OCSF activity identifier.
    pub activity_id: u8,
    /// Event timestamp in Unix milliseconds.
    pub time: i64,
    /// Human-readable description of the event.
    pub message: Option<String>,

    // ── Endpoint context ─────────────────────────────────────────────────
    /// The host where the event originated.
    pub src_endpoint: Option<Endpoint>,
    /// Destination endpoint (relevant for network events).
    pub dst_endpoint: Option<Endpoint>,

    // ── Actor (the process that caused the event) ─────────────────────────
    pub actor: Option<Actor>,

    // ── Target object (file, process, network) ───────────────────────────
    pub file: Option<FileObject>,
    pub target_process: Option<Process>,

    // ── Metadata ─────────────────────────────────────────────────────────
    pub metadata: EventMetadata,

    // ── Threat intel overlay (populated in Phase 6) ───────────────────────
    pub mitre_attack: Option<MitreAttack>,

    // ── Severity ─────────────────────────────────────────────────────────
    /// 0=Unknown, 1=Info, 2=Low, 3=Medium, 4=High, 5=Critical
    pub severity_id: u8,
}

/// The actor struct wraps the process that initiated an event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Actor {
    pub process: Option<Process>,
    /// Logged-in user session, if available.
    pub session: Option<Session>,
}

/// Represents a user session.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub uid: Option<String>,
    pub user: Option<String>,
    pub is_remote: Option<bool>,
}

/// Metadata block attached to every event.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EventMetadata {
    /// OCSF schema version.
    pub version: String,
    /// Name of the product/sensor generating the event.
    pub product: String,
    /// Unique event UUID for deduplication.
    pub uid: Option<String>,
}
