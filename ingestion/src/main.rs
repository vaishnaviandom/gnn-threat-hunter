//! GNN Ingestion Engine — Phase 3 entry point.
//!
//! Consumes OCSF-normalized telemetry from Redpanda and writes graph edges
//! to Memgraph. This scaffold will be fully implemented in Phase 3.
//!
//! For Phase 0 (current), this binary compiles cleanly and logs a startup
//! message to confirm the crate builds correctly.

mod config;
mod graph;
mod schema;

use config::Config;
use tracing::info;

#[tokio::main]
async fn main() {
    // Initialize structured logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("gnn_ingestion=debug".parse().unwrap()),
        )
        .init();

    // Load env vars (reads .env in dev via dotenvy)
    let _ = dotenvy::dotenv();
    let config = Config::from_env();

    info!(
        brokers = %config.kafka_brokers,
        topic = %config.kafka_topic_telemetry,
        memgraph = %format!("{}:{}", config.memgraph_host, config.memgraph_port),
        "GNN Ingestion Engine starting — Phase 3 consumer will connect here"
    );

    // Phase 3 will replace this with the full rdkafka consumer loop.
    info!("Phase 0 scaffold: binary compiled and running. Awaiting Phase 3 implementation.");
}
