import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from vaultwares_agentciation.extrovert_agent import ExtrovertAgent
from vaultwares_agentciation.enums import AgentStatus


class SecurityAgent(ExtrovertAgent):
    """
    Post-Quantum Cryptography (PQC) Security Agent.

    Specializes in:
    - ML-KEM-768 (Kyber768) key-pair generation and key encapsulation
    - ML-DSA-65 (Dilithium3) key-pair generation, signing, and verification
    - ChaCha20-Poly1305 AEAD encryption/decryption of media payloads
    - Full signed-envelope sealing and opening via the high-level PQC API
    - Key rotation for long-lived sessions

    All cryptographic operations are performed in-process and local-first.
    No key material is persisted to disk or transmitted externally by this
    agent unless an explicit export task is dispatched.

    Inherits the full Extrovert personality: heartbeat every 5 seconds,
    status broadcast every minute, socialization on every user interaction.
    """

    AGENT_TYPE = "security"
    SKILLS = [
        "pqc_keygen_kem",
        "pqc_keygen_sig",
        "pqc_encrypt",
        "pqc_decrypt",
        "pqc_sign",
        "pqc_verify",
        "pqc_seal",
        "pqc_open",
        "pqc_rotate_keys",
    ]

    def __init__(
        self,
        agent_id: str = "security-agent",
        channel: str = "tasks",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        super().__init__(agent_id, channel, redis_host, redis_port, redis_db)
        # In-memory key store: maps logical key-id → serialized public/private key bytes.
        # Keys are never written to disk by this agent.
        self._kem_keys: dict[str, dict] = {}   # key_id → {public_key, private_key}
        self._sig_keys: dict[str, dict] = {}   # key_id → {public_key, private_key}

    # ------------------------------------------------------------------
    # Task Execution
    # ------------------------------------------------------------------

    def _perform_task(self, task: str, details: dict):
        """Execute a PQC security task based on the task identifier."""
        print(f"🔐 [{self.agent_id}] Executing security task: {task}")

        handlers = {
            "generate_kem_keypair": self._generate_kem_keypair,
            "generate_sig_keypair": self._generate_sig_keypair,
            "encrypt_payload": self._encrypt_payload,
            "decrypt_payload": self._decrypt_payload,
            "sign_payload": self._sign_payload,
            "verify_payload": self._verify_payload,
            "seal_envelope": self._seal_envelope,
            "open_envelope": self._open_envelope,
            "rotate_keys": self._rotate_keys,
        }

        handler = handlers.get(task)
        if handler:
            handler(details)
        else:
            print(f"⚠️  [{self.agent_id}] Unknown security task: {task}. Logging and continuing.")
            self._log_unknown_task(task, details)

    # ------------------------------------------------------------------
    # Key Generation
    # ------------------------------------------------------------------

    def _generate_kem_keypair(self, details: dict):
        """Generate a fresh ML-KEM-768 key pair and store it in-memory."""
        from components.pqc_crypto import PQCKeyPair, PQCUnavailableError

        key_id = details.get("key_id", f"kem-{int(time.time())}")
        print(f"🔑 [{self.agent_id}] Generating ML-KEM-768 keypair | key_id={key_id}")
        try:
            keypair = PQCKeyPair.generate_kem()
            self._kem_keys[key_id] = {
                "public_key": keypair.public_key,
                "private_key": keypair.private_key,
            }
            result = (
                f"ML-KEM-768 keypair generated | key_id={key_id} | "
                f"public_key_len={len(keypair.public_key)}B"
            )
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("generate_kem_keypair", result, {"key_id": key_id})
        except PQCUnavailableError as exc:
            self._publish_error("generate_kem_keypair", str(exc))

    def _generate_sig_keypair(self, details: dict):
        """Generate a fresh ML-DSA-65 (Dilithium3) key pair and store it in-memory."""
        from components.pqc_crypto import PQCKeyPair, PQCUnavailableError

        key_id = details.get("key_id", f"sig-{int(time.time())}")
        print(f"🖊️  [{self.agent_id}] Generating ML-DSA-65 keypair | key_id={key_id}")
        try:
            keypair = PQCKeyPair.generate_sig()
            self._sig_keys[key_id] = {
                "public_key": keypair.public_key,
                "private_key": keypair.private_key,
            }
            result = (
                f"ML-DSA-65 keypair generated | key_id={key_id} | "
                f"public_key_len={len(keypair.public_key)}B"
            )
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("generate_sig_keypair", result, {"key_id": key_id})
        except PQCUnavailableError as exc:
            self._publish_error("generate_sig_keypair", str(exc))

    # ------------------------------------------------------------------
    # Encryption / Decryption
    # ------------------------------------------------------------------

    def _encrypt_payload(self, details: dict):
        """
        Encrypt a raw payload using ML-KEM-768 + ChaCha20-Poly1305.

        Expected detail keys:
            payload (bytes | str): plaintext to encrypt.
            recipient_key_id (str): key_id of a stored ML-KEM public key.
            associated_data (str, optional): authenticated context string.
        """
        from components.pqc_crypto import PQCEncryptor, PQCUnavailableError

        recipient_key_id = details.get("recipient_key_id", "")
        kem_entry = self._kem_keys.get(recipient_key_id)
        if not kem_entry:
            self._publish_error("encrypt_payload", f"Unknown recipient key_id: {recipient_key_id}")
            return

        payload = details.get("payload", b"")
        if isinstance(payload, str):
            payload = payload.encode()
        associated_data = details.get("associated_data", "")
        ad_bytes = associated_data.encode() if isinstance(associated_data, str) else associated_data

        print(f"🔒 [{self.agent_id}] Encrypting payload | size={len(payload)}B | recipient={recipient_key_id}")
        try:
            encryptor = PQCEncryptor.from_kem_public_key(kem_entry["public_key"])
            ciphertext, tag, nonce = encryptor.encrypt(payload, associated_data=ad_bytes or None)
            result = (
                f"Payload encrypted | ciphertext_len={len(ciphertext)}B | "
                f"nonce_len={len(nonce)}B | tag_len={len(tag)}B"
            )
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result(
                "encrypt_payload",
                result,
                {
                    "kem_ciphertext": encryptor.kem_ciphertext.hex(),
                    "ciphertext": ciphertext.hex(),
                    "tag": tag.hex(),
                    "nonce": nonce.hex(),
                },
            )
        except PQCUnavailableError as exc:
            self._publish_error("encrypt_payload", str(exc))

    def _decrypt_payload(self, details: dict):
        """
        Decrypt a payload produced by :meth:`_encrypt_payload`.

        Expected detail keys:
            kem_ciphertext (str): hex-encoded KEM ciphertext.
            ciphertext (str): hex-encoded encrypted payload.
            tag (str): hex-encoded Poly1305 tag.
            nonce (str): hex-encoded nonce.
            recipient_key_id (str): key_id of the stored ML-KEM private key.
            associated_data (str, optional): must match encryption context.
        """
        from components.pqc_crypto import PQCEncryptor, PQCDecryptionError, PQCUnavailableError

        recipient_key_id = details.get("recipient_key_id", "")
        kem_entry = self._kem_keys.get(recipient_key_id)
        if not kem_entry:
            self._publish_error("decrypt_payload", f"Unknown recipient key_id: {recipient_key_id}")
            return

        try:
            kem_ciphertext = bytes.fromhex(details["kem_ciphertext"])
            ciphertext = bytes.fromhex(details["ciphertext"])
            tag = bytes.fromhex(details["tag"])
            nonce = bytes.fromhex(details["nonce"])
        except (KeyError, ValueError) as exc:
            self._publish_error("decrypt_payload", f"Invalid ciphertext fields: {exc}")
            return

        associated_data = details.get("associated_data", "")
        ad_bytes = associated_data.encode() if isinstance(associated_data, str) else associated_data

        print(f"🔓 [{self.agent_id}] Decrypting payload | ciphertext_len={len(ciphertext)}B")
        try:
            decryptor = PQCEncryptor.from_kem_private_key(kem_entry["private_key"], kem_ciphertext)
            plaintext = decryptor.decrypt(ciphertext, tag, nonce, associated_data=ad_bytes or None)
            result = f"Payload decrypted successfully | plaintext_len={len(plaintext)}B"
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("decrypt_payload", result)
        except (PQCDecryptionError, PQCUnavailableError) as exc:
            self._publish_error("decrypt_payload", str(exc))

    # ------------------------------------------------------------------
    # Signing / Verification
    # ------------------------------------------------------------------

    def _sign_payload(self, details: dict):
        """
        Sign a payload with ML-DSA-65.

        Expected detail keys:
            payload (bytes | str): message to sign.
            sig_key_id (str): key_id of the stored ML-DSA signing key.
        """
        from components.pqc_crypto import PQCKeyPair, PQCSigner, PQCUnavailableError

        sig_key_id = details.get("sig_key_id", "")
        sig_entry = self._sig_keys.get(sig_key_id)
        if not sig_entry:
            self._publish_error("sign_payload", f"Unknown sig key_id: {sig_key_id}")
            return

        payload = details.get("payload", b"")
        if isinstance(payload, str):
            payload = payload.encode()

        print(f"🖊️  [{self.agent_id}] Signing payload | size={len(payload)}B | key={sig_key_id}")
        try:
            from components.pqc_crypto import SIG_ALGORITHM
            keypair = PQCKeyPair(
                algorithm=SIG_ALGORITHM,
                public_key=sig_entry["public_key"],
                private_key=sig_entry["private_key"],
            )
            signer = PQCSigner(keypair)
            signature = signer.sign(payload)
            result = f"Payload signed | signature_len={len(signature)}B | key={sig_key_id}"
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result(
                "sign_payload",
                result,
                {
                    "signature": signature.hex(),
                    "public_key": sig_entry["public_key"].hex(),
                },
            )
        except PQCUnavailableError as exc:
            self._publish_error("sign_payload", str(exc))

    def _verify_payload(self, details: dict):
        """
        Verify an ML-DSA-65 signature.

        Expected detail keys:
            payload (bytes | str): original signed message.
            signature (str): hex-encoded signature.
            public_key (str): hex-encoded ML-DSA public key.
        """
        from components.pqc_crypto import PQCSigner, PQCUnavailableError

        payload = details.get("payload", b"")
        if isinstance(payload, str):
            payload = payload.encode()

        try:
            signature = bytes.fromhex(details["signature"])
            public_key = bytes.fromhex(details["public_key"])
        except (KeyError, ValueError) as exc:
            self._publish_error("verify_payload", f"Invalid signature fields: {exc}")
            return

        print(f"🔎 [{self.agent_id}] Verifying ML-DSA-65 signature | msg_len={len(payload)}B")
        try:
            valid = PQCSigner.verify(payload, signature, public_key)
            status = "VALID" if valid else "INVALID"
            result = f"Signature verification: {status}"
            print(f"{'✅' if valid else '❌'} [{self.agent_id}] {result}")
            self._publish_result("verify_payload", result, {"valid": valid})
        except PQCUnavailableError as exc:
            self._publish_error("verify_payload", str(exc))

    # ------------------------------------------------------------------
    # High-level seal / open
    # ------------------------------------------------------------------

    def _seal_envelope(self, details: dict):
        """
        Seal a payload into a signed, encrypted :class:`SignedEnvelope`.

        Expected detail keys:
            payload (bytes | str): plaintext to seal.
            recipient_key_id (str): key_id of recipient ML-KEM public key.
            sender_sig_key_id (str, optional): key_id of sender ML-DSA key.
            associated_data (str, optional): binding context string.
        """
        from components.pqc_crypto import (
            PQCKeyPair,
            PQCUnavailableError,
            SIG_ALGORITHM,
            seal,
        )

        recipient_key_id = details.get("recipient_key_id", "")
        kem_entry = self._kem_keys.get(recipient_key_id)
        if not kem_entry:
            self._publish_error("seal_envelope", f"Unknown recipient key_id: {recipient_key_id}")
            return

        payload = details.get("payload", b"")
        if isinstance(payload, str):
            payload = payload.encode()

        associated_data = details.get("associated_data", "")
        ad_bytes = associated_data.encode() if isinstance(associated_data, str) else associated_data

        sender_sig_keypair = None
        sender_sig_key_id = details.get("sender_sig_key_id", "")
        if sender_sig_key_id:
            sig_entry = self._sig_keys.get(sender_sig_key_id)
            if sig_entry:
                sender_sig_keypair = PQCKeyPair(
                    algorithm=SIG_ALGORITHM,
                    public_key=sig_entry["public_key"],
                    private_key=sig_entry["private_key"],
                )

        print(
            f"📦 [{self.agent_id}] Sealing envelope | size={len(payload)}B | "
            f"recipient={recipient_key_id} | signed={sender_sig_keypair is not None}"
        )
        try:
            envelope = seal(
                payload,
                kem_entry["public_key"],
                sender_sig_keypair=sender_sig_keypair,
                associated_data=ad_bytes or None,
            )
            raw = envelope.to_bytes()
            result = f"Envelope sealed | envelope_len={len(raw)}B | signed={envelope.signature is not None}"
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("seal_envelope", result, {"envelope": raw.hex()})
        except PQCUnavailableError as exc:
            self._publish_error("seal_envelope", str(exc))

    def _open_envelope(self, details: dict):
        """
        Open a sealed envelope produced by :meth:`_seal_envelope`.

        Expected detail keys:
            envelope (str): hex-encoded serialized SignedEnvelope.
            recipient_key_id (str): key_id of the stored ML-KEM private key.
            associated_data (str, optional): must match sealing context.
            verify_signature (bool, optional): defaults to True.
        """
        from components.pqc_crypto import (
            PQCDecryptionError,
            PQCUnavailableError,
            SignedEnvelope,
            open_envelope,
        )

        recipient_key_id = details.get("recipient_key_id", "")
        kem_entry = self._kem_keys.get(recipient_key_id)
        if not kem_entry:
            self._publish_error("open_envelope", f"Unknown recipient key_id: {recipient_key_id}")
            return

        try:
            envelope_bytes = bytes.fromhex(details["envelope"])
            envelope = SignedEnvelope.from_bytes(envelope_bytes)
        except (KeyError, ValueError) as exc:
            self._publish_error("open_envelope", f"Invalid envelope data: {exc}")
            return

        associated_data = details.get("associated_data", "")
        ad_bytes = associated_data.encode() if isinstance(associated_data, str) else associated_data
        verify_sig = details.get("verify_signature", True)

        print(f"📬 [{self.agent_id}] Opening envelope | verify_sig={verify_sig}")
        try:
            plaintext = open_envelope(
                envelope,
                kem_entry["private_key"],
                associated_data=ad_bytes or None,
                verify_signature=verify_sig,
            )
            result = f"Envelope opened successfully | plaintext_len={len(plaintext)}B"
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("open_envelope", result)
        except (PQCDecryptionError, PQCUnavailableError, ValueError) as exc:
            self._publish_error("open_envelope", str(exc))

    # ------------------------------------------------------------------
    # Key Rotation
    # ------------------------------------------------------------------

    def _rotate_keys(self, details: dict):
        """
        Rotate a stored key by generating a fresh replacement.

        Expected detail keys:
            key_type (str): "kem" or "sig".
            key_id (str): the logical key identifier to rotate.
        """
        from components.pqc_crypto import PQCKeyPair, PQCUnavailableError

        key_type = details.get("key_type", "kem").lower()
        key_id = details.get("key_id", "")

        if key_type not in ("kem", "sig"):
            self._publish_error("rotate_keys", f"Invalid key_type '{key_type}' — must be 'kem' or 'sig'")
            return

        print(f"🔄 [{self.agent_id}] Rotating {key_type.upper()} key | key_id={key_id}")
        try:
            if key_type == "kem":
                keypair = PQCKeyPair.generate_kem()
                self._kem_keys[key_id] = {
                    "public_key": keypair.public_key,
                    "private_key": keypair.private_key,
                }
            else:
                keypair = PQCKeyPair.generate_sig()
                self._sig_keys[key_id] = {
                    "public_key": keypair.public_key,
                    "private_key": keypair.private_key,
                }
            result = (
                f"{key_type.upper()} key rotated | key_id={key_id} | "
                f"public_key_len={len(keypair.public_key)}B"
            )
            print(f"✅ [{self.agent_id}] {result}")
            self._publish_result("rotate_keys", result, {"key_id": key_id, "key_type": key_type})
        except PQCUnavailableError as exc:
            self._publish_error("rotate_keys", str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _log_unknown_task(self, task: str, details: dict):
        """Log an unrecognized task for debugging."""
        print(f"📋 [{self.agent_id}] Unknown task '{task}' — details: {details}")

    def _publish_result(self, task: str, result: str, extra: dict | None = None):
        """Publish a task result back to the Redis channel."""
        payload = {"agent": self.agent_id, "task": task, "result": result}
        if extra:
            payload.update(extra)
        self.coordinator.publish("RESULT", task, payload)
        print(f"📤 [{self.agent_id}] Result published for task '{task}'")

    def _publish_error(self, task: str, message: str):
        """Publish a task error back to the Redis channel."""
        print(f"❌ [{self.agent_id}] Error in '{task}': {message}")
        self.coordinator.publish(
            "RESULT",
            task,
            {"agent": self.agent_id, "task": task, "error": message},
        )
