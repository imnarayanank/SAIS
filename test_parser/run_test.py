import openpyxl
import os
import sys

# add parent dir so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils.excel_parser import parse_format_c, parse_timetable_excel

wb = openpyxl.load_workbook(r"C:\Users\Admin\Desktop\LEARNABLE\backend\uploads\timetable_1.xlsx", data_only=True)
c_entries = parse_format_c(wb)
print("Entries from Format C:")
print(len(c_entries))
for e in c_entries[:5]:
    print(e)
    
print("\nEntries from parse_timetable_excel:")
all_entries = parse_timetable_excel(r"C:\Users\Admin\Desktop\LEARNABLE\backend\uploads\timetable_1.xlsx")
print(len(all_entries))
for e in all_entries[:5]:
    print(e)
