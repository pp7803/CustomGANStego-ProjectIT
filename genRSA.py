#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENRSA - Simple RSA keypair generator
=====================================

Utility script to create RSA public/private key pairs for the
steganography pipeline. The encode/decode scripts consume these PEM
files directly.
"""

import argparse
from pathlib import Path
from Crypto.PublicKey import RSA


def generate_keypair(bits: int) -> tuple[bytes, bytes]:
    """Generate an RSA keypair and return (public_pem, private_pem)."""
    key = RSA.generate(bits)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return public_key, private_key


def write_key(path: Path, data: bytes) -> None:
    """Persist a key to disk, creating parent folders as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate RSA public/private key pair for steganography."
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=2048,
        choices=(1024, 2048, 3072, 4096),
        help="Key length in bits (default: 2048).",
    )
    parser.add_argument(
        "--public",
        type=Path,
        default=Path("public_key.pem"),
        help="Destination path for the public key.",
    )
    parser.add_argument(
        "--private",
        type=Path,
        default=Path("private_key.pem"),
        help="Destination path for the private key.",
    )
    args = parser.parse_args()

    print(f"🔑 Generating RSA keypair ({args.bits} bits)...")
    public_key, private_key = generate_keypair(args.bits)

    write_key(args.public, public_key)
    write_key(args.private, private_key)

    print(f"✅ Saved public key to: {args.public}")
    print(f"✅ Saved private key to: {args.private}")
    print("⚠️  Keep the private key safe!")


if __name__ == "__main__":
    main()

