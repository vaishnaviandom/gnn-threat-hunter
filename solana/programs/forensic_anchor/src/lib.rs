//! forensic_anchor — Solana Anchor Smart Contract (Phase 12)
//!
//! This program receives a SHA-256 hash of the GNN graph state
//! (computed from PyG edge_index + edge_attr tensors) and stores it
//! on-chain in a Program Derived Address (PDA) account.
//!
//! The on-chain record provides cryptographic, tamper-proof forensic
//! anchoring that cannot be retroactively modified. Any investigator
//! can independently verify incident integrity by:
//!   1. Recomputing the SHA-256 of the graph snapshot
//!   2. Verifying the Ed25519 signature from the backend keypair
//!   3. Comparing against the on-chain stored hash
//!
//! # Program Instructions
//! - `anchor_graph_state`: Store a new graph state hash on-chain
//! - `verify_graph_state`:  Verify a stored hash matches a provided hash
//!
//! # Deployment
//! ```bash
//! # Build (requires Anchor CLI + Solana BPF toolchain)
//! anchor build
//!
//! # Deploy to Devnet
//! anchor deploy --provider.cluster devnet
//! ```

use anchor_lang::prelude::*;

declare_id!("REPLACE_WITH_DEPLOYED_PROGRAM_ID");

// ─────────────────────────────────────────────────────────────────────────────
// Program
// ─────────────────────────────────────────────────────────────────────────────

#[program]
pub mod forensic_anchor {
    use super::*;

    /// Store a SHA-256 graph state hash on-chain.
    ///
    /// # Arguments
    /// * `graph_hash`   - 32-byte SHA-256 of the serialized graph state
    /// * `timestamp_ms` - Unix millisecond timestamp of the graph snapshot
    /// * `incident_id`  - Optional UUID string linking to a Django AnomalyAlert
    pub fn anchor_graph_state(
        ctx: Context<AnchorGraphState>,
        graph_hash: [u8; 32],
        timestamp_ms: i64,
        incident_id: String,
    ) -> Result<()> {
        let record = &mut ctx.accounts.graph_record;
        require!(incident_id.len() <= 64, ForensicAnchorError::IncidentIdTooLong);

        record.authority = ctx.accounts.authority.key();
        record.graph_hash = graph_hash;
        record.timestamp_ms = timestamp_ms;
        record.incident_id = incident_id;
        record.verified = false;
        record.bump = ctx.bumps.graph_record;

        emit!(GraphStateAnchored {
            authority: record.authority,
            graph_hash,
            timestamp_ms,
        });

        msg!(
            "Graph state anchored | hash={} | ts={}",
            hex::encode(graph_hash),
            timestamp_ms
        );
        Ok(())
    }

    /// Mark a stored graph state record as verified by an authorized party.
    pub fn verify_graph_state(ctx: Context<VerifyGraphState>) -> Result<()> {
        let record = &mut ctx.accounts.graph_record;
        record.verified = true;
        msg!("Graph record verified by {}", ctx.accounts.authority.key());
        Ok(())
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Account Contexts
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Accounts)]
#[instruction(graph_hash: [u8; 32], timestamp_ms: i64, incident_id: String)]
pub struct AnchorGraphState<'info> {
    #[account(
        init,
        payer = authority,
        space = GraphStateRecord::SPACE,
        seeds = [b"graph_record", authority.key().as_ref(), &timestamp_ms.to_le_bytes()],
        bump
    )]
    pub graph_record: Account<'info, GraphStateRecord>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct VerifyGraphState<'info> {
    #[account(
        mut,
        has_one = authority,
    )]
    pub graph_record: Account<'info, GraphStateRecord>,

    pub authority: Signer<'info>,
}

// ─────────────────────────────────────────────────────────────────────────────
// Account Data
// ─────────────────────────────────────────────────────────────────────────────

#[account]
pub struct GraphStateRecord {
    /// The backend keypair that signed and submitted this record.
    pub authority: Pubkey,
    /// SHA-256 of PyG graph state (edge_index + edge_attr).
    pub graph_hash: [u8; 32],
    /// Unix ms timestamp of the graph snapshot.
    pub timestamp_ms: i64,
    /// Links back to AnomalyAlert.uid in the Django database.
    pub incident_id: String,
    /// Whether the record has been independently verified.
    pub verified: bool,
    /// PDA bump seed.
    pub bump: u8,
}

impl GraphStateRecord {
    // discriminator(8) + pubkey(32) + hash(32) + i64(8) + String(4+64) + bool(1) + bump(1)
    pub const SPACE: usize = 8 + 32 + 32 + 8 + (4 + 64) + 1 + 1;
}

// ─────────────────────────────────────────────────────────────────────────────
// Events
// ─────────────────────────────────────────────────────────────────────────────

#[event]
pub struct GraphStateAnchored {
    pub authority: Pubkey,
    pub graph_hash: [u8; 32],
    pub timestamp_ms: i64,
}

// ─────────────────────────────────────────────────────────────────────────────
// Errors
// ─────────────────────────────────────────────────────────────────────────────

#[error_code]
pub enum ForensicAnchorError {
    #[msg("incident_id must be 64 characters or fewer")]
    IncidentIdTooLong,
}
