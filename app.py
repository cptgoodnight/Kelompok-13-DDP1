"""Flask web application & REST API for Rak-it! Pacil (Member 4)."""

from __future__ import annotations

import os
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from auth import (
    authenticate_demo,
    build_cas_login_url,
    is_real_sso_enabled,
    validate_cas_ticket,
)
from models import (
    Notification,
    compute_stats,
    get_all_cubby_ids,
    suggest_emptiest_cubby,
)
from notifications import NotificationService
from storage import RackStore

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rak-it-pacil-ddp1-kelompok13-dev")

store = RackStore()
notifier = NotificationService(store)


def build_state_payload(user: dict | None) -> dict:
    """Assemble full frontend state JSON for the active session user."""
    if user and user.get("role") == "asdos":
        class_rosters = store.get_class_rosters(user.get("assignedClasses"))
    else:
        class_rosters = {}

    return {
        "user": user,
        "envelopes": store.envelopes,
        "quizzes": store.quizzes,
        "notifications": store.get_notifications_for_user(user),
        "classRosters": class_rosters,
        "suggestedCubby": suggest_emptiest_cubby(store.envelopes, store.quizzes),
        "stats": compute_stats(store.envelopes, store.quizzes),
        "realSsoEnabled": is_real_sso_enabled(),
    }


def _require_user() -> tuple[dict | None, tuple | None]:
    user = session.get("user")
    if not user:
        return None, (jsonify({"error": "Silakan login SSO UI terlebih dahulu."}), 401)
    return user, None


def _require_asdos() -> tuple[dict | None, tuple | None]:
    user, err = _require_user()
    if err:
        return None, err
    if user.get("role") != "asdos":
        return None, (jsonify({"error": "Hanya akun SSO Asdos yang dapat menaruh berkas ke rak."}), 403)
    return user, None


# ---------------------------------------------------------------------------
# Page Routes
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    """Render the main Rak-it! Pacil application shell."""
    return render_template(
        "index.html",
        initial_cubby=None,
        real_sso_enabled=is_real_sso_enabled(),
    )


@app.get("/slot/<cubby_id>")
def slot_page(cubby_id: str):
    """Deep link used by compartment QR stickers (e.g. /slot/C2)."""
    normalized = cubby_id.strip().upper()
    if normalized not in get_all_cubby_ids():
        return redirect(url_for("index"))

    return render_template(
        "index.html",
        initial_cubby=normalized,
        real_sso_enabled=is_real_sso_enabled(),
    )


# ---------------------------------------------------------------------------
# UI SSO (CAS 2.0) Routes
# ---------------------------------------------------------------------------
@app.get("/auth/sso/login")
def sso_login():
    """Redirect browser to sso.ui.ac.id/cas2/login for real UI SSO authentication."""
    callback_url = url_for("sso_callback", _external=True)
    return redirect(build_cas_login_url(callback_url))


@app.get("/auth/sso/callback")
def sso_callback():
    """Validate CAS ticket returned by sso.ui.ac.id and start Flask session."""
    ticket = request.args.get("ticket", "").strip()
    callback_url = url_for("sso_callback", _external=True)
    user = validate_cas_ticket(
        ticket,
        callback_url,
        all_class_ids=store.class_rosters.keys(),
    )
    if user:
        session["user"] = user
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# JSON REST API Routes
# ---------------------------------------------------------------------------
@app.get("/api/state")
def api_state():
    """Return current rack inventory, user session, rosters, and notifications."""
    return jsonify(build_state_payload(session.get("user")))


@app.post("/api/auth/login")
def api_auth_login():
    """Authenticate via local demo SSO account."""
    data = request.get_json(silent=True) or {}
    raw_username = str(data.get("username", "")).strip()
    user = authenticate_demo(raw_username, all_class_ids=store.class_rosters.keys())
    if not user:
        return jsonify({"error": "Username SSO UI wajib diisi."}), 400

    session["user"] = user
    return jsonify(build_state_payload(user))


@app.post("/api/auth/logout")
def api_auth_logout():
    """Clear current user session."""
    session.pop("user", None)
    return jsonify(build_state_payload(None))


@app.post("/api/envelopes")
def api_create_envelope():
    """Place a new envelope batch for checked students and dispatch notifications."""
    user, err = _require_asdos()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    class_id = str(data.get("classId", "")).strip()
    quiz_name = str(data.get("quizName", "")).strip()
    cubby = str(data.get("cubby", "")).strip().upper()
    folder_type = str(data.get("folderType", "Amplop Cokelat")).strip() or "Amplop Cokelat"
    selected_npms = data.get("selectedNpms") or []
    notify_enabled = bool(data.get("notifyEnabled", True))
    channels = data.get("channels") or ["Inbox Web"]

    if cubby not in get_all_cubby_ids():
        return jsonify({"error": f"Loker '{cubby}' tidak valid (pilih A1-C5)."}), 400
    if not quiz_name:
        return jsonify({"error": "Nama kuis / penilaian wajib diisi."}), 400

    try:
        envelope, created_quizzes, skipped_count, roster = store.create_envelope_batch(
            ta_user=user,
            class_id=class_id,
            quiz_name=quiz_name,
            cubby=cubby,
            folder_type=folder_type,
            selected_npms=selected_npms,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if notify_enabled:
        notif_items = [
            Notification(
                id=f"notif-{quiz['id'][2:]}",
                recipient_npm=quiz["npm"],
                recipient_name=quiz["studentName"],
                sender_name=user["name"],
                cubby=cubby,
                envelope_id=envelope["id"],
                quiz_id=quiz["id"],
                course=roster["course"],
                class_name=roster["className"],
                quiz_title=quiz_name,
                channels=list(channels) if channels else ["Inbox Web"],
                date_added=envelope["dateAdded"],
                read=False,
            ).to_dict()
            for quiz in created_quizzes
        ]
        notifier.dispatch(notif_items, channels)

    return jsonify(
        {
            "envelope": envelope,
            "addedCount": len(created_quizzes),
            "skippedCount": skipped_count,
            "state": build_state_payload(user),
        }
    ), 201


@app.post("/api/loose")
def api_create_loose():
    """Place a single loose quiz sheet and optionally notify the student."""
    user, err = _require_asdos()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    class_id = str(data.get("classId", "")).strip()
    selected_npm = str(data.get("selectedNpm", "")).strip()
    manual_name = str(data.get("manualName", "")).strip()
    manual_npm = str(data.get("manualNpm", "")).strip()
    quiz_title = str(data.get("quizTitle", "")).strip()
    cubby = str(data.get("cubby", "")).strip().upper()
    notify_enabled = bool(data.get("notifyEnabled", True))
    channels = data.get("channels") or ["Inbox Web", "Email @ui.ac.id"]

    if cubby not in get_all_cubby_ids():
        return jsonify({"error": f"Loker '{cubby}' tidak valid (pilih A1-C5)."}), 400
    if not quiz_title:
        return jsonify({"error": "Judul kuis wajib diisi."}), 400

    try:
        quiz, roster = store.create_loose_quiz(
            ta_user=user,
            class_id=class_id,
            selected_npm=selected_npm,
            manual_name=manual_name,
            manual_npm=manual_npm,
            quiz_title=quiz_title,
            cubby=cubby,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if notify_enabled:
        notif = Notification(
            id=f"notif-{quiz['id'][2:]}",
            recipient_npm=quiz["npm"],
            recipient_name=quiz["studentName"],
            sender_name=user["name"],
            cubby=cubby,
            envelope_id=None,
            quiz_id=quiz["id"],
            course=quiz["course"],
            class_name=roster["className"] if roster else "",
            quiz_title=quiz_title,
            channels=list(channels),
            date_added=quiz["dateAdded"],
            read=False,
        ).to_dict()
        notifier.dispatch([notif], channels)

    return jsonify({"quiz": quiz, "state": build_state_payload(user)}), 201


@app.post("/api/quizzes/<quiz_id>/pickup")
def api_pickup_quiz(quiz_id: str):
    """Record a student picking up a graded quiz sheet."""
    user, err = _require_user()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    verifier = str(data.get("verifier", "")).strip() or f"{user['npm']} ({user['name']})"

    updated = store.mark_quiz_picked_up(quiz_id, verifier)
    if not updated:
        return jsonify({"error": "Data kuis tidak ditemukan."}), 404

    return jsonify({"quiz": updated, "state": build_state_payload(user)})


@app.post("/api/notifications/<notif_id>/read")
def api_mark_notification_read(notif_id: str):
    """Mark one notification as read."""
    user, err = _require_user()
    if err:
        return err

    if not store.mark_notification_read(notif_id):
        return jsonify({"error": "Notifikasi tidak ditemukan."}), 404

    return jsonify({"state": build_state_payload(user)})


@app.post("/api/notifications/read-all")
def api_mark_all_notifications_read():
    """Mark all notifications addressed to the logged-in student as read."""
    user, err = _require_user()
    if err:
        return err

    store.mark_all_read_for_npm(user.get("npm", ""))
    return jsonify({"state": build_state_payload(user)})


@app.post("/api/reset")
def api_reset():
    """Reset the JSON store back to initial demo seed data."""
    store.reset()
    return jsonify({"state": build_state_payload(session.get("user"))})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
