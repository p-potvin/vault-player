# Security Agent — Post-Quantum Cryptography

## Overview

The `SecurityAgent` implements the VaultWares Post-Quantum Cryptography (PQC)
protocol for media payload encryption and agent-to-agent authentication.

All operations are **local-first**: no key material is persisted to disk or
transmitted to external services by this agent.

## Cryptographic Stack

| Layer | Algorithm | Standard | Purpose |
|---|---|---|---|
| Key Encapsulation | ML-KEM-768 (Kyber768) | NIST FIPS 203 | Establish shared secret between parties |
| Stream Cipher | ChaCha20-Poly1305 | RFC 8439 | Authenticated encryption of media payloads |
| Digital Signatures | ML-DSA-65 (Dilithium3) | NIST FIPS 204 | Authenticate encrypted envelopes |

## Skills

- `pqc_keygen_kem` — Generate a fresh ML-KEM-768 keypair (in-memory)
- `pqc_keygen_sig` — Generate a fresh ML-DSA-65 keypair (in-memory)
- `pqc_encrypt` — Encrypt a raw payload with ML-KEM + ChaCha20-Poly1305
- `pqc_decrypt` — Decrypt an encrypted payload
- `pqc_sign` — Sign a payload with ML-DSA-65
- `pqc_verify` — Verify an ML-DSA-65 signature
- `pqc_seal` — Seal a payload into a signed, encrypted envelope
- `pqc_open` — Open and verify a sealed envelope
- `pqc_rotate_keys` — Rotate a stored KEM or signature key

## Task Types (dispatched by LonelyManager)

| Task ID | Description |
|---|---|
| `generate_kem_keypair` | Generate a fresh ML-KEM-768 keypair, stored under `key_id` |
| `generate_sig_keypair` | Generate a fresh ML-DSA-65 keypair, stored under `key_id` |
| `encrypt_payload` | Encrypt bytes with a stored recipient KEM public key |
| `decrypt_payload` | Decrypt with a stored recipient KEM private key |
| `sign_payload` | Sign bytes with a stored ML-DSA private key |
| `verify_payload` | Verify a detached ML-DSA signature |
| `seal_envelope` | Encrypt + sign a payload into a `SignedEnvelope` |
| `open_envelope` | Verify + decrypt a `SignedEnvelope` |
| `rotate_keys` | Replace a stored key with a fresh keypair |

## Dispatch Examples

```python
# 1. Generate a recipient KEM keypair
manager.assign_task(
    "security-agent",
    "generate_kem_keypair",
    description="Generate ML-KEM-768 keypair for media session",
    key_id="media-session-001",
)

# 2. Encrypt a media payload
manager.assign_task(
    "security-agent",
    "encrypt_payload",
    description="Encrypt media chunk",
    payload="<binary payload as hex or bytes>",
    recipient_key_id="media-session-001",
    associated_data="vault-player/session/abc123",
)

# 3. Seal a signed envelope (requires both KEM and sig keys)
manager.assign_task(
    "security-agent",
    "seal_envelope",
    description="Seal and sign media envelope",
    payload="<plaintext>",
    recipient_key_id="media-session-001",
    sender_sig_key_id="agent-sig-key",
    associated_data="vault-player/session/abc123",
)
```

## Security Notes

- Keys are held **in-memory only**.  Restart the agent to clear all key material.
- Nonces are generated via `os.urandom(12)` for every encryption call — never reused.
- The KEM shared secret is derived fresh for every `seal` / `encrypt` call.
- `verify_signature=True` (default) is enforced on all `open_envelope` calls unless
  the caller explicitly sets it to `False` (e.g. for unauthenticated test payloads).
- Associated data binds ciphertext to a session context and must match exactly
  between encryption and decryption.

## Dependencies

```
oqs>=0.10.2        # liboqs Python bindings (ML-KEM, ML-DSA)
cryptography>=44.0 # ChaCha20-Poly1305 AEAD
```

Install with:

```bash
pip install oqs cryptography
```

## Integration

```python
from agents.security_agent import SecurityAgent

agent = SecurityAgent(agent_id="security-agent")
agent.start()
```
