"""SCELE (Moodle Web Services) integration for Rak-it! Pacil (Member 2 / Member 3).

Uses the same Moodle mobile web-service token flow as `scele-cli`:
  1. POST /login/token.php (service=moodle_mobile_app) -> wstoken
  2. POST /webservice/rest/server.php?wsfunction=core_webservice_get_site_info
  3. POST /webservice/rest/server.php?wsfunction=core_enrol_get_users_courses
  4. POST /webservice/rest/server.php?wsfunction=core_enrol_get_enrolled_users
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_SCELE_BASE_URL = os.environ.get("SCELE_BASE_URL", "https://scele.cs.ui.ac.id").rstrip("/")
DEFAULT_SCELE_WS_SERVICE = os.environ.get("SCELE_WS_SERVICE", "moodle_mobile_app")

_NPM_RE = re.compile(r"\b(\d{10})\b")
_STAFF_ROLES = {"editingteacher", "teacher", "manager", "coursecreator"}


class SceleError(Exception):
    """Raised when SCELE authentication or Moodle Web Services calls fail."""


def normalize_base_url(base_url: str | None) -> str:
    """Validate and normalize the SCELE Moodle base URL."""
    url = (base_url or DEFAULT_SCELE_BASE_URL).strip().rstrip("/")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SceleError("URL SCELE tidak valid (gunakan format https://scele.cs.ui.ac.id).")
    return url


def _post_form_json(url: str, form_data: dict[str, str], timeout_seconds: float = 12.0) -> dict | list:
    encoded = urllib.parse.urlencode(form_data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Rak-it-Pacil/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise SceleError(f"Server SCELE menolak permintaan (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SceleError(f"Gagal terhubung ke server SCELE: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SceleError("Respon dari server SCELE bukan JSON yang valid.") from exc


def mint_token(
    username: str,
    password: str,
    base_url: str | None = None,
    service: str = DEFAULT_SCELE_WS_SERVICE,
) -> str:
    """Authenticate against Moodle /login/token.php and return a web-service token."""
    clean_user = username.strip()
    if not clean_user or not password:
        raise SceleError("Username dan password SCELE wajib diisi.")

    root_url = normalize_base_url(base_url)
    data = _post_form_json(
        f"{root_url}/login/token.php",
        {
            "username": clean_user,
            "password": password,
            "service": service,
        },
    )

    if isinstance(data, dict) and data.get("token"):
        return str(data["token"]).strip()

    err_msg = (
        data.get("error") or data.get("message") or "Username atau password SCELE salah."
        if isinstance(data, dict)
        else "Gagal mendapatkan token SCELE."
    )
    raise SceleError(str(err_msg))


def call_ws(
    token: str,
    wsfunction: str,
    params: dict[str, str | int] | None = None,
    base_url: str | None = None,
) -> dict | list:
    """Call a Moodle REST web-service function using a minted wstoken."""
    if not token:
        raise SceleError("Token SCELE belum tersedia. Silakan hubungkan akun SCELE terlebih dahulu.")

    root_url = normalize_base_url(base_url)
    payload: dict[str, str] = {
        "wstoken": token,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
    }
    if params:
        for key, value in params.items():
            payload[str(key)] = str(value)

    data = _post_form_json(f"{root_url}/webservice/rest/server.php", payload)

    if isinstance(data, dict) and (data.get("exception") or data.get("errorcode")):
        message = data.get("message") or data.get("errorcode") or "Permintaan SCELE gagal."
        raise SceleError(f"SCELE API error ({wsfunction}): {message}")

    return data


def get_site_info(token: str, base_url: str | None = None) -> dict:
    """Verify the token and retrieve the authenticated SCELE user profile."""
    raw = call_ws(token, "core_webservice_get_site_info", base_url=base_url)
    if not isinstance(raw, dict) or not raw.get("userid"):
        raise SceleError("Gagal membaca profil pengguna dari SCELE.")

    return {
        "userid": int(raw["userid"]),
        "username": str(raw.get("username", "")),
        "fullname": str(raw.get("fullname", raw.get("username", "Pengguna SCELE"))),
        "sitename": str(raw.get("sitename", "SCELE Fasilkom UI")),
    }


def parse_course_label(shortname: str, fullname: str) -> tuple[str, str]:
    """Infer clean (course_name, class_name) defaults from a SCELE course title."""
    clean_full = (fullname or shortname or "Mata Kuliah").strip()
    clean_short = (shortname or clean_full).strip()

    # Common Fasilkom patterns e.g. "DDP 1 - Kelas G (Gasal 2026)" or "CSGE601020 - DDP 1"
    class_match = re.search(r"\b(Kelas\s+[A-Z0-9]+|KKI|Reguler|Paralel)\b", clean_full, re.IGNORECASE)
    suggested_class = class_match.group(1) if class_match else "Umum"

    course_part = clean_short
    if " - " in clean_full:
        parts = [p.strip() for p in clean_full.split(" - ") if p.strip()]
        # Skip leading course code like CSGE601020 if present
        if len(parts) >= 2 and re.match(r"^[A-Z]{2,5}\d{4,}$", parts[0]):
            course_part = parts[1]
        else:
            course_part = parts[0]

    return course_part[:48], suggested_class[:32]


def get_user_courses(token: str, userid: int, base_url: str | None = None) -> list[dict]:
    """Fetch visible courses the authenticated user is enrolled in on SCELE."""
    raw = call_ws(
        token,
        "core_enrol_get_users_courses",
        params={"userid": userid},
        base_url=base_url,
    )
    if not isinstance(raw, list):
        return []

    courses: list[dict] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        shortname = str(item.get("shortname", "")).strip()
        fullname = str(item.get("fullname") or item.get("displayname") or shortname).strip()
        suggested_course, suggested_class = parse_course_label(shortname, fullname)
        courses.append(
            {
                "id": int(item["id"]),
                "shortname": shortname,
                "fullname": fullname,
                "enrolledusercount": int(item.get("enrolledusercount") or 0),
                "suggestedCourse": suggested_course,
                "suggestedClassName": suggested_class,
            }
        )

    courses.sort(key=lambda c: c["id"], reverse=True)
    return courses


def parse_enrolled_users(
    raw_users: list[dict],
    only_students: bool = True,
) -> tuple[list[dict], list[str]]:
    """Normalize Moodle core_enrol_get_enrolled_users output into Student dicts + group names."""
    students: list[dict] = []
    group_names: set[str] = set()

    for entry in raw_users:
        if not isinstance(entry, dict):
            continue

        roles = [
            str(r.get("shortname", "")).lower()
            for r in (entry.get("roles") or [])
            if isinstance(r, dict)
        ]
        if only_students and roles:
            if "student" not in roles and any(r in _STAFF_ROLES for r in roles):
                continue
            if "student" not in roles and roles:
                continue

        fullname = str(entry.get("fullname") or "").strip()
        if not fullname:
            first = str(entry.get("firstname") or "").strip()
            last = str(entry.get("lastname") or "").strip()
            fullname = f"{first} {last}".strip()

        idnumber = str(entry.get("idnumber") or "").strip()
        username = str(entry.get("username") or "").strip()
        email = str(entry.get("email") or "").strip()

        if not username and email and "@" in email:
            username = email.split("@")[0].strip().lower()

        # Extract NPM (10-digit UI student ID) from idnumber, fullname, or username
        npm = ""
        if idnumber:
            npm_match = _NPM_RE.search(idnumber)
            npm = npm_match.group(1) if npm_match else idnumber
        if not npm:
            npm_match = _NPM_RE.search(fullname) or _NPM_RE.search(username)
            if npm_match:
                npm = npm_match.group(1)
        if not npm and entry.get("id") is not None:
            npm = str(entry["id"])

        # Clean redundant "2406351891 - " prefix if present in fullname
        clean_name = re.sub(r"^\d{8,12}\s*[-–—]\s*", "", fullname).strip() or fullname

        if not username and clean_name:
            username = ".".join(clean_name.lower().split()[:2])

        user_groups = [
            str(g.get("name", "")).strip()
            for g in (entry.get("groups") or [])
            if isinstance(g, dict) and str(g.get("name", "")).strip()
        ]
        for gname in user_groups:
            group_names.add(gname)

        if npm and clean_name:
            students.append(
                {
                    "npm": npm,
                    "name": clean_name,
                    "username": username,
                    "groups": user_groups,
                }
            )

    students.sort(key=lambda s: s["name"].lower())
    return students, sorted(group_names)


def get_course_students(
    token: str,
    course_id: int,
    base_url: str | None = None,
    only_students: bool = True,
) -> tuple[list[dict], list[str]]:
    """Fetch enrolled users for a SCELE course and normalize them into our roster format."""
    raw = call_ws(
        token,
        "core_enrol_get_enrolled_users",
        params={"courseid": course_id},
        base_url=base_url,
    )
    if not isinstance(raw, list):
        return [], []
    return parse_enrolled_users(raw, only_students=only_students)


def slugify_class_id(prefix: str, text: str) -> str:
    """Create a stable lowercase kebab-case roster ID."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return f"{prefix}-{slug}" if slug else prefix
