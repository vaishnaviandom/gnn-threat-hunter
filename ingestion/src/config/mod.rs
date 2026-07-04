//! Runtime configuration loaded from environment variables.

use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub kafka_brokers: String,
    pub kafka_topic_telemetry: String,
    pub kafka_topic_graph_edges: String,
    pub memgraph_host: String,
    pub memgraph_port: u16,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            kafka_brokers: env::var("REDPANDA_BOOTSTRAP_SERVERS")
                .unwrap_or_else(|_| "localhost:19092".to_string()),
            kafka_topic_telemetry: env::var("REDPANDA_TOPIC_TELEMETRY")
                .unwrap_or_else(|_| "ocsf.telemetry.raw".to_string()),
            kafka_topic_graph_edges: env::var("REDPANDA_TOPIC_GRAPH_EDGES")
                .unwrap_or_else(|_| "graph.edges.v1".to_string()),
            memgraph_host: env::var("MEMGRAPH_HOST")
                .unwrap_or_else(|_| "localhost".to_string()),
            memgraph_port: env::var("MEMGRAPH_PORT")
                .ok()
                .and_then(|p| p.parse().ok())
                .unwrap_or(7687),
        }
    }
}
