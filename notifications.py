"""Pluggable OOP notification channels for Rak-it! Pacil (Member 3)."""

from __future__ import annotations

import json
import os
import smtplib
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from email.message import EmailMessage

from storage import RackStore


class Notifier(ABC):
    """Abstract base class for student notification delivery channels."""

    channel_name: str

    @abstractmethod
    def send(self, notification: dict) -> bool:
        """Deliver a single notification and return True if dispatched/logged."""


class WebInboxNotifier(Notifier):
    """Persists notifications to the in-app web inbox via RackStore."""

    channel_name = "Inbox Web"

    def __init__(self, store: RackStore) -> None:
        self.store = store

    def send(self, notification: dict) -> bool:
        self.store.add_notifications([notification])
        return True


class EmailNotifier(Notifier):
    """Sends @ui.ac.id email alerts via SMTP when configured, or simulates cleanly."""

    channel_name = "Email @ui.ac.id"

    def __init__(self) -> None:
        self.smtp_host = os.environ.get("SMTP_HOST", "").strip()
        self.smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = os.environ.get("SMTP_USER", "").strip()
        self.smtp_pass = os.environ.get("SMTP_PASS", "").strip()

    def _build_recipient_email(self, notification: dict) -> str:
        name_slug = ".".join(notification.get("recipientName", "").lower().split()[:2])
        return f"{name_slug}@ui.ac.id" if name_slug else f"{notification.get('recipientNpm', 'student')}@ui.ac.id"

    def send(self, notification: dict) -> bool:
        recipient_email = self._build_recipient_email(notification)
        subject = (
            f"[Rak-it! Pacil] Kuis {notification.get('course', '')} "
            f"sudah di Loker {notification.get('cubby', '')}"
        )
        body = (
            f"Halo {notification.get('recipientName', 'Mahasiswa')},\n\n"
            f"Kuis \"{notification.get('quizTitle', '')}\" ({notification.get('course', '')} "
            f"{notification.get('className', '')}) sudah dinilai dan ditaruh di "
            f"Loker {notification.get('cubby', '')} oleh {notification.get('senderName', 'Asdos')}.\n"
        )

        if not (self.smtp_host and self.smtp_user and self.smtp_pass):
            # Clean local simulation mode when SMTP credentials are not configured
            print(f"[EmailNotifier][SIMULATED] To={recipient_email} | Subject={subject}")
            return True

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = recipient_email
        msg.set_content(body)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            return True
        except OSError as exc:
            print(f"[EmailNotifier][ERROR] Failed sending to {recipient_email}: {exc}")
            return False


class WebhookNotifier(Notifier):
    """Posts alerts to a Discord/Telegram webhook URL when configured, or simulates."""

    channel_name = "Telegram/Discord"

    def __init__(self) -> None:
        self.webhook_url = os.environ.get("NOTIFY_WEBHOOK_URL", "").strip()

    def send(self, notification: dict) -> bool:
        message = (
            f"[Rak-it! Pacil] {notification.get('recipientName')} "
            f"({notification.get('recipientNpm')}): "
            f"{notification.get('course')} {notification.get('quizTitle')} "
            f"-> Loker {notification.get('cubby')}"
        )

        if not self.webhook_url:
            print(f"[WebhookNotifier][SIMULATED] {message}")
            return True

        payload = json.dumps({"content": message, "text": message}).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=8):
                return True
        except (urllib.error.URLError, OSError) as exc:
            print(f"[WebhookNotifier][ERROR] Webhook dispatch failed: {exc}")
            return False


class NotificationService:
    """Coordinates persistence and multi-channel dispatch for pickup notifications."""

    def __init__(self, store: RackStore) -> None:
        self.store = store
        self.web_notifier = WebInboxNotifier(store)
        self.channel_notifiers: dict[str, Notifier] = {
            "Email @ui.ac.id": EmailNotifier(),
            "Telegram/Discord": WebhookNotifier(),
            "Telegram / Discord": WebhookNotifier(),
        }

    def dispatch(self, notifications_list: list[dict], channels: list[str] | None = None) -> list[dict]:
        """Store web notifications in bulk and forward to any additional selected channels."""
        if not notifications_list:
            return []

        selected_channels = list(channels) if channels else ["Inbox Web"]
        # Always persist to in-app inbox (or when explicitly selected)
        if "Inbox Web" in selected_channels or not selected_channels:
            self.store.add_notifications(notifications_list)

        for notif in notifications_list:
            for ch in selected_channels:
                if ch == "Inbox Web":
                    continue
                notifier = self.channel_notifiers.get(ch)
                if notifier is not None:
                    notifier.send(notif)

        return notifications_list
