"""
VaultWares Post-Quantum Cryptography (PQC) Layer

Implements a hybrid PQC encryption scheme for media payloads:

Key Encapsulation:
    ML-KEM-768 (Kyber768) — NIST FIPS 203, post-quantum key encapsulation.
    Used to establish a shared secret between parties without transmitting
    a private key over any channel.

Stream Cipher:
    ChaCha20-Poly1305 — authenticated encryption with associated data (AEAD).
    The 32-byte shared secret derived from ML-KEM is used directly as the
    symmetric key for all media payload encryption.

Digital Signatures:
    ML-DSA-65 (Dilithium3) — NIST FIPS 204, post-quantum digital signature.
    Used to authenticate encrypted payloads and key-exchange messages.

Design Principles:
    - All operations are local-first.  No key material ever leaves the process
      unless the caller explicitly serializes it.
    - Nonces are generated fresh with os.urandom for every encryption call.
    - Associated data (AD) is authenticated but not encrypted; callers may use
      it to bind ciphertext to session context without revealing payload content.

Usage example::

    from components.pqc_crypto import PQCKeyPair, PQCEncryptor

    # Recipient generates a long-term KEM keypair
    recipient = PQCKeyPair.generate_kem()

    # Sender encapsulates a shared secret toward the recipient
    enc = PQCEncryptor.from_kem_public_key(recipient.public_key)
    ciphertext, tag = enc.encrypt(b"secret media bytes", associated_data=b"session-id")

    # Recipient decapsulates and decrypts
    dec = PQCEncryptor.from_kem_private_key(recipient.private_key, enc.kem_ciphertext)
    plaintext = dec.decrypt(ciphertext, tag, associated_data=b"session-id")
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Optional import: liboqs / oqs
# If the library is not installed the module still loads and raises
# PQCUnavailableError at runtime so that other parts of the system can start
# and report a clear error.
# ---------------------------------------------------------------------------
try:
    import oqs  # type: ignore[import]

    _OQS_AVAILABLE = True
except ImportError:
    _OQS_AVAILABLE = False

# ---------------------------------------------------------------------------
# Symmetric AEAD: ChaCha20-Poly1305 from the `cryptography` package
# ---------------------------------------------------------------------------
try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305  # type: ignore[import]

    _CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    _CRYPTOGRAPHY_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KEM_ALGORITHM = "Kyber768"       # ML-KEM-768 / NIST FIPS 203
SIG_ALGORITHM = "Dilithium3"     # ML-DSA-65  / NIST FIPS 204
NONCE_BYTES = 12                 # ChaCha20-Poly1305 nonce length (96 bits)
KEY_BYTES = 32                   # Symmetric key length (256 bits)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PQCUnavailableError(RuntimeError):
    """Raised when a required PQC library is not installed."""


class PQCDecryptionError(ValueError):
    """Raised when decryption or tag verification fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_oqs() -> None:
    if not _OQS_AVAILABLE:
        raise PQCUnavailableError(
            "liboqs-python (oqs) is not installed. "
            "Install it with:  pip install oqs"
        )


def _require_cryptography() -> None:
    if not _CRYPTOGRAPHY_AVAILABLE:
        raise PQCUnavailableError(
            "cryptography is not installed. "
            "Install it with:  pip install cryptography"
        )


# ---------------------------------------------------------------------------
# Key material containers
# ---------------------------------------------------------------------------


@dataclass
class PQCKeyPair:
    """Holds a public/private keypair for either KEM or signature use."""

    algorithm: str
    public_key: bytes
    private_key: bytes

    @classmethod
    def generate_kem(cls) -> "PQCKeyPair":
        """Generate a fresh ML-KEM-768 keypair."""
        _require_oqs()
        with oqs.KeyEncapsulation(KEM_ALGORITHM) as kem:
            public_key = kem.generate_keypair()
            private_key = kem.export_secret_key()
        return cls(algorithm=KEM_ALGORITHM, public_key=public_key, private_key=private_key)

    @classmethod
    def generate_sig(cls) -> "PQCKeyPair":
        """Generate a fresh ML-DSA-65 (Dilithium3) keypair."""
        _require_oqs()
        with oqs.Signature(SIG_ALGORITHM) as sig:
            public_key = sig.generate_keypair()
            private_key = sig.export_secret_key()
        return cls(algorithm=SIG_ALGORITHM, public_key=public_key, private_key=private_key)


@dataclass
class SignedEnvelope:
    """A signed, encrypted payload envelope."""

    kem_ciphertext: bytes      # KEM encapsulation — shared secret derivation
    nonce: bytes               # ChaCha20-Poly1305 nonce (12 bytes)
    ciphertext: bytes          # Encrypted media payload
    tag: bytes                 # Poly1305 authentication tag (16 bytes)
    signature: Optional[bytes] # ML-DSA-65 signature over (kem_ciphertext + nonce + ciphertext + tag)
    sig_public_key: Optional[bytes]  # Sender's signature public key (optional, for verification)

    def to_bytes(self) -> bytes:
        """Serialize the envelope to a compact binary format."""

        def _pack_field(data: bytes) -> bytes:
            return struct.pack(">I", len(data)) + data

        parts = [
            _pack_field(self.kem_ciphertext),
            _pack_field(self.nonce),
            _pack_field(self.ciphertext),
            _pack_field(self.tag),
            _pack_field(self.signature or b""),
            _pack_field(self.sig_public_key or b""),
        ]
        return b"".join(parts)

    @classmethod
    def from_bytes(cls, data: bytes) -> "SignedEnvelope":
        """Deserialize an envelope from bytes produced by :meth:`to_bytes`."""
        offset = 0

        def _unpack_field() -> bytes:
            nonlocal offset
            (length,) = struct.unpack_from(">I", data, offset)
            offset += 4
            field = data[offset : offset + length]
            offset += length
            return field

        kem_ciphertext = _unpack_field()
        nonce = _unpack_field()
        ciphertext = _unpack_field()
        tag = _unpack_field()
        signature = _unpack_field() or None
        sig_public_key = _unpack_field() or None
        return cls(
            kem_ciphertext=kem_ciphertext,
            nonce=nonce,
            ciphertext=ciphertext,
            tag=tag,
            signature=signature,
            sig_public_key=sig_public_key,
        )


# ---------------------------------------------------------------------------
# Core cryptographic operations
# ---------------------------------------------------------------------------


class PQCEncryptor:
    """
    Handles encryption of a single payload using a hybrid PQC scheme:

    1. ML-KEM-768  — encapsulates a 32-byte shared secret for the recipient
    2. ChaCha20-Poly1305 — encrypts the payload with the shared secret

    One encryptor instance is created per payload (fresh nonce & KEM ciphertext
    each time).
    """

    def __init__(self, shared_secret: bytes, kem_ciphertext: bytes) -> None:
        if len(shared_secret) < KEY_BYTES:
            raise ValueError(
                f"Shared secret too short: {len(shared_secret)} bytes "
                f"(expected >= {KEY_BYTES})"
            )
        self._key = shared_secret[:KEY_BYTES]
        self.kem_ciphertext = kem_ciphertext

    # ------------------------------------------------------------------
    # Factory constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_kem_public_key(cls, recipient_public_key: bytes) -> "PQCEncryptor":
        """
        Sender-side: encapsulate a fresh shared secret using the recipient's
        ML-KEM public key.  Returns a new encryptor that holds the shared
        secret and the KEM ciphertext to send to the recipient.
        """
        _require_oqs()
        with oqs.KeyEncapsulation(KEM_ALGORITHM) as kem:
            kem_ciphertext, shared_secret = kem.encap_secret(recipient_public_key)
        return cls(shared_secret=shared_secret, kem_ciphertext=kem_ciphertext)

    @classmethod
    def from_kem_private_key(
        cls, recipient_private_key: bytes, kem_ciphertext: bytes
    ) -> "PQCEncryptor":
        """
        Recipient-side: decapsulate the shared secret using the recipient's
        ML-KEM private key and the KEM ciphertext received from the sender.
        """
        _require_oqs()
        with oqs.KeyEncapsulation(KEM_ALGORITHM, secret_key=recipient_private_key) as kem:
            shared_secret = kem.decap_secret(kem_ciphertext)
        return cls(shared_secret=shared_secret, kem_ciphertext=kem_ciphertext)

    # ------------------------------------------------------------------
    # Encrypt / Decrypt
    # ------------------------------------------------------------------

    def encrypt(
        self,
        plaintext: bytes,
        associated_data: Optional[bytes] = None,
    ) -> tuple[bytes, bytes, bytes]:
        """
        Encrypt *plaintext* with ChaCha20-Poly1305.

        Returns ``(ciphertext_with_tag, nonce)``.  The nonce is a fresh
        12-byte random value generated by :func:`os.urandom`.

        *associated_data* is authenticated but not encrypted.
        """
        _require_cryptography()
        nonce = os.urandom(NONCE_BYTES)
        chacha = ChaCha20Poly1305(self._key)
        ciphertext_with_tag = chacha.encrypt(nonce, plaintext, associated_data)
        # Split tag off (last 16 bytes) so callers can store it separately
        tag = ciphertext_with_tag[-16:]
        ciphertext = ciphertext_with_tag[:-16]
        return ciphertext, tag, nonce

    def decrypt(
        self,
        ciphertext: bytes,
        tag: bytes,
        nonce: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt and verify *ciphertext*.

        Raises :class:`PQCDecryptionError` if authentication fails.
        """
        _require_cryptography()
        chacha = ChaCha20Poly1305(self._key)
        try:
            plaintext = chacha.decrypt(nonce, ciphertext + tag, associated_data)
        except Exception as exc:
            raise PQCDecryptionError("Decryption or authentication failed") from exc
        return plaintext


# ---------------------------------------------------------------------------
# Signing helpers
# ---------------------------------------------------------------------------


class PQCSigner:
    """Sign and verify messages using ML-DSA-65 (Dilithium3)."""

    def __init__(self, keypair: PQCKeyPair) -> None:
        if keypair.algorithm != SIG_ALGORITHM:
            raise ValueError(
                f"Expected {SIG_ALGORITHM} keypair, got {keypair.algorithm}"
            )
        self._keypair = keypair

    def sign(self, message: bytes) -> bytes:
        """Return a detached ML-DSA-65 signature over *message*."""
        _require_oqs()
        with oqs.Signature(SIG_ALGORITHM, secret_key=self._keypair.private_key) as sig:
            return sig.sign(message)

    @staticmethod
    def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
        """
        Verify a detached ML-DSA-65 *signature* over *message* using
        *public_key*.  Returns ``True`` on success, ``False`` otherwise.
        """
        _require_oqs()
        with oqs.Signature(SIG_ALGORITHM) as sig:
            return sig.verify(message, signature, public_key)


# ---------------------------------------------------------------------------
# High-level API: seal / open
# ---------------------------------------------------------------------------


def seal(
    plaintext: bytes,
    recipient_kem_public_key: bytes,
    sender_sig_keypair: Optional[PQCKeyPair] = None,
    associated_data: Optional[bytes] = None,
) -> SignedEnvelope:
    """
    Encrypt *plaintext* for *recipient_kem_public_key* and optionally sign
    the envelope with *sender_sig_keypair*.

    Returns a :class:`SignedEnvelope` that can be serialized with
    :meth:`SignedEnvelope.to_bytes`.
    """
    encryptor = PQCEncryptor.from_kem_public_key(recipient_kem_public_key)
    ciphertext, tag, nonce = encryptor.encrypt(plaintext, associated_data=associated_data)

    signature: Optional[bytes] = None
    sig_public_key: Optional[bytes] = None

    if sender_sig_keypair is not None:
        signer = PQCSigner(sender_sig_keypair)
        signed_data = encryptor.kem_ciphertext + nonce + ciphertext + tag
        signature = signer.sign(signed_data)
        sig_public_key = sender_sig_keypair.public_key

    return SignedEnvelope(
        kem_ciphertext=encryptor.kem_ciphertext,
        nonce=nonce,
        ciphertext=ciphertext,
        tag=tag,
        signature=signature,
        sig_public_key=sig_public_key,
    )


def open_envelope(
    envelope: SignedEnvelope,
    recipient_kem_private_key: bytes,
    associated_data: Optional[bytes] = None,
    verify_signature: bool = True,
) -> bytes:
    """
    Decrypt and (optionally) verify a :class:`SignedEnvelope`.

    Raises :class:`PQCDecryptionError` on decryption failure.
    Raises :class:`ValueError` when *verify_signature* is ``True`` but the
    envelope carries no signature or signature verification fails.
    """
    if verify_signature:
        if envelope.signature is None or envelope.sig_public_key is None:
            raise ValueError("Signature verification requested but envelope has no signature")
        signed_data = envelope.kem_ciphertext + envelope.nonce + envelope.ciphertext + envelope.tag
        if not PQCSigner.verify(signed_data, envelope.signature, envelope.sig_public_key):
            raise ValueError("Signature verification failed — envelope may have been tampered with")

    decryptor = PQCEncryptor.from_kem_private_key(
        recipient_kem_private_key, envelope.kem_ciphertext
    )
    return decryptor.decrypt(
        envelope.ciphertext, envelope.tag, envelope.nonce, associated_data=associated_data
    )
