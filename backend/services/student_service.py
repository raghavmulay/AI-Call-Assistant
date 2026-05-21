"""
student_service.py — Student data retrieval.

WHY THIS FILE EXISTS:
  Separates student-related DB logic from query mechanics.
  AI handlers (e.g. session memory, PRN lookup) call these functions
  directly without knowing anything about SQL or DB connections.
  When you add more student queries later (by name, by branch, etc.),
  they all go here — one place, easy to maintain.

HOW IT CONNECTS TO AI:
  When a student says their PRN, intent_handler calls get_student_by_prn()
  and stores the result in session memory for personalized responses.
"""

from backend.database.queries import fetch_one


def get_student_by_prn(prn: str) -> dict | None:
    """
    Fetches a single student record by PRN.

    Returns dict with keys:
      id, prn, name, email, branch, year, division, cgpa, role, created_at
    Returns None if PRN not found.

    Usage:
      student = get_student_by_prn("22070123")
      if student:
          print(student["name"], student["branch"])
    """
    sql = """
        SELECT id, prn, name, email, branch, year, division, cgpa, role, created_at
        FROM students
        WHERE prn = %s
        LIMIT 1
    """
    return fetch_one(sql, (prn,))


def get_students_by_branch(branch: str) -> list[dict]:
    """
    Fetches all students in a given branch.
    Useful for admin queries or batch operations.
    """
    from backend.database.queries import fetch_all
    sql = """
        SELECT id, prn, name, branch, year, division, cgpa
        FROM students
        WHERE LOWER(branch) = LOWER(%s)
        ORDER BY name
    """
    return fetch_all(sql, (branch,))
