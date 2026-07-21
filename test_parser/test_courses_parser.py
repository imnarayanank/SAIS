import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils.excel_parser import parse_courses_excel

courses = parse_courses_excel(r"C:\Users\Admin\Desktop\LEARNABLE\backend\uploads\timetable_1.xlsx")
print(f"Total Unique Courses Parsed: {len(courses)}")
for c in sorted(courses, key=lambda x: x['course_code'] or ''):
    print(f"Code: {c['course_code']} | Name: {c['name']} | Teacher: {c['teacher']} | Type: {c['course_type']} | Credits: {c['credits']}")
