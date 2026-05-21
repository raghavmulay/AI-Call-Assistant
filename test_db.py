from backend.services.student_service import get_student_by_prn
from backend.services.attendance_service import get_student_attendance


prn = "12413749"


student = get_student_by_prn(prn)

print("\n===== STUDENT DETAILS =====")
print(student)


attendance = get_student_attendance(prn)

print("\n===== ATTENDANCE =====")

for row in attendance:
    print(row)