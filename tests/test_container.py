import os
import tempfile
import json
import pytest
from unittest.mock import patch, MagicMock

import components.pqc_crypto

# Mock OQS so we can run tests without compiling liboqs on Windows
class MockPQCKeypair:
    def __init__(self, pub, priv):
        self.public_key = pub
        self.secret_key = priv
        
    @classmethod
    def generate_kem(cls):
        return cls(b"pub", b"priv")
        
    @classmethod
    def generate_sig(cls):
        return cls(b"sig_pub", b"sig_priv")

class MockPQCEncryptor:
    def __init__(self, kem_public_key=None, kem_private_key=None, kem_ciphertext=None):
        self.kem_ciphertext = b"mock_kem_ciphertext"
        
    @classmethod
    def from_kem_public_key(cls, kem_public_key):
        return cls(kem_public_key=kem_public_key)
        
    @classmethod
    def from_kem_private_key(cls, kem_private_key, kem_ciphertext):
        return cls(kem_private_key=kem_private_key, kem_ciphertext=kem_ciphertext)
        
    def encrypt(self, plaintext, associated_data=None):
        # Return mock ciphertext, tag, nonce
        return (plaintext, b"tag", b"nonce")
        
    def decrypt(self, ciphertext, tag, nonce, associated_data=None):
        return ciphertext

class MockPQCSigner:
    def __init__(self, keypair):
        self.keypair = keypair
        
    def sign(self, message):
        return b"mock_signature"
        
    @classmethod
    def verify(cls, message, signature, public_key):
        return signature == b"mock_signature"

# Patch the pqc_crypto module classes
components.pqc_crypto.PQCKeyPair = MockPQCKeypair
components.pqc_crypto.PQCEncryptor = MockPQCEncryptor
components.pqc_crypto.PQCSigner = MockPQCSigner

from components.container import (
    VaultContainerWriter,
    VaultContainerReader,
    export_standard_format,
    encapsulate_standard_format,
    MAGIC_BYTES
)

def test_container_read_write_memory():
    import io
    # Generate mock keys
    recipient_kem = MockPQCKeypair.generate_kem()
    sender_sig = MockPQCKeypair.generate_sig()
    
    out_fh = io.BytesIO()
    
    # Write
    writer = VaultContainerWriter(out_fh, recipient_kem.public_key, sender_sig)
    manifest = {"video": "test.mp4", "duration": 120}
    writer.write_manifest(manifest)
    
    chunk1 = b"Hello, vault stream 1"
    chunk2 = b"Hello, vault stream 2"
    writer.write_chunk(chunk1)
    writer.write_chunk(chunk2)
    
    # Reset
    out_fh.seek(0)
    
    # Read
    reader = VaultContainerReader(out_fh, recipient_kem.secret_key, verify_sender_public_key=sender_sig.public_key)
    
    assert reader.manifest == manifest
    chunks = list(reader.iter_chunks())
    
    assert chunks[0] == chunk1
    assert chunks[1] == chunk2

def test_encapsulate_and_export():
    recipient_kem = MockPQCKeypair.generate_kem()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        input_mp4 = os.path.join(temp_dir, "input.mp4")
        vault_file = os.path.join(temp_dir, "video.vault")
        output_mp4 = os.path.join(temp_dir, "output.mp4")
        
        # Create a dummy media file
        original_data = os.urandom(10 * 1024 * 1024) # 10 MB payload
        with open(input_mp4, "wb") as f:
            f.write(original_data)
            
        manifest = {"title": "Dummy 10MB file"}
        
        encapsulate_standard_format(
            input_mp4,
            vault_file,
            recipient_kem.public_key,
            manifest_metadata=manifest,
            chunk_size=4*1024*1024
        )
        
        # Verify it created something
        assert os.path.exists(vault_file)
        assert os.path.getsize(vault_file) > 0
        
        export_standard_format(
            vault_file,
            output_mp4,
            recipient_kem.secret_key
        )
        
        with open(output_mp4, "rb") as f:
            recovered_data = f.read()
            
        assert original_data == recovered_data
