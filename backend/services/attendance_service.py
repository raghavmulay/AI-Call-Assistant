"""
attendance_service.py — Attendance data retrieval.

WHY THIS FILE EXISTS:
  Isolates all attendance-related DB queries in one place.
  AI handler for attendance queries calls these functions directly.
  No SQL leaks into the intent handler or response formatter.

HOW IT CONNECTS TO AI:
  When a student asks "What is my attendance?", the intent handler
  calls get_student_attendance(prn) using the PRN stored in session.
  The result is formatted into a short voice-friendly response.
"""

from backend.database.queries import fetch_all, fetch_one


def get_student_attendance(prn: str) -> list[dict]:
    """
    Fetches all subject-wise attendance for a student by PRN.

    Returns list of dicts with keys:
      subject, attendance_percent
    Returns empty list if PRN not found or no records.

    Usage:
      records = get_student_attendance("22070123")
      for r in records:
          print(r["subject"], r["attendance_percent"])
    """
    sql = """
        SELECT a.subject, a.attendance_percent
        FROM attendance a
        JOIN students s ON s.id = a.student_id
        WHERE s.prn = %s
        ORDER BY a.subject
    """
    return fetch_all(sql, (prn,))


def get_low_attendance(prn: str, threshold: float = 75.0) -> list[dict]:
    """
    Returns only subjects where attendance is below the threshold.
    Default threshold is 75% (standard college requirement).

    Useful for proactive alerts:
      "You have low attendance in 2 subjects."
    """
    records = get_student_attendance(prn)
    return [r for r in records if r["attendance_percent"] < threshold]
