"""Demo authentication and UI SSO (CAS 2.0) integration for Rak-it! Pacil (Member 3)."""

from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Iterable

from models import User

SSO_CAS_BASE_URL = os.environ.get("SSO_CAS_BASE_URL", "https://sso.ui.ac.id/cas2/")
CAS_NAMESPACE = {"cas": "http://www.yale.edu/tp/cas"}

SSO_DIRECTORY: dict[str, dict] = {
    "jonathan.tan": {
        "name": "Jonathan Christopher Tan",
        "npm": "2306214509",
        "username": "jonathan.tan",
        "role": "asdos",
        "title": "Asdos DDP 1, DDP 2 & SDA",
        "assignedClasses": ["ddp1-g", "ddp2-c", "sda-reg"],
    },
    "nadia.khairunnisa": {
        "name": "Nadia Khairunnisa",
        "npm": "2306215567",
        "username": "nadia.khairunnisa",
        "role": "asdos",
        "title": "Asdos Basdat, OS & Jarkom",
        "assignedClasses": ["basdat-a", "os-a", "jarkom-a"],
    },
    "alya.zahra24": {
        "name": "Alya Zahra Ramadhani",
        "npm": "2406351891",
        "username": "alya.zahra24",
        "role": "mahasiswa",
        "title": "Mahasiswa Ilmu Komputer 2024",
        "assignedClasses": [],
    },
    "muhammad.rafli24": {
        "name": "Muhammad Rafli Alfarizi",
        "npm": "2406351204",
        "username": "muhammad.rafli24",
        "role": "mahasiswa",
        "title": "Mahasiswa Sistem Informasi 2024",
        "assignedClasses": [],
    },
}

# TA authorization lists (checked for both demo and real SSO UI logins)
TA_USERNAME_WHITELIST: set[str] = {"jonathan.tan", "nadia.khairunnisa"}
TA_NPM_WHITELIST: set[str] = {"2306214509", "2306215567"}

DEFAULT_ALL_CLASSES = ["ddp1-g", "ddp2-c", "sda-reg", "basdat-a", "os-a", "jarkom-a"]


def is_real_sso_enabled() -> bool:
    """Return True when real SSO UI CAS login is explicitly enabled via env var."""
    return os.environ.get("ENABLE_REAL_SSO", "").strip().lower() in {"1", "true", "yes"}


def _format_display_name(username: str) -> str:
    parts = [
        "".join(ch for ch in part if not ch.isdigit())
        for part in username.split(".")
    ]
    words = [part.capitalize() for part in parts if part]
    return " ".join(words) if words else username


def authenticate_demo(
    raw_username: str,
    all_class_ids: Iterable[str] | None = None,
) -> dict | None:
    """Authenticate a local demo user matching the HTML mockup's SSO directory rules."""
    cleaned = raw_username.strip().lower().replace("@ui.ac.id", "")
    if not cleaned:
        return None

    if cleaned in SSO_DIRECTORY:
        return dict(SSO_DIRECTORY[cleaned])

    available_classes = list(all_class_ids) if all_class_ids else list(DEFAULT_ALL_CLASSES)
    auto_role = "asdos" if ("asdos" in cleaned or cleaned in TA_USERNAME_WHITELIST) else "mahasiswa"
    return User(
        name=_format_display_name(cleaned),
        npm="2306219901" if auto_role == "asdos" else "2406358821",
        username=cleaned,
        role=auto_role,
        title="Asisten Dosen Fasilkom" if auto_role == "asdos" else "Mahasiswa Fasilkom",
        assigned_classes=available_classes if auto_role == "asdos" else [],
    ).to_dict()


def build_cas_login_url(service_url: str) -> str:
    """Build the UI SSO CAS 2.0 login redirect URL."""
    base = SSO_CAS_BASE_URL.rstrip("/") + "/login"
    return f"{base}?{urllib.parse.urlencode({'service': service_url})}"


def build_cas_logout_url(service_url: str) -> str:
    """Build the UI SSO CAS 2.0 logout redirect URL."""
    base = SSO_CAS_BASE_URL.rstrip("/") + "/logout"
    return f"{base}?{urllib.parse.urlencode({'url': service_url})}"


def _parse_cas_xml(xml_payload: str, all_class_ids: Iterable[str] | None = None) -> dict | None:
    """Parse a CAS 2.0 serviceValidate XML response into a normalized User dict."""
    try:
        root = ET.fromstring(xml_payload)
    except ET.ParseError:
        return None

    success = root.find("cas:authenticationSuccess", CAS_NAMESPACE)
    if success is None:
        return None

    username_el = success.find("cas:user", CAS_NAMESPACE)
    if username_el is None or not (username_el.text or "").strip():
        return None

    username = username_el.text.strip().lower()
    attrs = success.find("cas:attributes", CAS_NAMESPACE)

    def _attr(tag: str, default: str = "") -> str:
        if attrs is None:
            return default
        el = attrs.find(f"cas:{tag}", CAS_NAMESPACE)
        return el.text.strip() if el is not None and el.text else default

    # TODO: Verify exact CAS attribute names & kd_org faculty/prodi mappings against
    # upperclassmen's SSO UI reference repo (commonly: nama, npm, kd_org, peran_user).
    nama = _attr("nama", _format_display_name(username))
    npm = _attr("npm", "")
    kd_org = _attr("kd_org", "")
    peran_user = _attr("peran_user", "mahasiswa").lower()

    known_entry = SSO_DIRECTORY.get(username)
    if username in TA_USERNAME_WHITELIST or npm in TA_NPM_WHITELIST or peran_user in {"staff", "dosen"}:
        role = "asdos"
    else:
        role = "mahasiswa"

    if role == "asdos":
        if known_entry and known_entry.get("assignedClasses"):
            assigned_classes = list(known_entry["assignedClasses"])
        elif all_class_ids:
            assigned_classes = list(all_class_ids)
        else:
            assigned_classes = list(DEFAULT_ALL_CLASSES)
    else:
        assigned_classes = []

    title_suffix = f" ({kd_org})" if kd_org else ""
    title = (
        f"Asisten Dosen Fasilkom{title_suffix}"
        if role == "asdos"
        else f"Mahasiswa UI{title_suffix}"
    )

    return User(
        name=nama,
        npm=npm or (known_entry["npm"] if known_entry else "0000000000"),
        username=username,
        role=role,
        title=title,
        assigned_classes=assigned_classes,
    ).to_dict()


def validate_cas_ticket(
    ticket: str,
    service_url: str,
    all_class_ids: Iterable[str] | None = None,
    timeout_seconds: float = 8.0,
) -> dict | None:
    """Validate a CAS 2.0 ticket with sso.ui.ac.id and return the authenticated user dict."""
    if not ticket:
        return None

    validate_base = SSO_CAS_BASE_URL.rstrip("/") + "/serviceValidate"
    query = urllib.parse.urlencode({"ticket": ticket, "service": service_url})
    url = f"{validate_base}?{query}"

    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as resp:
            xml_payload = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    return _parse_cas_xml(xml_payload, all_class_ids=all_class_ids)
