//! Graph edge derivation from OCSF events.
//!
//! Translates normalized OCSF events into (source_node, edge_type, target_node)
//! triples that will be upserted into Memgraph (Phase 4).

use sha2::{Digest, Sha256};
use crate::schema::ocsf::OcsfEvent;

/// A directed graph edge derived from a single OCSF event.
#[derive(Debug, Clone)]
pub struct GraphEdge {
    /// SHA-256 derived node ID for the source (actor process or endpoint).
    pub src_node_id: String,
    /// SHA-256 derived node ID for the target (file, process, or endpoint).
    pub dst_node_id: String,
    /// Relationship type in Memgraph (e.g., "EXECUTED", "READ_FILE").
    pub edge_type: String,
    /// Original event timestamp (Unix ms) — used for TTL eviction.
    pub timestamp_ms: i64,
    /// OCSF activity_id for downstream filtering.
    pub activity_id: u8,
}

/// Derive a stable, deterministic Node ID from an arbitrary string seed.
///
/// Uses SHA-256 so that the same process path always maps to the same node,
/// enabling graph merge without duplication.
pub fn derive_node_id(seed: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(seed.as_bytes());
    hex::encode(hasher.finalize())
}

/// Convert an OCSF event into zero or more graph edges.
///
/// Returns `None` if the event lacks enough information to form an edge.
pub fn event_to_edges(event: &OcsfEvent) -> Vec<GraphEdge> {
    let mut edges = Vec::new();

    let actor_process = event
        .actor
        .as_ref()
        .and_then(|a| a.process.as_ref());

    if let Some(proc) = actor_process {
        let src_seed = format!(
            "process:{}:{}",
            proc.exe.as_deref().unwrap_or("unknown"),
            proc.user.as_deref().unwrap_or("unknown")
        );
        let src_node_id = derive_node_id(&src_seed);

        // ── Process execution edge ─────────────────────────────────────────
        if let Some(target_proc) = &event.target_process {
            let dst_seed = format!(
                "process:{}:{}",
                target_proc.exe.as_deref().unwrap_or("unknown"),
                target_proc.user.as_deref().unwrap_or("unknown")
            );
            edges.push(GraphEdge {
                src_node_id: src_node_id.clone(),
                dst_node_id: derive_node_id(&dst_seed),
                edge_type: "SPAWNED".to_string(),
                timestamp_ms: event.time,
                activity_id: event.activity_id,
            });
        }

        // ── File access edge ───────────────────────────────────────────────
        if let Some(file) = &event.file {
            let dst_seed = format!("file:{}", file.path);
            edges.push(GraphEdge {
                src_node_id: src_node_id.clone(),
                dst_node_id: derive_node_id(&dst_seed),
                edge_type: match event.activity_id {
                    4 => "READ_FILE",
                    5 => "WROTE_FILE",
                    6 => "DELETED_FILE",
                    8 => "EXECUTED_FILE",
                    _ => "ACCESSED_FILE",
                }
                .to_string(),
                timestamp_ms: event.time,
                activity_id: event.activity_id,
            });
        }

        // ── Network connection edge ────────────────────────────────────────
        if event.activity_id == 9 {
            if let Some(dst_ep) = &event.dst_endpoint {
                let dst_seed = format!(
                    "endpoint:{}:{}",
                    dst_ep.ip.as_deref().unwrap_or("unknown"),
                    dst_ep.hostname.as_deref().unwrap_or("unknown")
                );
                edges.push(GraphEdge {
                    src_node_id: src_node_id.clone(),
                    dst_node_id: derive_node_id(&dst_seed),
                    edge_type: "CONNECTED_TO".to_string(),
                    timestamp_ms: event.time,
                    activity_id: event.activity_id,
                });
            }
        }
    }

    edges
}
