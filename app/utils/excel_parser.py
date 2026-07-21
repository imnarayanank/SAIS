"""
app/utils/excel_parser.py
--------------------------
Parses a college timetable Excel file (.xlsx) into structured data.

Supported formats:
  Format A: Row-per-class style (subject, code, teacher, classroom, day, start, end)
  Format B: Weekly grid style (days as columns, periods as rows)

The parser tries Format A first (explicit columns), then falls back to Format B.
"""
import openpyxl
from typing import List, Dict, Any, Optional
import re


# Common column name variations for Format A
COLUMN_ALIASES = {
    "subject_name": ["subject", "subject name", "course name", "name", "course"],
    "course_code": ["code", "course code", "subject code", "course_code"],
    "teacher": ["teacher", "faculty", "lecturer", "instructor", "professor"],
    "classroom": ["room", "classroom", "venue", "hall", "lab"],
    "day": ["day", "weekday", "days"],
    "start_time": ["start", "start time", "from", "begin", "time from", "start_time"],
    "end_time": ["end", "end time", "to", "till", "time to", "end_time"],
}

DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def normalize_time(value: Any) -> Optional[str]:
    """Convert various time formats to HH:MM string."""
    if value is None:
        return None
    s = str(value).strip()
    # Already HH:MM
    if re.match(r"^\d{1,2}:\d{2}$", s):
        parts = s.split(":")
        return f"{int(parts[0]):02d}:{parts[1]}"
    # HH:MM:SS
    if re.match(r"^\d{1,2}:\d{2}:\d{2}$", s):
        parts = s.split(":")
        return f"{int(parts[0]):02d}:{parts[1]}"
    # Decimal hours (e.g., 9.5 → 09:30)
    try:
        decimal = float(s)
        hours = int(decimal)
        minutes = int(round((decimal - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"
    except ValueError:
        pass
    return s


def normalize_day(value: Any) -> Optional[str]:
    """Normalize day names."""
    if not value:
        return None
    s = str(value).strip().lower()
    day_map = {
        "mon": "Monday", "tue": "Tuesday", "wed": "Wednesday",
        "thu": "Thursday", "fri": "Friday", "sat": "Saturday", "sun": "Sunday",
        "monday": "Monday", "tuesday": "Tuesday", "wednesday": "Wednesday",
        "thursday": "Thursday", "friday": "Friday", "saturday": "Saturday", "sunday": "Sunday",
    }
    for key, full in day_map.items():
        if s.startswith(key):
            return full
    return str(value).strip().title()


def find_column(headers: List[str], field: str) -> Optional[int]:
    """Find the column index for a field by checking aliases."""
    aliases = COLUMN_ALIASES.get(field, [field])
    for i, header in enumerate(headers):
        if header.strip().lower() in aliases:
            return i
    return None


def parse_format_a(ws) -> List[Dict[str, Any]]:
    """
    Format A: Each row is a class entry.
    First row must be headers.
    """
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Find header row (first non-empty row)
    header_row_idx = 0
    for i, row in enumerate(rows):
        if any(cell for cell in row if cell is not None):
            header_row_idx = i
            break

    headers = [str(cell).strip().lower() if cell else "" for cell in rows[header_row_idx]]

    # Map fields to column indices
    col_map = {}
    for field in COLUMN_ALIASES:
        idx = find_column(headers, field)
        if idx is not None:
            col_map[field] = idx

    # We need at least subject+day+time to proceed
    if "subject_name" not in col_map or "day" not in col_map:
        return []

    entries = []
    for row in rows[header_row_idx + 1:]:
        if not any(cell for cell in row if cell is not None):
            continue

        def get(field):
            idx = col_map.get(field)
            if idx is not None and idx < len(row):
                return row[idx]
            return None

        subject = get("subject_name")
        day = get("day")
        if not subject or not day:
            continue

        entries.append({
            "subject_name": str(subject).strip(),
            "course_code": str(get("course_code")).strip() if get("course_code") else None,
            "teacher": str(get("teacher")).strip() if get("teacher") else None,
            "classroom": str(get("classroom")).strip() if get("classroom") else None,
            "day": normalize_day(day),
            "start_time": normalize_time(get("start_time")) or "08:00",
            "end_time": normalize_time(get("end_time")) or "09:00",
        })

    return entries


def parse_format_b(ws) -> List[Dict[str, Any]]:
    """
    Format B: Weekly grid.
    Columns = days, rows = time slots.
    Detects days in the header row.
    """
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # Find header row with day names
    header_row_idx = None
    day_columns = {}
    for i, row in enumerate(rows[:10]):
        for j, cell in enumerate(row):
            if cell and str(cell).strip().lower() in [d[:3].lower() for d in DAYS_OF_WEEK] + DAYS_OF_WEEK:
                day_columns[j] = normalize_day(str(cell).strip())
        if day_columns:
            header_row_idx = i
            break

    if header_row_idx is None:
        return []

    entries = []
    for row in rows[header_row_idx + 1:]:
        if not any(row):
            continue
        # First cell might be time
        time_cell = row[0]
        start_time = normalize_time(time_cell) if time_cell else "08:00"

        for col_idx, day in day_columns.items():
            if col_idx < len(row) and row[col_idx]:
                cell_text = str(row[col_idx]).strip()
                if cell_text:
                    lines = cell_text.split("\n")
                    entries.append({
                        "subject_name": lines[0].strip(),
                        "course_code": lines[1].strip() if len(lines) > 1 else None,
                        "teacher": lines[2].strip() if len(lines) > 2 else None,
                        "classroom": lines[3].strip() if len(lines) > 3 else None,
                        "day": day,
                        "start_time": start_time,
                        "end_time": "09:00",  # End time not available in grid format
                    })

    return entries


# Define standard VTOP times
VIT_THEORY_STARTS = ["08:00", "08:55", "09:50", "10:45", "11:40", "12:35", "Lunch", "14:00", "14:55", "15:50", "16:45", "17:40", "18:35"]
VIT_THEORY_ENDS   = ["08:50", "09:45", "10:40", "11:35", "12:30", "13:25", "Lunch", "14:50", "15:45", "16:40", "17:35", "18:30", "19:25"]
VIT_LAB_STARTS    = ["08:00", "08:50", "09:50", "10:40", "11:40", "12:30", "Lunch", "14:00", "14:50", "15:50", "16:40", "17:40", "18:30"]
VIT_LAB_ENDS      = ["08:50", "09:40", "10:40", "11:30", "12:30", "13:20", "Lunch", "14:50", "15:40", "16:40", "17:30", "18:30", "19:20"]

def parse_format_c(wb) -> List[Dict[str, Any]]:
    """
    Format C: VTOP Timetable.
    Detects VTOP format by looking for specific headers in course details or the specific grid structure.
    """
    course_map = {}
    
    # 1. Parse Course Details
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        
        in_course_table = False
        course_col = -1
        faculty_col = -1
        
        for row in rows:
            if not in_course_table:
                row_strs = [str(c).strip().lower() for c in row if c is not None]
                if "course" in row_strs and "faculty details" in row_strs:
                    in_course_table = True
                    course_col = row_strs.index("course")
                    faculty_col = row_strs.index("faculty details")
            else:
                if not any(row):
                    continue
                if course_col < len(row) and faculty_col < len(row):
                    course_cell = row[course_col]
                    faculty_cell = row[faculty_col]
                    
                    if course_cell and faculty_cell and " - " in str(course_cell):
                        parts = str(course_cell).split(" - ", 1)
                        code = parts[0].strip()
                        name = parts[1].strip() if len(parts) > 1 else code
                        
                        fac_parts = str(faculty_cell).split(" - ", 1)
                        teacher = fac_parts[0].strip()
                        
                        course_map[code] = {"name": name, "teacher": teacher}

    # 2. Parse Grid
    entries = []
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        
        theory_starts = VIT_THEORY_STARTS
        theory_ends = VIT_THEORY_ENDS
        lab_starts = VIT_LAB_STARTS
        lab_ends = VIT_LAB_ENDS
        
        grid_start_row = -1
        day_col_idx = -1
        type_col_idx = -1
        data_col_idx = -1
        
        # Detect grid
        for i, row in enumerate(rows):
            # Check all cells to find a day (e.g., "MON") followed by "THEORY"
            for j in range(len(row) - 1):
                if str(row[j]).strip().upper() in days and str(row[j+1]).strip().upper() == "THEORY":
                    grid_start_row = i
                    day_col_idx = j
                    type_col_idx = j + 1
                    data_col_idx = j + 2
                    break
            if grid_start_row != -1:
                break
                
        if grid_start_row != -1:
            current_day = None
            
            for i in range(grid_start_row, len(rows)):
                row = rows[i]
                if not any(row):
                    continue
                    
                cell_day = str(row[day_col_idx]).strip().upper() if day_col_idx < len(row) and row[day_col_idx] is not None else ""
                cell_type = str(row[type_col_idx]).strip().upper() if type_col_idx < len(row) and row[type_col_idx] is not None else ""
                
                if cell_day in days:
                    current_day = cell_day
                    
                if cell_type not in ["THEORY", "LAB"]:
                    continue
                    
                if not current_day:
                    continue
                    
                starts = theory_starts if cell_type == "THEORY" else lab_starts
                ends = theory_ends if cell_type == "THEORY" else lab_ends
                
                for col_idx in range(data_col_idx, len(row)):
                    cell = row[col_idx]
                    if not cell or str(cell).strip() == "" or str(cell).strip() == "-":
                        continue
                        
                    cell_text = str(cell).strip()
                    
                    if "-" in cell_text and len(cell_text.split("-")) > 2:
                        parts = cell_text.split("-")
                        slot = parts[0]
                        course_code = parts[1]
                        venue = parts[3] + "-" + parts[4] if len(parts) > 4 else (parts[3] if len(parts) > 3 else "")
                            
                        mapped = course_map.get(course_code, {})
                        subject_name = mapped.get("name", course_code)
                        teacher = mapped.get("teacher", "Unknown")
                        
                        time_idx = col_idx - data_col_idx
                        start_time = starts[time_idx] if time_idx < len(starts) else "00:00"
                        end_time = ends[time_idx] if time_idx < len(ends) else "00:00"
                        
                        if start_time.lower() != "lunch":
                            day_full = normalize_day(current_day) or current_day.capitalize()
                            entries.append({
                                "subject_name": subject_name,
                                "course_code": course_code,
                                "teacher": teacher,
                                "classroom": venue,
                                "day": day_full,
                                "start_time": start_time,
                                "end_time": end_time
                            })
                            
            if entries:
                return entries

    return []


def parse_courses_excel(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a Courses spreadsheet containing explicitly separated columns like:
    Course Code, Course Name, C (Credits), Faculty, etc.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    courses = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        
        header_row_idx = -1
        code_col = -1
        name_col = -1
        credits_col = -1
        faculty_col = -1
        type_col = -1
        
        # Find headers
        for i, row in enumerate(rows):
            row_strs = [str(c).strip().lower() for c in row if c is not None]
            if "course code" in row_strs or "course name" in row_strs or "subject" in row_strs:
                header_row_idx = i
                # map columns precisely
                for j, cell in enumerate(row):
                    if not cell:
                        continue
                    header = str(cell).strip().lower()
                    if header in ["course code", "code"]:
                        code_col = j
                    elif header in ["course name", "course", "subject", "subject name"]:
                        name_col = j
                    elif header in ["c", "credits"]:
                        credits_col = j
                    elif header in ["faculty", "teacher", "faculty details"]:
                        faculty_col = j
                    elif header in ["course type", "type", "category"]:
                        type_col = j
                break
                
        if header_row_idx != -1:
            # Parse data rows
            for row in rows[header_row_idx + 1:]:
                if not any(row):
                    continue
                
                code = str(row[code_col]).strip() if code_col != -1 and code_col < len(row) and row[code_col] is not None else None
                name = str(row[name_col]).strip() if name_col != -1 and name_col < len(row) and row[name_col] is not None else None
                faculty = str(row[faculty_col]).strip() if faculty_col != -1 and faculty_col < len(row) and row[faculty_col] is not None else None
                course_type = str(row[type_col]).strip() if type_col != -1 and type_col < len(row) and row[type_col] is not None else "Theory"
                
                credits_val = 3.0
                if credits_col != -1 and credits_col < len(row) and row[credits_col] is not None:
                    try:
                        credits_val = float(str(row[credits_col]).strip())
                    except ValueError:
                        pass
                
                if not name and not code:
                    continue
                    
                # Clean composite course code (e.g. B1-BAMEE101-ETH-AB2-201-ALL03 -> BAMEE101)
                clean_code = code
                if code and "-" in code:
                    parts = code.split("-")
                    if len(parts) >= 3:
                        clean_code = parts[1].strip()
                    else:
                        clean_code = code.strip()
                elif code:
                    clean_code = code.strip()

                # Clean name if it matches code or is empty
                clean_name = name.strip() if name else ""
                if not clean_name and clean_code:
                    clean_name = clean_code

                # Skip dummy slots (e.g. Code = Name = 'G1' or 'E1')
                if clean_code == clean_name and len(clean_code) <= 4:
                    continue
                    
                courses.append({
                    "course_code": clean_code,
                    "name": clean_name or clean_code,
                    "teacher": faculty,
                    "course_type": course_type,
                    "credits": credits_val
                })
            
    # Deduplicate unique courses across all sheets and sum credits of distinct components
    unique_courses = {}
    seen_components = set()
    for item in courses:
        code = item["course_code"]
        name = item["name"]
        key = code or name
        ctype = item["course_type"] or "Theory"
        
        comp_key = (code, ctype) if code else (name, ctype)
        
        if key in unique_courses:
            if comp_key not in seen_components:
                seen_components.add(comp_key)
                unique_courses[key]["credits"] += item["credits"]
                # Combine course type if different (e.g. Theory + Lab)
                existing_type = unique_courses[key]["course_type"]
                if existing_type != ctype and ctype not in existing_type:
                    unique_courses[key]["course_type"] = f"{existing_type} + {ctype}"
        else:
            seen_components.add(comp_key)
            unique_courses[key] = item

    return list(unique_courses.values())


def parse_timetable_excel(file_path: str) -> List[Dict[str, Any]]:
    """
    Main parser entry point.
    Tries Format C (VTOP) first, then Format A (row-per-class), falls back to Format B (grid).
    Returns list of timetable entry dicts.
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    
    # Try Format C (VTOP) first
    entries = parse_format_c(wb)
    if entries:
        return entries
        
    ws = wb.active

    # Try Format A first
    entries = parse_format_a(ws)
    if entries:
        return entries

    # Try other sheets
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        entries = parse_format_a(ws)
        if entries:
            return entries

    # Fall back to Format B (grid)
    ws = wb.active
    entries = parse_format_b(ws)
    return entries
