"""Core domain models and rack placement helpers for Rak-it! Pacil (Member 1)."""

from __future__ import annotations

from dataclasses import dataclass, field

ROWS = ["A", "B", "C", "D", "E"]
COLUMNS = [1, 2, 3]


def get_all_cubby_ids() -> list[str]:
    """Return ordered compartment IDs for the 5x3 rack (A1-E3, rows A-E, cols 1-3)."""
    return [f"{row}{col}" for row in ROWS for col in COLUMNS]


@dataclass
class Student:
    """A student enrolled in a class roster."""

    npm: str
    name: str
    username: str

    def to_dict(self) -> dict:
        return {
            "npm": self.npm,
            "name": self.name,
            "username": self.username,
        }


@dataclass
class ClassRoster:
    """A course class section and its enrolled students (synced from SCELE/CSV)."""

    id: str
    course: str
    class_name: str
    label: str
    students: list[Student] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "course": self.course,
            "className": self.class_name,
            "label": self.label,
            "students": [student.to_dict() for student in self.students],
        }


@dataclass
class User:
    """Authenticated UI SSO / demo session user (TA or student)."""

    name: str
    npm: str
    username: str
    role: str
    title: str
    assigned_classes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "npm": self.npm,
            "username": self.username,
            "role": self.role,
            "title": self.title,
            "assignedClasses": list(self.assigned_classes),
        }


@dataclass
class Envelope:
    """A physical brown envelope or yellow folder placed in a rack compartment."""

    id: str
    cubby: str
    course: str
    label: str
    folder_type: str
    placed_by: str
    date_added: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cubby": self.cubby,
            "course": self.course,
            "label": self.label,
            "folderType": self.folder_type,
            "placedBy": self.placed_by,
            "dateAdded": self.date_added,
        }


@dataclass
class QuizRecord:
    """An individual student's graded quiz sheet (inside an envelope or loose)."""

    id: str
    envelope_id: str | None
    cubby: str
    student_name: str
    npm: str
    course: str
    quiz_title: str
    status: str
    date_added: str
    picked_up_by: str | None = None
    picked_up_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "envelopeId": self.envelope_id,
            "cubby": self.cubby,
            "studentName": self.student_name,
            "npm": self.npm,
            "course": self.course,
            "quizTitle": self.quiz_title,
            "status": self.status,
            "dateAdded": self.date_added,
            "pickedUpBy": self.picked_up_by,
            "pickedUpAt": self.picked_up_at,
        }


@dataclass
class Notification:
    """A pickup notification dispatched when a TA places marked papers on the rack."""

    id: str
    recipient_npm: str
    recipient_name: str
    sender_name: str
    cubby: str
    envelope_id: str | None
    quiz_id: str
    course: str
    class_name: str
    quiz_title: str
    channels: list[str]
    date_added: str
    read: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "recipientNpm": self.recipient_npm,
            "recipientName": self.recipient_name,
            "senderName": self.sender_name,
            "cubby": self.cubby,
            "envelopeId": self.envelope_id,
            "quizId": self.quiz_id,
            "course": self.course,
            "className": self.class_name,
            "quizTitle": self.quiz_title,
            "channels": list(self.channels),
            "dateAdded": self.date_added,
            "read": self.read,
        }


def suggest_emptiest_cubby(envelopes: list[dict], quizzes: list[dict]) -> str:
    """Recommend the least-crowded cubby ID (tie-breaking by row then column)."""
    cubby_ids = get_all_cubby_ids()
    counts = {cid: 0 for cid in cubby_ids}

    for env in envelopes:
        cid = env.get("cubby")
        if cid in counts:
            counts[cid] += 1

    for quiz in quizzes:
        if not quiz.get("envelopeId") and quiz.get("status") == "available":
            cid = quiz.get("cubby")
            if cid in counts:
                counts[cid] += 1

    return min(cubby_ids, key=lambda cid: counts[cid])


def compute_stats(envelopes: list[dict], quizzes: list[dict]) -> dict[str, int]:
    """Compute summary counters shown above the rack grid."""
    available_quizzes = [q for q in quizzes if q.get("status") == "available"]
    loose_quizzes = [q for q in available_quizzes if not q.get("envelopeId")]
    return {
        "envelopes": len(envelopes),
        "loose": len(loose_quizzes),
        "available": len(available_quizzes),
    }
