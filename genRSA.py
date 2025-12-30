"""
GENRSA - Công cụ tạo cặp khóa RSA đơn giản
=====================================

Script tiện ích để tạo cặp khóa public/private RSA cho
quá trình steganography. Các script encode/decode sử dụng
trực tiếp các file PEM này.
"""

import argparse
from pathlib import Path
from Crypto.PublicKey import RSA


def generate_keypair(bits: int) -> tuple[bytes, bytes]:
    """Tạo cặp khóa RSA và trả về (public_pem, private_pem)."""
    key = RSA.generate(bits)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return public_key, private_key


def write_key(path: Path, data: bytes) -> None:
    """Lưu khóa vào đĩa, tạo thư mục cha nếu cần."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tạo cặp khóa public/private RSA cho steganography."
    )
    parser.add_argument(
        "--bits",
        type=int,
        default=2048,
        choices=(1024, 2048, 3072, 4096),
        help="Độ dài khóa theo bit (mặc định: 2048).",
    )
    parser.add_argument(
        "--public",
        type=Path,
        default=Path("public_key.pem"),
        help="Đường dẫn lưu khóa public.",
    )
    parser.add_argument(
        "--private",
        type=Path,
        default=Path("private_key.pem"),
        help="Đường dẫn lưu khóa private.",
    )
    args = parser.parse_args()

    print(f"Đang tạo cặp khóa RSA ({args.bits} bits)...")
    public_key, private_key = generate_keypair(args.bits)

    write_key(args.public, public_key)
    write_key(args.private, private_key)

    print(f"Đã lưu khóa public vào: {args.public}")
    print(f"Đã lưu khóa private vào: {args.private}")
    print("Hãy giữ an toàn khóa private!")


if __name__ == "__main__":
    main()

