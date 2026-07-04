/**
 * lib/crypto/ed25519.ts
 *
 * Client-side Ed25519 cryptographic signing utility for Phase 12.
 *
 * Implements:
 *  1. Ed25519 keypair generation (stored securely in browser memory / Solana wallet)
 *  2. SHA-256 hashing of graph state payloads
 *  3. Ed25519 signature generation for kill-switch authorization (Phase 11)
 *  4. Server-side signature verification helper using Node.js `crypto` module
 *
 * Security model:
 *  - Private keys NEVER leave the browser (or hardware wallet in production)
 *  - Backend verifies signatures using the public key registered at setup
 *  - All forensic anchor submissions require a valid Ed25519 signature
 *
 * References:
 *  - Web Crypto API: https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto
 *  - @solana/web3.js: Used for Solana transaction signing
 */

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface Ed25519KeyPair {
  publicKey: CryptoKey;
  privateKey: CryptoKey;
  /** Base64-encoded public key — safe to share with the backend. */
  publicKeyBase64: string;
}

export interface GraphStatePayload {
  /** SHA-256 hex of PyG graph state (edge_index + edge_attr). */
  graphHash: string;
  /** Unix millisecond timestamp of the graph snapshot. */
  timestampMs: number;
  /** UUID of the AnomalyAlert in the Django database. */
  incidentId: string;
}

export interface SignedGraphState {
  payload: GraphStatePayload;
  /** Base64-encoded Ed25519 signature of the payload. */
  signature: string;
  /** Base64-encoded public key of the signing keypair. */
  publicKey: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Key Generation
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Generate a new Ed25519 keypair using the Web Crypto API.
 * In production this is replaced by a Solana hardware wallet (Ledger).
 */
export async function generateEd25519KeyPair(): Promise<Ed25519KeyPair> {
  const keyPair = await window.crypto.subtle.generateKey(
    { name: "Ed25519" },
    true,  // extractable — needed for export to Base64
    ["sign", "verify"]
  );

  const rawPublicKey = await window.crypto.subtle.exportKey("raw", keyPair.publicKey);
  const publicKeyBase64 = btoa(String.fromCharCode(...new Uint8Array(rawPublicKey)));

  return {
    publicKey: keyPair.publicKey,
    privateKey: keyPair.privateKey,
    publicKeyBase64,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Hashing
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Compute SHA-256 of a string payload using the Web Crypto API.
 * Returns a hex-encoded digest (matches the Rust SHA-256 output).
 */
export async function sha256Hex(data: string): Promise<string> {
  const encoded = new TextEncoder().encode(data);
  const hashBuffer = await window.crypto.subtle.digest("SHA-256", encoded);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// ─────────────────────────────────────────────────────────────────────────────
// Signing
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Sign a graph state payload with an Ed25519 private key.
 *
 * The backend (Django) verifies this signature before:
 *  - Accepting a kill-switch command (Phase 11)
 *  - Submitting a forensic anchor to Solana (Phase 12)
 *
 * @param payload - The graph state to sign
 * @param privateKey - The signer's Ed25519 private key
 * @param publicKeyBase64 - Base64 public key for inclusion in the response
 */
export async function signGraphState(
  payload: GraphStatePayload,
  privateKey: CryptoKey,
  publicKeyBase64: string
): Promise<SignedGraphState> {
  const canonicalPayload = JSON.stringify({
    graphHash: payload.graphHash,
    timestampMs: payload.timestampMs,
    incidentId: payload.incidentId,
  });

  const encoded = new TextEncoder().encode(canonicalPayload);

  const signatureBuffer = await window.crypto.subtle.sign(
    { name: "Ed25519" },
    privateKey,
    encoded
  );

  const signature = btoa(String.fromCharCode(...new Uint8Array(signatureBuffer)));

  return { payload, signature, publicKey: publicKeyBase64 };
}

// ─────────────────────────────────────────────────────────────────────────────
// Client-side Verification (for UI confirmation before submission)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Verify an Ed25519 signature against the original payload.
 * Used client-side to confirm the signature before sending to the backend.
 *
 * @param signed - The signed graph state
 * @param publicKey - The public key CryptoKey object
 */
export async function verifySignature(
  signed: SignedGraphState,
  publicKey: CryptoKey
): Promise<boolean> {
  const canonicalPayload = JSON.stringify({
    graphHash: signed.payload.graphHash,
    timestampMs: signed.payload.timestampMs,
    incidentId: signed.payload.incidentId,
  });

  const encoded = new TextEncoder().encode(canonicalPayload);

  const signatureBytes = Uint8Array.from(atob(signed.signature), (c) =>
    c.charCodeAt(0)
  );

  return window.crypto.subtle.verify(
    { name: "Ed25519" },
    publicKey,
    signatureBytes,
    encoded
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Server-side Verification Utility (Node.js, for Django API calls)
// ─────────────────────────────────────────────────────────────────────────────
// NOTE: This section is only used in Next.js server components / API routes.
// It uses the Node.js `crypto` module, NOT the Web Crypto API.

/**
 * Verify an Ed25519 signature server-side using Node.js crypto.
 *
 * Call this from a Next.js API Route (app/api/...) when the backend
 * needs to verify a kill-switch command before forwarding to Django.
 *
 * @example
 * // app/api/kill-switch/route.ts
 * import { verifySignatureNodeJs } from "@/lib/crypto/ed25519";
 * const isValid = await verifySignatureNodeJs(signed, publicKeyBase64);
 */
export async function verifySignatureNodeJs(
  signed: SignedGraphState,
  publicKeyBase64: string
): Promise<boolean> {
  // Only available in Node.js environment (Next.js API routes / server components)
  if (typeof window !== "undefined") {
    throw new Error("verifySignatureNodeJs must only be called server-side");
  }

  const { createVerify } = await import("crypto");

  const canonicalPayload = JSON.stringify({
    graphHash: signed.payload.graphHash,
    timestampMs: signed.payload.timestampMs,
    incidentId: signed.payload.incidentId,
  });

  const publicKeyBuffer = Buffer.from(publicKeyBase64, "base64");
  const signatureBuffer = Buffer.from(signed.signature, "base64");

  const verifier = createVerify("Ed25519");
  verifier.update(canonicalPayload);

  return verifier.verify(
    { key: publicKeyBuffer, format: "der", type: "spki" },
    signatureBuffer
  );
}
