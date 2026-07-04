"""
ocsf/schemas.py

Python OCSF v1.3 Pydantic data contracts.

These Pydantic models are the Python mirror of the Rust structs defined in
`ingestion/src/schema/ocsf.rs`. They are the single Python source of truth
for all OCSF event validation throughout the Django backend and inference
service.

Usage:
    from ocsf.schemas import OcsfEvent
    event = OcsfEvent.model_validate(raw_json_dict)
"""

from __future__ import annotations

from enum import IntEnum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ─────────────────────────────────────────────────────────────────────────────
# OCSF Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class ActivityId(IntEnum):
    """OCSF numeric activity codes — mirrors Rust ActivityId enum."""
    UNKNOWN = 0
    LAUNCH = 1
    TERMINATE = 2
    OPEN = 3
    READ = 4
    WRITE = 5
    DELETE = 6
    RENAME = 7
    EXECUTE = 8
    NETWORK_CONNECT = 9
    NETWORK_DISCONNECT = 10


class SeverityId(IntEnum):
    """OCSF severity codes."""
    UNKNOWN = 0
    INFO = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5


class ClassUid(IntEnum):
    """OCSF class UIDs for event categorization."""
    PROCESS_ACTIVITY = 4001
    FILE_SYSTEM_ACTIVITY = 4004
    NETWORK_ACTIVITY = 4003


# ─────────────────────────────────────────────────────────────────────────────
# Sub-object models
# ─────────────────────────────────────────────────────────────────────────────

class Endpoint(BaseModel):
    """OCSF endpoint object — source or destination host."""
    ip: Optional[str] = None
    hostname: Optional[str] = None
    uid: Optional[str] = Field(None, description="macOS Hardware UUID")
    os_name: Optional[str] = None


class Process(BaseModel):
    """OCSF process object — the actor or target process."""
    pid: int
    parent_pid: Optional[int] = None
    name: str
    exe: Optional[str] = Field(None, description="Full path to executable")
    cmd_line: Optional[str] = None
    user: Optional[str] = None
    exe_hash_sha256: Optional[str] = Field(
        None,
        description="SHA-256 of the binary — used for deterministic Node ID derivation",
    )


class FileObject(BaseModel):
    """OCSF file system object."""
    path: str
    name: str
    mime_type: Optional[str] = None
    hash_sha256: Optional[str] = None
    size: Optional[int] = None


class Session(BaseModel):
    """User session attached to the actor."""
    uid: Optional[str] = None
    user: Optional[str] = None
    is_remote: Optional[bool] = None


class Actor(BaseModel):
    """The actor (process + session) that caused the event."""
    process: Optional[Process] = None
    session: Optional[Session] = None


class MitreAttack(BaseModel):
    """MITRE ATT&CK overlay — populated by threat intel enrichment (Phase 6)."""
    tactic: Optional[str] = None
    technique_id: Optional[str] = None
    technique_name: Optional[str] = None


class EventMetadata(BaseModel):
    """OCSF metadata block — version, product, deduplication UID."""
    version: str = "1.3.0"
    product: str = "GNN-Threat-Hunter-ESF"
    uid: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))


# ─────────────────────────────────────────────────────────────────────────────
# Root OCSF Event Envelope
# ─────────────────────────────────────────────────────────────────────────────

class OcsfEvent(BaseModel):
    """
    The canonical OCSF v1.3 event envelope.

    Every event emitted by the macOS ESF telemetry daemon (Phase 1),
    validated by the Django backend (Phase 5), and scored by the inference
    engine (Phase 9) MUST conform to this schema.

    Example:
        >>> from ocsf.schemas import OcsfEvent, ActivityId
        >>> event = OcsfEvent(
        ...     class_uid=4001,
        ...     activity_id=ActivityId.LAUNCH,
        ...     time=1720000000000,
        ...     metadata=EventMetadata(),
        ...     severity_id=1,
        ... )
    """

    # ── Required OCSF fields ─────────────────────────────────────────────────
    class_uid: int = Field(..., description="OCSF class UID (e.g., 4001=ProcessActivity)")
    activity_id: int = Field(..., description="OCSF activity ID")
    time: int = Field(..., description="Event timestamp in Unix milliseconds")
    severity_id: int = Field(SeverityId.INFO, description="Severity 0–5")
    message: Optional[str] = None

    # ── Endpoint context ─────────────────────────────────────────────────────
    src_endpoint: Optional[Endpoint] = None
    dst_endpoint: Optional[Endpoint] = None

    # ── Actor ────────────────────────────────────────────────────────────────
    actor: Optional[Actor] = None

    # ── Target objects ───────────────────────────────────────────────────────
    file: Optional[FileObject] = None
    target_process: Optional[Process] = None

    # ── Metadata ─────────────────────────────────────────────────────────────
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    # ── Threat intel overlay (Phase 6) ───────────────────────────────────────
    mitre_attack: Optional[MitreAttack] = None

    model_config = {"json_schema_extra": {"example": {
        "class_uid": 4001,
        "activity_id": 1,
        "time": 1720000000000,
        "severity_id": 1,
        "message": "Process launched: bash",
        "src_endpoint": {"hostname": "macbook-pro.local", "uid": "HARDWARE-UUID"},
        "actor": {"process": {"pid": 1234, "name": "bash", "exe": "/bin/bash"}},
        "metadata": {"version": "1.3.0", "product": "GNN-Threat-Hunter-ESF"},
    }}}
