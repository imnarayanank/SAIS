import openpyxl
from typing import List, Dict, Any
import re

def parse_vtop_format(wb) -> List[Dict[str, Any]]:
    # 1. Parse Course Details to get mappings
    course_map = {} # course_code -> {name, teacher}
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        
        in_course_table = False
        course_col = -1
        faculty_col = -1
        
        for row in rows:
            if not in_course_table:
                # check for header
                row_strs = [str(c).strip().lower() for c in row if c is not None]
                if "course" in row_strs and "faculty details" in row_strs:
                    in_course_table = True
                    course_col = row_strs.index("course")
                    faculty_col = row_strs.index("faculty details")
            else:
                if not any(row): # empty row might mean end of table
                    break
                if course_col < len(row) and faculty_col < len(row):
                    course_cell = row[course_col]
                    faculty_cell = row[faculty_col]
                    
                    if course_cell and faculty_cell and " - " in str(course_cell):
                        parts = str(course_cell).split(" - ", 1)
                        code = parts[0].strip()
                        name = parts[1].strip()
                        
                        fac_parts = str(faculty_cell).split(" - ", 1)
                        teacher = fac_parts[0].strip()
                        
                        course_map[code] = {"name": name, "teacher": teacher}

    print("Course Map:", course_map)

    # 2. Parse Timetable Grid
    entries = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        
        theory_starts = []
        theory_ends = []
        lab_starts = []
        lab_ends = []
        
        grid_start_row = -1
        
        for i, row in enumerate(rows):
            # Check if this row is THEORY Start
            if row[0] == "THEORY" and row[1] == "Start":
                theory_starts = [str(x) for x in row[2:]]
                theory_ends = [str(x) for x in rows[i+1][2:]]
                lab_starts = [str(x) for x in rows[i+2][2:]]
                lab_ends = [str(x) for x in rows[i+3][2:]]
                grid_start_row = i + 4
                break
                
        if grid_start_row != -1:
            days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
            current_day = None
            
            for i in range(grid_start_row, len(rows)):
                row = rows[i]
                if not any(row):
                    continue
                    
                cell_0 = str(row[0]).strip().upper() if row[0] else ""
                cell_1 = str(row[1]).strip().upper() if row[1] else ""
                
                if cell_0 in days:
                    current_day = cell_0
                    
                row_type = None
                if cell_0 == "THEORY" or cell_1 == "THEORY":
                    row_type = "THEORY"
                elif cell_0 == "LAB" or cell_1 == "LAB":
                    row_type = "LAB"
                    
                if not row_type or not current_day:
                    continue
                    
                starts = theory_starts if row_type == "THEORY" else lab_starts
                ends = theory_ends if row_type == "THEORY" else lab_ends
                
                col_offset = 2
                
                for col_idx in range(col_offset, len(row)):
                    cell = row[col_idx]
                    if not cell or str(cell).strip() == "" or str(cell).strip() == "-":
                        continue
                        
                    cell_text = str(cell).strip()
                    # e.g. A1-BAPHY101-ETH-AB2-201-ALL03
                    # Sometimes just TG1 or L1 without details
                    if "-" in cell_text:
                        parts = cell_text.split("-")
                        slot = parts[0]
                        course_code = parts[1] if len(parts) > 1 else ""
                        venue = parts[3] + "-" + parts[4] if len(parts) > 4 else ""
                        
                        mapped = course_map.get(course_code, {})
                        subject_name = mapped.get("name", course_code)
                        teacher = mapped.get("teacher", "Unknown")
                        
                        time_idx = col_idx - col_offset
                        start_time = starts[time_idx] if time_idx < len(starts) else "00:00"
                        end_time = ends[time_idx] if time_idx < len(ends) else "00:00"
                        
                        # Only add if it's a valid time (not 'Lunch')
                        if start_time.lower() != "lunch":
                            entries.append({
                                "subject_name": subject_name,
                                "course_code": course_code,
                                "teacher": teacher,
                                "classroom": venue,
                                "day": current_day.capitalize() + "day" if current_day != "MON" else "Monday", # wait, simple title is enough, actually Monday, Tuesday...
                                "start_time": start_time,
                                "end_time": end_time
                            })
                            
    return entries

if __name__ == "__main__":
    pass
