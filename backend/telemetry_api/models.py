"""
telemetry_api/models.py

Phase 0 base ORM models for the Telemetry API.

These models store the OCSF-normalized events ingested from the macOS ESF
daemon (Phase 1) after they flow through Redpanda (Phase 2) and the Rust
consumer (Phase 3). PostgreSQL is the persistent record of truth; Memgraph
holds the live graph view.
"""

from django.db import models


class HostEndpoint(models.Model):
    """
    Represents a monitored host (macOS workstation or server).
    Maps to the OCSF `src_endpoint` / `dst_endpoint` object.
    """
    uid = models.CharField(max_length=255, unique=True, help_text="macOS Hardware UUID")
    hostname = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    os_name = models.CharField(max_length=128, blank=True, default="macOS")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]
        verbose_name = "Host Endpoint"

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"


class ProcessNode(models.Model):
    """
    A process observed on a host. Used to populate graph nodes in Memgraph.
    The `node_id` is the SHA-256 deterministic ID matching the Rust graph engine.
    """
    node_id = models.CharField(max_length=64, unique=True, help_text="SHA-256 of exe:user")
    name = models.CharField(max_length=255)
    exe_path = models.TextField(blank=True)
    exe_hash_sha256 = models.CharField(max_length=64, blank=True)
    user = models.CharField(max_length=128, blank=True)
    host = models.ForeignKey(HostEndpoint, on_delete=models.CASCADE, related_name="processes")
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.name} [{self.node_id[:8]}]"


class TelemetryEvent(models.Model):
    """
    The raw OCSF event as received from the ESF daemon.

    Stored in PostgreSQL for audit trail and replay. The Rust ingestion
    engine simultaneously writes the derived graph edges to Memgraph.
    """

    class ActivityType(models.IntegerChoices):
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

    class SeverityLevel(models.IntegerChoices):
        UNKNOWN = 0
        INFO = 1
        LOW = 2
        MEDIUM = 3
        HIGH = 4
        CRITICAL = 5

    # Core OCSF fields
    uid = models.UUIDField(unique=True, help_text="OCSF event UID for deduplication")
    class_uid = models.IntegerField(help_text="OCSF class UID (e.g., 4001=ProcessActivity)")
    activity_id = models.IntegerField(choices=ActivityType.choices, default=ActivityType.UNKNOWN)
    severity_id = models.IntegerField(choices=SeverityLevel.choices, default=SeverityLevel.INFO)
    timestamp = models.DateTimeField(help_text="Original event timestamp from the ESF daemon")
    message = models.TextField(blank=True)

    # Relational links
    source_host = models.ForeignKey(
        HostEndpoint, on_delete=models.SET_NULL, null=True, related_name="events"
    )
    actor_process = models.ForeignKey(
        ProcessNode, on_delete=models.SET_NULL, null=True, related_name="actor_events"
    )

    # Full OCSF JSON blob for replay/debugging
    raw_ocsf = models.JSONField(help_text="Full OCSF event JSON")

    # Graph status
    graph_written = models.BooleanField(
        default=False,
        help_text="True if edges have been written to Memgraph by the Rust ingestion engine",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["activity_id"]),
            models.Index(fields=["severity_id"]),
        ]

    def __str__(self):
        return f"Event {self.uid} — activity={self.activity_id} severity={self.severity_id}"


class AnomalyAlert(models.Model):
    """
    Represents an anomaly surfaced by the GNN inference engine (Phase 9).
    Created by the Django inference coordinator when anomaly score exceeds threshold.
    """

    class Status(models.TextChoices):
        NEW = "new", "New"
        TRIAGING = "triaging", "Triaging"
        CONFIRMED = "confirmed", "Confirmed Threat"
        FALSE_POSITIVE = "fp", "False Positive"
        RESOLVED = "resolved", "Resolved"

    triggering_event = models.ForeignKey(
        TelemetryEvent, on_delete=models.CASCADE, related_name="alerts"
    )
    anomaly_score = models.FloatField(help_text="GNN reconstruction error or score [0.0–1.0]")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    # XAI triage report generated in Phase 10
    triage_report = models.TextField(blank=True)
    # Solana forensic anchor hash (Phase 12)
    solana_tx_signature = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Alert [{self.status}] score={self.anomaly_score:.3f}"
