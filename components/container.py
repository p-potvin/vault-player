import os
import struct
import json
from typing import Optional, Iterator, BinaryIO, Dict, Any

from components.pqc_crypto import PQCEncryptor, PQCKeyPair, PQCSigner

MAGIC_BYTES = b"VAULTV1\0"
DEFAULT_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB

def _pack_field(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data

def _unpack_field(fh: BinaryIO) -> bytes:
    len_bytes = fh.read(4)
    if not len_bytes:
        raise EOFError("Unexpected end of file")
    (length,) = struct.unpack(">I", len_bytes)
    data = fh.read(length)
    if len(data) != length:
        raise EOFError("Unexpected end of file reading field")
    return data

class VaultContainerWriter:
    def __init__(
        self,
        output_fh: BinaryIO,
        recipient_kem_public_key: bytes,
        sender_sig_keypair: Optional[PQCKeyPair] = None,
        associated_data: Optional[bytes] = None,
    ):
        self._fh = output_fh
        self._encryptor = PQCEncryptor.from_kem_public_key(recipient_kem_public_key)
        self._sender_sig = sender_sig_keypair
        self._ad = associated_data or b""
        
        self._fh.write(MAGIC_BYTES)
        self._fh.write(_pack_field(self._encryptor.kem_ciphertext))

    def write_manifest(self, manifest_dict: Dict[str, Any]) -> None:
        manifest_bytes = json.dumps(manifest_dict).encode('utf-8')
        ciphertext, tag, nonce = self._encryptor.encrypt(manifest_bytes, self._ad)
        
        manifest_payload = _pack_field(nonce) + _pack_field(tag) + _pack_field(ciphertext)
        
        sig_data = b""
        pub_key = b""
        if self._sender_sig:
            signer = PQCSigner(self._sender_sig)
            sig_data = signer.sign(self._encryptor.kem_ciphertext + manifest_payload)
            pub_key = self._sender_sig.public_key
            
        self._fh.write(_pack_field(pub_key))
        self._fh.write(_pack_field(sig_data))
        self._fh.write(manifest_payload)

    def write_chunk(self, chunk: bytes) -> None:
        if not chunk:
            return
        ciphertext, tag, nonce = self._encryptor.encrypt(chunk, self._ad)
        self._fh.write(_pack_field(nonce))
        self._fh.write(_pack_field(tag))
        self._fh.write(_pack_field(ciphertext))


class VaultContainerReader:
    def __init__(
        self,
        input_fh: BinaryIO,
        recipient_kem_private_key: bytes,
        associated_data: Optional[bytes] = None,
        verify_sender_public_key: Optional[bytes] = None,
    ):
        self._fh = input_fh
        self._ad = associated_data or b""
        
        magic = self._fh.read(8)
        if magic != MAGIC_BYTES:
            raise ValueError("Invalid Vault container magic bytes")
            
        self.kem_ciphertext = _unpack_field(self._fh)
        self._encryptor = PQCEncryptor.from_kem_private_key(recipient_kem_private_key, self.kem_ciphertext)
        
        self.sig_public_key = _unpack_field(self._fh)
        self.signature = _unpack_field(self._fh)
        
        nonce = _unpack_field(self._fh)
        tag = _unpack_field(self._fh)
        ciphertext = _unpack_field(self._fh)
        
        manifest_payload = _pack_field(nonce) + _pack_field(tag) + _pack_field(ciphertext)
        
        if self.sig_public_key and self.signature:
            if verify_sender_public_key and self.sig_public_key != verify_sender_public_key:
                raise ValueError("Sender public key mismatch")
            is_valid = PQCSigner.verify(
                self.kem_ciphertext + manifest_payload,
                self.signature,
                self.sig_public_key
            )
            if not is_valid:
                raise ValueError("Container signature verification failed")
        elif verify_sender_public_key:
            raise ValueError("Container is unsigned, but sender key verification was required")
            
        manifest_bytes = self._encryptor.decrypt(ciphertext, tag, nonce, self._ad)
        self.manifest = json.loads(manifest_bytes.decode('utf-8'))

    def iter_chunks(self) -> Iterator[bytes]:
        while True:
            try:
                nonce = _unpack_field(self._fh)
            except EOFError:
                break
            tag = _unpack_field(self._fh)
            ciphertext = _unpack_field(self._fh)
            
            yield self._encryptor.decrypt(ciphertext, tag, nonce, self._ad)

def export_standard_format(
    vault_path: str,
    output_path: str,
    recipient_kem_private_key: bytes,
    associated_data: Optional[bytes] = None,
    verify_sender_public_key: Optional[bytes] = None,
) -> None:
    """
    Export a .vault file back to its standard wrapper format (e.g. MP4, MKV) 
    for authorized external clients.
    """
    with open(vault_path, "rb") as in_fh, open(output_path, "wb") as out_fh:
        reader = VaultContainerReader(
            in_fh,
            recipient_kem_private_key,
            associated_data,
            verify_sender_public_key
        )
        for chunk in reader.iter_chunks():
            out_fh.write(chunk)

def encapsulate_standard_format(
    input_path: str,
    vault_path: str,
    recipient_kem_public_key: bytes,
    sender_sig_keypair: Optional[PQCKeyPair] = None,
    associated_data: Optional[bytes] = None,
    manifest_metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> None:
    """
    Wrap a standard file (MP4, MKV) into the Vault post-quantum streaming format.
    """
    manifest = manifest_metadata or {}
    
    with open(input_path, "rb") as in_fh, open(vault_path, "wb") as out_fh:
        writer = VaultContainerWriter(
            out_fh,
            recipient_kem_public_key,
            sender_sig_keypair,
            associated_data
        )
        writer.write_manifest(manifest)
        
        while True:
            chunk = in_fh.read(chunk_size)
            if not chunk:
                break
            writer.write_chunk(chunk)
