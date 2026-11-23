"""Printable compartment QR code generator for Rak-it! Pacil (Member 3)."""

from __future__ import annotations

from pathlib import Path

from models import get_all_cubby_ids


def get_cubby_url(base_url: str, cubby_id: str) -> str:
    """Return the direct compartment URL encoded into a compartment QR sticker."""
    return f"{base_url.rstrip('/')}/slot/{cubby_id.upper()}"


def generate_all_qr_codes(
    base_url: str = "http://127.0.0.1:5000",
    output_dir: str | Path = "qr_codes",
) -> list[Path]:
    """Generate PNG QR stickers for compartments A1-C5 using the optional qrcode package."""
    try:
        import qrcode
    except ImportError as exc:
        raise RuntimeError(
            "Paket 'qrcode[pil]' belum terpasang. "
            "Jalankan: pip install qrcode[pil]"
        ) from exc

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []
    for cubby_id in get_all_cubby_ids():
        url = get_cubby_url(base_url, cubby_id)
        img = qrcode.make(url)
        target = out_path / f"{cubby_id}.png"
        img.save(target)
        generated.append(target)

    return generated


if __name__ == "__main__":
    try:
        files = generate_all_qr_codes()
        print(f"Berhasil membuat {len(files)} QR code di folder qr_codes/.")
    except RuntimeError as err:
        print(err)
