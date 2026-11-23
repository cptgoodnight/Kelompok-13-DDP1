"""JSON persistence, SCELE class rosters, and rack CRUD queries for Rak-it! Pacil (Member 2)."""

from __future__ import annotations

import copy
import csv
import io
import json
import time
from datetime import datetime
from pathlib import Path

from models import ClassRoster, Envelope, QuizRecord, Student

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "store.json"

INITIAL_CLASS_ROSTERS: dict[str, dict] = {
    "ddp1-g": {
        "id": "ddp1-g",
        "course": "DDP 1",
        "className": "Kelas G",
        "label": "DDP 1 — Kelas G",
        "students": [
            {"npm": "2406351891", "name": "Alya Zahra Ramadhani", "username": "alya.zahra24"},
            {"npm": "2406351204", "name": "Muhammad Rafli Alfarizi", "username": "muhammad.rafli24"},
            {"npm": "2406351990", "name": "Kevin Wijaya Kusuma", "username": "kevin.wijaya24"},
            {"npm": "2406352011", "name": "Fadhil Rahman Hakim", "username": "fadhil.rahman24"},
            {"npm": "2406352088", "name": "Siti Nurhaliza Putri", "username": "siti.nurhaliza24"},
            {"npm": "2406351442", "name": "Bagas Kara Pratama", "username": "bagas.kara24"},
            {"npm": "2406357001", "name": "Syifa Aulia Rahma", "username": "syifa.aulia24"},
            {"npm": "2406357002", "name": "Bima Sakti Putra", "username": "bima.sakti24"},
        ],
    },
    "ddp2-c": {
        "id": "ddp2-c",
        "course": "DDP 2",
        "className": "Kelas C",
        "label": "DDP 2 — Kelas C",
        "students": [
            {"npm": "2406353112", "name": "Farhan Syahputra", "username": "farhan.syahputra24"},
            {"npm": "2406353199", "name": "Mutiara Salsabila", "username": "mutiara.salsabila24"},
            {"npm": "2406357003", "name": "Clarissa Jasmine Putri", "username": "clarissa.jasmine24"},
            {"npm": "2406357004", "name": "Muhammad Alif Ramadhan", "username": "muhammad.alif24"},
            {"npm": "2406354110", "name": "Raka Aditya Nugraha", "username": "raka.aditya24"},
            {"npm": "2406354221", "name": "Salsabila Khairunnisa", "username": "salsabila.k24"},
        ],
    },
    "sda-reg": {
        "id": "sda-reg",
        "course": "SDA",
        "className": "Kelas Reguler",
        "label": "SDA — Kelas Reguler",
        "students": [
            {"npm": "2306214812", "name": "Rizky Maulana Akbar", "username": "rizky.maulana23"},
            {"npm": "2306215110", "name": "Clarissa Aurelia Wijaya", "username": "clarissa.aurelia23"},
            {"npm": "2306215334", "name": "Daniel Sebastian Lim", "username": "daniel.sebastian23"},
            {"npm": "2306214901", "name": "Anisa Fitriani", "username": "anisa.fitriani23"},
            {"npm": "2306214777", "name": "Hendra Gunawan", "username": "hendra.gunawan23"},
            {"npm": "2306217102", "name": "Andika Pratama", "username": "andika.pratama23"},
        ],
    },
    "basdat-a": {
        "id": "basdat-a",
        "course": "Basdat",
        "className": "Kelas A",
        "label": "Basdat — Kelas A",
        "students": [
            {"npm": "2306216001", "name": "Galih Permana", "username": "galih.permana23"},
            {"npm": "2306216044", "name": "Tiara Andini Putri", "username": "tiara.andini23"},
            {"npm": "2306216123", "name": "Shafira Azzahra", "username": "shafira.azzahra23"},
            {"npm": "2306218105", "name": "Reyhan Zulfikar", "username": "reyhan.zulfikar23"},
            {"npm": "2306218502", "name": "Naufal Hakim", "username": "naufal.hakim23"},
        ],
    },
    "os-a": {
        "id": "os-a",
        "course": "OS",
        "className": "Kelas A",
        "label": "OS — Kelas A",
        "students": [
            {"npm": "2206081234", "name": "Daffa Alifiansyah", "username": "daffa.alif22"},
            {"npm": "2206081567", "name": "Putri Amalia Kartika", "username": "putri.amalia22"},
            {"npm": "2206081902", "name": "Bagas Prakoso", "username": "bagas.prakoso22"},
            {"npm": "2206082115", "name": "Rania Salsabila", "username": "rania.salsabila22"},
        ],
    },
    "jarkom-a": {
        "id": "jarkom-a",
        "course": "Jarkom",
        "className": "Kelas A",
        "label": "Jarkom — Kelas A",
        "students": [
            {"npm": "2206081902", "name": "Bagas Prakoso", "username": "bagas.prakoso22"},
            {"npm": "2206081234", "name": "Daffa Alifiansyah", "username": "daffa.alif22"},
            {"npm": "2206082301", "name": "Fajar Nugroho", "username": "fajar.nugroho22"},
            {"npm": "2206082450", "name": "Nadine Larasati", "username": "nadine.larasati22"},
        ],
    },
}

INITIAL_ENVELOPES: list[dict] = [
    {"id": "env-a1-1", "cubby": "A1", "course": "DDP 1", "label": "Amplop Cokelat - DDP 1 Kelas A (Kuis 1)", "folderType": "Amplop Cokelat", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "20 Nov, 14:20"},
    {"id": "env-a1-2", "cubby": "A1", "course": "DDP 1", "label": "Amplop Cokelat - DDP 1 Kelas B (Kuis 2)", "folderType": "Amplop Cokelat", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "21 Nov, 09:10"},
    {"id": "env-b1-1", "cubby": "B1", "course": "SDA", "label": "Amplop Cokelat - SDA Reguler (Kuis 1 AVL)", "folderType": "Amplop Cokelat Besar", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "19 Nov, 11:40"},
    {"id": "env-b1-2", "cubby": "B1", "course": "SDA", "label": "Amplop Cokelat - SDA KKI (Kuis 2 Graph)", "folderType": "Amplop Cokelat", "placedBy": "Nadia Khairunnisa (Asdos)", "dateAdded": "20 Nov, 16:00"},
    {"id": "env-b1-3", "cubby": "B1", "course": "SDA", "label": "Amplop Cokelat - SDA Susulan", "folderType": "Amplop Cokelat", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "21 Nov, 08:15"},
    {"id": "env-c1-1", "cubby": "C1", "course": "OS", "label": "Amplop Cokelat - Sistem Operasi (Kuis 2)", "folderType": "Amplop Cokelat", "placedBy": "Nadia Khairunnisa (Asdos)", "dateAdded": "21 Nov, 10:10"},
    {"id": "env-c1-2", "cubby": "C1", "course": "Jarkom", "label": "Amplop Cokelat - Jarkom Kelas A", "folderType": "Amplop Cokelat", "placedBy": "Nadia Khairunnisa (Asdos)", "dateAdded": "21 Nov, 10:30"},
    {"id": "env-a2-1", "cubby": "A2", "course": "DDP 2", "label": "Map Kuning - DDP 2 Kelas C (Kuis 1)", "folderType": "Map Kuning", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "20 Nov, 13:00"},
    {"id": "env-b2-1", "cubby": "B2", "course": "Basdat", "label": "Amplop Cokelat - Basdat (ERD & SQL)", "folderType": "Amplop Cokelat", "placedBy": "Nadia Khairunnisa (Asdos)", "dateAdded": "20 Nov, 15:30"},
    {"id": "env-c2-1", "cubby": "C2", "course": "TBA", "label": "Amplop Cokelat - TBA (DFA & NFA)", "folderType": "Amplop Cokelat", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "21 Nov, 08:45"},
    {"id": "env-a3-1", "cubby": "A3", "course": "Kalkulus 1", "label": "Amplop Cokelat - Kalkulus 1 Kelas B", "folderType": "Amplop Cokelat Besar", "placedBy": "Asdos Kalkulus", "dateAdded": "20 Nov, 09:15"},
    {"id": "env-b3-1", "cubby": "B3", "course": "Matdis 1", "label": "Amplop Cokelat - Matdis 1 (Logika)", "folderType": "Amplop Cokelat", "placedBy": "Asdos Matdis", "dateAdded": "19 Nov, 16:20"},
    {"id": "env-c3-1", "cubby": "C3", "course": "Alin", "label": "Amplop Cokelat - Aljabar Linear", "folderType": "Amplop Cokelat", "placedBy": "Asdos Alin", "dateAdded": "21 Nov, 08:30"},
    {"id": "env-b4-1", "cubby": "B4", "course": "Adpro", "label": "Amplop Cokelat - Pemrograman Lanjut", "folderType": "Amplop Cokelat", "placedBy": "Asdos Adpro", "dateAdded": "20 Nov, 11:00"},
    {"id": "env-c4-1", "cubby": "C4", "course": "Susulan", "label": "Amplop Cokelat - Lab & Susulan Gabungan", "folderType": "Amplop Cokelat", "placedBy": "Tim Asdos", "dateAdded": "21 Nov, 12:15"},
    {"id": "env-a5-1", "cubby": "A5", "course": "DDP 1", "label": "Amplop Cokelat - Arsip Kuis Awal Semester", "folderType": "Amplop Cokelat Besar", "placedBy": "Jonathan Tan (Asdos)", "dateAdded": "15 Nov, 09:00"},
    {"id": "env-c5-1", "cubby": "C5", "course": "Kalkulus 1", "label": "Map Kuning - Kalkulus Kelas A", "folderType": "Map Kuning", "placedBy": "Asdos Kalkulus", "dateAdded": "18 Nov, 14:00"},
]

INITIAL_QUIZZES: list[dict] = [
    # Inside Envelope env-a1-1 (DDP 1 Kelas A)
    {"id": "q-101", "envelopeId": "env-a1-1", "cubby": "A1", "studentName": "Alya Zahra Ramadhani", "npm": "2406351891", "course": "DDP 1", "quizTitle": "Kuis 1 - Percabangan & Loop", "status": "available", "dateAdded": "20 Nov, 14:20", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-102", "envelopeId": "env-a1-1", "cubby": "A1", "studentName": "Muhammad Rafli Alfarizi", "npm": "2406351204", "course": "DDP 1", "quizTitle": "Kuis 1 - Percabangan & Loop", "status": "available", "dateAdded": "20 Nov, 14:20", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-103", "envelopeId": "env-a1-1", "cubby": "A1", "studentName": "Kevin Wijaya Kusuma", "npm": "2406351990", "course": "DDP 1", "quizTitle": "Kuis 1 - Percabangan & Loop", "status": "picked_up", "dateAdded": "20 Nov, 14:20", "pickedUpBy": "Kevin (2406351990)", "pickedUpAt": "21 Nov, 09:30"},
    # Inside Envelope env-a1-2 (DDP 1 Kelas B)
    {"id": "q-104", "envelopeId": "env-a1-2", "cubby": "A1", "studentName": "Fadhil Rahman Hakim", "npm": "2406352011", "course": "DDP 1", "quizTitle": "Kuis 2 - List & String", "status": "available", "dateAdded": "21 Nov, 09:10", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-105", "envelopeId": "env-a1-2", "cubby": "A1", "studentName": "Siti Nurhaliza Putri", "npm": "2406352088", "course": "DDP 1", "quizTitle": "Kuis 2 - List & String", "status": "available", "dateAdded": "21 Nov, 09:10", "pickedUpBy": None, "pickedUpAt": None},
    # Loose Paper in A1
    {"id": "q-106", "envelopeId": None, "cubby": "A1", "studentName": "Bagas Kara Pratama", "npm": "2406351442", "course": "DDP 1", "quizTitle": "Kuis 1 (Amplop Sobek)", "status": "available", "dateAdded": "20 Nov, 15:00", "pickedUpBy": None, "pickedUpAt": None},
    # Inside Envelope env-b1-1, env-b1-2, env-b1-3 (SDA in B1)
    {"id": "q-201", "envelopeId": "env-b1-1", "cubby": "B1", "studentName": "Jonathan Christopher Tan", "npm": "2306214509", "course": "SDA", "quizTitle": "Kuis 1 - AVL Tree & Heap", "status": "available", "dateAdded": "19 Nov, 11:40", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-202", "envelopeId": "env-b1-1", "cubby": "B1", "studentName": "Nadia Khairunnisa", "npm": "2306215567", "course": "SDA", "quizTitle": "Kuis 1 - AVL Tree & Heap", "status": "available", "dateAdded": "19 Nov, 11:40", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-203", "envelopeId": "env-b1-1", "cubby": "B1", "studentName": "Rizky Maulana Akbar", "npm": "2306214812", "course": "SDA", "quizTitle": "Kuis 1 - AVL Tree & Heap", "status": "available", "dateAdded": "19 Nov, 11:40", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-204", "envelopeId": "env-b1-2", "cubby": "B1", "studentName": "Clarissa Aurelia Wijaya", "npm": "2306215110", "course": "SDA", "quizTitle": "Kuis 2 - Shortest Path", "status": "available", "dateAdded": "20 Nov, 16:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-205", "envelopeId": "env-b1-2", "cubby": "B1", "studentName": "Daniel Sebastian Lim", "npm": "2306215334", "course": "SDA", "quizTitle": "Kuis 2 - Shortest Path", "status": "available", "dateAdded": "20 Nov, 16:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-206", "envelopeId": "env-b1-3", "cubby": "B1", "studentName": "Anisa Fitriani", "npm": "2306214901", "course": "SDA", "quizTitle": "Kuis Susulan SDA", "status": "available", "dateAdded": "21 Nov, 08:15", "pickedUpBy": None, "pickedUpAt": None},
    # Loose Paper in B1
    {"id": "q-207", "envelopeId": None, "cubby": "B1", "studentName": "Hendra Gunawan", "npm": "2306214777", "course": "SDA", "quizTitle": "Kuis 1 - Lembar Lepas", "status": "available", "dateAdded": "20 Nov, 10:15", "pickedUpBy": None, "pickedUpAt": None},
    # C1 (OS & Jarkom)
    {"id": "q-301", "envelopeId": "env-c1-1", "cubby": "C1", "studentName": "Daffa Alifiansyah", "npm": "2206081234", "course": "OS", "quizTitle": "Kuis 2 - Deadlock & Memory", "status": "available", "dateAdded": "21 Nov, 10:10", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-302", "envelopeId": "env-c1-1", "cubby": "C1", "studentName": "Putri Amalia Kartika", "npm": "2206081567", "course": "OS", "quizTitle": "Kuis 2 - Deadlock & Memory", "status": "available", "dateAdded": "21 Nov, 10:10", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-303", "envelopeId": "env-c1-2", "cubby": "C1", "studentName": "Bagas Prakoso", "npm": "2206081902", "course": "Jarkom", "quizTitle": "Kuis 1 - TCP/IP & Subnetting", "status": "available", "dateAdded": "21 Nov, 10:30", "pickedUpBy": None, "pickedUpAt": None},
    # A2 (DDP 2)
    {"id": "q-401", "envelopeId": "env-a2-1", "cubby": "A2", "studentName": "Farhan Syahputra", "npm": "2406353112", "course": "DDP 2", "quizTitle": "Kuis 1 - OOP & Inheritance", "status": "available", "dateAdded": "20 Nov, 13:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-402", "envelopeId": "env-a2-1", "cubby": "A2", "studentName": "Mutiara Salsabila", "npm": "2406353199", "course": "DDP 2", "quizTitle": "Kuis 1 - OOP & Inheritance", "status": "available", "dateAdded": "20 Nov, 13:00", "pickedUpBy": None, "pickedUpAt": None},
    # B2 (Loose papers stack + Basdat envelope)
    {"id": "q-501", "envelopeId": None, "cubby": "B2", "studentName": "Galih Permana", "npm": "2306216001", "course": "Basdat", "quizTitle": "Kuis 1 - Lembar Lepas", "status": "available", "dateAdded": "19 Nov, 14:10", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-502", "envelopeId": None, "cubby": "B2", "studentName": "Tiara Andini Putri", "npm": "2306216044", "course": "Basdat", "quizTitle": "Kuis 1 - Lembar Lepas", "status": "available", "dateAdded": "19 Nov, 14:10", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-503", "envelopeId": "env-b2-1", "cubby": "B2", "studentName": "Shafira Azzahra", "npm": "2306216123", "course": "Basdat", "quizTitle": "Kuis 2 - Relational Algebra", "status": "available", "dateAdded": "20 Nov, 15:30", "pickedUpBy": None, "pickedUpAt": None},
    # C2 (TBA)
    {"id": "q-601", "envelopeId": "env-c2-1", "cubby": "C2", "studentName": "Andika Pratama", "npm": "2306217102", "course": "TBA", "quizTitle": "Kuis 1 - Regular Expression", "status": "available", "dateAdded": "21 Nov, 08:45", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-602", "envelopeId": "env-c2-1", "cubby": "C2", "studentName": "Vina Panduwinata", "npm": "2306217188", "course": "TBA", "quizTitle": "Kuis 1 - Regular Expression", "status": "available", "dateAdded": "21 Nov, 08:45", "pickedUpBy": None, "pickedUpAt": None},
    # Row 3 (A3, B3, C3)
    {"id": "q-701", "envelopeId": "env-a3-1", "cubby": "A3", "studentName": "Raka Aditya Nugraha", "npm": "2406354110", "course": "Kalkulus 1", "quizTitle": "Kuis 2 - Turunan & Limit", "status": "available", "dateAdded": "20 Nov, 09:15", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-702", "envelopeId": "env-b3-1", "cubby": "B3", "studentName": "Salsabila Khairunnisa", "npm": "2406354221", "course": "Matdis 1", "quizTitle": "Kuis 1 - Induksi Matematika", "status": "available", "dateAdded": "19 Nov, 16:20", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-703", "envelopeId": "env-c3-1", "cubby": "C3", "studentName": "Reyhan Zulfikar", "npm": "2306218105", "course": "Alin", "quizTitle": "Kuis 1 - Determinan & Matriks", "status": "available", "dateAdded": "21 Nov, 08:30", "pickedUpBy": None, "pickedUpAt": None},
    # Row 4 (A4 loose papers only, B4, C4)
    {"id": "q-801", "envelopeId": None, "cubby": "A4", "studentName": "Ilham Saputra", "npm": "2406355101", "course": "Statprob", "quizTitle": "Kuis 1 - Kertas Lepas", "status": "available", "dateAdded": "20 Nov, 10:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-802", "envelopeId": "env-b4-1", "cubby": "B4", "studentName": "Naufal Hakim", "npm": "2306218502", "course": "Adpro", "quizTitle": "Kuis 1 - Concurrency", "status": "available", "dateAdded": "20 Nov, 11:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-803", "envelopeId": "env-c4-1", "cubby": "C4", "studentName": "Citra Kirana Dewi", "npm": "2306218990", "course": "Susulan", "quizTitle": "Kuis Susulan Lab", "status": "available", "dateAdded": "21 Nov, 12:15", "pickedUpBy": None, "pickedUpAt": None},
    # Row 5 (A5, C5)
    {"id": "q-901", "envelopeId": "env-a5-1", "cubby": "A5", "studentName": "Bintang Ramadhan", "npm": "2406350012", "course": "DDP 1", "quizTitle": "Kuis 0 - Pengenalan Python", "status": "available", "dateAdded": "15 Nov, 09:00", "pickedUpBy": None, "pickedUpAt": None},
    {"id": "q-902", "envelopeId": "env-c5-1", "cubby": "C5", "studentName": "Larasati Ayuningtyas", "npm": "2406350099", "course": "Kalkulus 1", "quizTitle": "Kuis 1 - Fungsi & Grafik", "status": "available", "dateAdded": "18 Nov, 14:00", "pickedUpBy": None, "pickedUpAt": None},
]

INITIAL_NOTIFICATIONS: list[dict] = [
    {
        "id": "notif-init-1",
        "recipientNpm": "2406351891",
        "recipientName": "Alya Zahra Ramadhani",
        "senderName": "Jonathan Christopher Tan",
        "cubby": "A1",
        "envelopeId": "env-a1-1",
        "quizId": "q-101",
        "course": "DDP 1",
        "className": "Kelas A",
        "quizTitle": "Kuis 1 - Percabangan & Loop",
        "channels": ["Inbox Web", "Email @ui.ac.id"],
        "dateAdded": "20 Nov, 14:20",
        "read": False,
    }
]


def _format_now() -> str:
    return f"Hari ini, {datetime.now().strftime('%H:%M')}"


class RackStore:
    """File-backed JSON store managing envelopes, quiz sheets, rosters, and notifications."""

    def __init__(self, file_path: Path = DATA_FILE) -> None:
        self.file_path = Path(file_path)
        self.envelopes: list[dict] = []
        self.quizzes: list[dict] = []
        self.notifications: list[dict] = []
        self.class_rosters: dict[str, dict] = copy.deepcopy(INITIAL_CLASS_ROSTERS)
        self.load()

    def load(self) -> None:
        """Load state from JSON file or seed initial demo data on first run."""
        if self.file_path.exists():
            try:
                data = json.loads(self.file_path.read_text(encoding="utf-8"))
                self.envelopes = data.get("envelopes", copy.deepcopy(INITIAL_ENVELOPES))
                self.quizzes = data.get("quizzes", copy.deepcopy(INITIAL_QUIZZES))
                self.notifications = data.get("notifications", copy.deepcopy(INITIAL_NOTIFICATIONS))
                self.class_rosters = data.get("classRosters", copy.deepcopy(INITIAL_CLASS_ROSTERS))
                return
            except (json.JSONDecodeError, OSError):
                pass

        self.reset()

    def save(self) -> None:
        """Persist current store state to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "envelopes": self.envelopes,
            "quizzes": self.quizzes,
            "notifications": self.notifications,
            "classRosters": self.class_rosters,
        }
        self.file_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def reset(self) -> None:
        """Restore initial demo data and write it to disk."""
        self.envelopes = copy.deepcopy(INITIAL_ENVELOPES)
        self.quizzes = copy.deepcopy(INITIAL_QUIZZES)
        self.notifications = copy.deepcopy(INITIAL_NOTIFICATIONS)
        self.class_rosters = copy.deepcopy(INITIAL_CLASS_ROSTERS)
        self.save()

    def get_class_rosters(self, assigned_ids: list[str] | None = None) -> dict[str, dict]:
        """Return rosters filtered to a TA's assigned class IDs (or all if omitted)."""
        if not assigned_ids:
            return copy.deepcopy(self.class_rosters)
        return {
            cid: copy.deepcopy(self.class_rosters[cid])
            for cid in assigned_ids
            if cid in self.class_rosters
        }

    def create_envelope_batch(
        self,
        ta_user: dict,
        class_id: str,
        quiz_name: str,
        cubby: str,
        folder_type: str,
        selected_npms: list[str],
    ) -> tuple[dict, list[dict], int, dict]:
        """Create an envelope and quiz records only for checked students in the class."""
        roster = self.class_rosters.get(class_id)
        if not roster:
            raise ValueError(f"Kelas '{class_id}' tidak ditemukan.")

        selected_set = {str(npm).strip() for npm in selected_npms}
        checked_students = [s for s in roster["students"] if s["npm"] in selected_set]
        if not checked_students:
            raise ValueError("Pilih minimal 1 mahasiswa yang kuisnya sudah dinilai.")

        timestamp = _format_now()
        base_ms = int(time.time() * 1000)
        new_env_id = f"env-{base_ms}"
        full_label = f"{folder_type} - {roster['course']} {roster['className']} ({quiz_name})"

        envelope = Envelope(
            id=new_env_id,
            cubby=cubby,
            course=roster["course"],
            label=full_label,
            folder_type=folder_type,
            placed_by=f"{ta_user['name']} (Asdos)",
            date_added=timestamp,
        ).to_dict()

        created_quizzes: list[dict] = []
        for idx, student in enumerate(checked_students):
            quiz = QuizRecord(
                id=f"q-{base_ms}-{idx}",
                envelope_id=new_env_id,
                cubby=cubby,
                student_name=student["name"],
                npm=student["npm"],
                course=roster["course"],
                quiz_title=f"{quiz_name} ({roster['className']})",
                status="available",
                date_added=timestamp,
            ).to_dict()
            created_quizzes.append(quiz)

        # Preserve newest-first ordering from the frontend mockup
        for quiz in reversed(created_quizzes):
            self.quizzes.insert(0, quiz)
        self.envelopes.insert(0, envelope)
        self.save()

        skipped_count = len(roster["students"]) - len(checked_students)
        return envelope, created_quizzes, skipped_count, roster

    def create_loose_quiz(
        self,
        ta_user: dict,
        class_id: str,
        selected_npm: str,
        manual_name: str,
        manual_npm: str,
        quiz_title: str,
        cubby: str,
    ) -> tuple[dict, dict | None]:
        """Create a single loose quiz sheet (outside an envelope)."""
        roster = self.class_rosters.get(class_id)

        if selected_npm == "__manual__":
            student_name = manual_name.strip()
            student_npm = manual_npm.strip()
        elif roster:
            found = next((s for s in roster["students"] if s["npm"] == selected_npm), None)
            if not found:
                raise ValueError("Mahasiswa tidak ditemukan pada daftar kelas.")
            student_name = found["name"]
            student_npm = found["npm"]
        else:
            raise ValueError("Kelas atau mahasiswa belum dipilih.")

        if not student_name or not student_npm:
            raise ValueError("Nama dan NPM mahasiswa wajib diisi.")

        course = roster["course"] if roster else "Umum"
        timestamp = _format_now()
        base_ms = int(time.time() * 1000)

        quiz = QuizRecord(
            id=f"q-{base_ms}",
            envelope_id=None,
            cubby=cubby,
            student_name=student_name,
            npm=student_npm,
            course=course,
            quiz_title=f"{quiz_title} (Ditaruh {ta_user['name']})",
            status="available",
            date_added=timestamp,
        ).to_dict()

        self.quizzes.insert(0, quiz)
        self.save()
        return quiz, roster

    def mark_quiz_picked_up(self, quiz_id: str, verifier: str) -> dict | None:
        """Mark a quiz as picked up and clear any unread notification pointing to it."""
        target = next((q for q in self.quizzes if q["id"] == quiz_id), None)
        if not target:
            return None

        target["status"] = "picked_up"
        target["pickedUpBy"] = verifier.strip()
        target["pickedUpAt"] = _format_now()

        for notif in self.notifications:
            if notif.get("quizId") == quiz_id:
                notif["read"] = True

        self.save()
        return target

    def add_notifications(self, items: list[dict]) -> None:
        """Prepend new notifications and persist."""
        if not items:
            return
        for item in reversed(items):
            self.notifications.insert(0, item)
        self.save()

    def get_notifications_for_user(self, user: dict | None) -> list[dict]:
        """Return notifications visible to the current user (sent by TA or addressed to student)."""
        if not user:
            return []
        if user.get("role") == "asdos":
            return [n for n in self.notifications if n.get("senderName") == user.get("name")]
        return [n for n in self.notifications if n.get("recipientNpm") == user.get("npm")]

    def mark_notification_read(self, notif_id: str) -> bool:
        """Mark a single notification as read."""
        target = next((n for n in self.notifications if n["id"] == notif_id), None)
        if not target:
            return False
        target["read"] = True
        self.save()
        return True

    def mark_all_read_for_npm(self, npm: str) -> int:
        """Mark all notifications for a student NPM as read."""
        changed = 0
        for notif in self.notifications:
            if notif.get("recipientNpm") == npm and not notif.get("read"):
                notif["read"] = True
                changed += 1
        if changed:
            self.save()
        return changed

    def import_roster_from_csv(
        self,
        csv_text: str,
        class_id: str,
        course: str,
        class_name: str,
    ) -> dict:
        """Parse an exported SCELE/EMAS CSV roster and register/update a class."""
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        students: list[dict] = []

        for row in reader:
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            npm = (
                normalized.get("npm")
                or normalized.get("id number")
                or normalized.get("nim")
                or ""
            )
            name = (
                normalized.get("name")
                or normalized.get("nama")
                or normalized.get("full name")
                or " ".join(
                    p for p in [normalized.get("first name", ""), normalized.get("last name", "")] if p
                ).strip()
            )
            username = normalized.get("username") or (
                normalized.get("email address", "").split("@")[0]
            )
            if not username and name:
                username = ".".join(name.lower().split()[:2])

            if npm and name:
                students.append(Student(npm=npm, name=name, username=username).to_dict())

        roster = ClassRoster(
            id=class_id,
            course=course,
            class_name=class_name,
            label=f"{course} — {class_name}",
            students=[Student(**s) for s in students],
        ).to_dict()
        self.class_rosters[class_id] = roster
        self.save()
        return roster
