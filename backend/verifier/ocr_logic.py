import sqlite3
import easyocr
import re
import cv2
import os

# ==============================
# 1. ONE-TIME SETUP 
# ==============================
print("Initializing OCR Logic Module...")

conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE marksheets (
    roll_no TEXT, semester TEXT, student_name TEXT NOT NULL, father_name TEXT, mother_name TEXT,
    institution_name TEXT NOT NULL, course_name TEXT, academic_year TEXT, apaar_id TEXT,
    reg_no TEXT, 
 
    yoga INTEGER, environmental_science INTEGER, computer_programming INTEGER,
    electrical_science INTEGER, general_english INTEGER, mathematics_1 INTEGER, physics INTEGER,

    intro_to_aiml INTEGER, intro_to_web_programming INTEGER, written_communication INTEGER,
    english_workshop INTEGER, mathematics_2 INTEGER, statistics INTEGER, contemporary_india INTEGER,
    -- Grades
    sgpa REAL, cgpa REAL, issue_date TEXT, digital_signature_date TEXT,
    PRIMARY KEY (roll_no, semester)
)""")
sample_data = [
    # Ved Changani - Semester I
    ("24BTM006", "I", "CHANGANI VED PARESH", "PARESH CHANGANI", "ASMITA CHANGANI", "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION", "2024-25", "672534463458", "24BTMBA293", 
    100, 85, 95, 85, 95, 100, 95,            # Sem I Subjects
    None, None, None, None, None, None, None, # Sem II Subjects are None
    8.83, 8.83, "DECEMBER - 2024", "13/06/2025 10:36:04 IST"),

    # Maanush Raval - Semester I
    ("24BTM004", "I", "MAANUSH TARANG RAVAL", "TARANG PRAVINCHANDRA RAVAL", "KHYATI TARANG RAVAL", "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION", "2024-25", "293581074998", "24BTMBA291", 
    100, 78, 100, 85, 95, 95, 85,            # Sem I Subjects
    None, None, None, None, None, None, None, # Sem II Subjects are None
    8.50, 8.50, "DECEMBER - 2024", "13/09/2025 11:35:17 IST"),
    
    # Jainish Shah - Semester I
    ("24BTM007", "I", "JAINISH NIRAVKUMAR SHAH", "NIRAVKUMAR DINESHCHANDRA SHAH", "SWEETUBEN NIRAVKUMAR SHAH", "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION", "2024-25", "509111879191", "24BTMBA294", 
    95, 85, 85, 85, 85, 95, 95,              # Sem I Subjects
    None, None, None, None, None, None, None, # Sem II Subjects are None
    8.83, 8.83, "DECEMBER - 2024", "07/06/2025 13:02:57 IST"),

    # Yashvi Joshi - Semester I
    ("24BCE023", "I", "JOSHI YASHVI KALPESHKUMAR", "KALPESHKUMAR BHALCHANDRA JOSHI", "TEJAL KALPESHKUMAR JOSHI", "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", "B. TECH. IN COMPUTER SCIENCE AND ENGINEERING", "2024-25", "630602333570", "24BTE19477", 
    100, 95, 100, 95, 100, 100, 100,          # Sem I Subjects
    None, None, None, None, None, None, None, # Sem II Subjects are None
    9.67, 9.67, "DECEMBER - 2024", "19/05/2025 12:01:24 IST"),

    # Yashvi Joshi - Semester II
    ("24BCE023", "II", "JOSHI YASHVI KALPESHKUMAR", "KALPESHKUMAR BHALCHANDRA JOSHI", "TEJAL KALPESHKUMAR JOSHI", "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", "B. TECH. IN COMPUTER SCIENCE AND ENGINEERING", "2024-25", "630602333570", "24BTE19477", 
    None, None, None, None, None, None, None, # Sem I Subjects are None
    100, 100, 85, 100, 100, 100, 100,         # Sem II Subjects
    9.86, 9.77, "APRIL - 2025", "13/09/2025 10:58:05 IST"),
]
cursor.executemany("INSERT INTO marksheets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", sample_data)
conn.commit()

reader = easyocr.Reader(['en'])
print("✅ OCR Logic Module Initialized.")

# ==============================
# 2. YOUR ORIGINAL HELPER FUNCTIONS
# ==============================
def upscale_image(image_path, scale=2):
    try:
        img = cv2.imread(image_path)
        if img is None: return image_path
        height, width = img.shape[:2]
        new_dim = (width * scale, height * scale)
        upscaled = cv2.resize(img, new_dim, interpolation=cv2.INTER_CUBIC)
        temp_path = f"{os.path.splitext(image_path)[0]}_upscaled.png"
        cv2.imwrite(temp_path, upscaled)
        return temp_path
    except Exception:
        return image_path

def extract_text_from_image(image_path, ocr_reader):
    try:
        results = ocr_reader.readtext(image_path)
        return [text.strip() for (bbox, text, confidence) in results if confidence > 0.3]
    except Exception:
        return []

# In backend/verifier/ocr_logic.py

def parse_certificate_data(extracted_texts):
    certificate_data = {'student_name': None, 'father_name': None, 'mother_name': None, 'roll_no': None, 'reg_no': None, 'apaar_id': None, 'institution_name': None, 'course_name': None, 'academic_year': None, 'semester': None, 'subjects': {}, 'sgpa': None, 'cgpa': None, 'issue_date': None, 'digital_signature_date': None}
    full_text = ' '.join(extracted_texts)
    print(f"\n🔍 DEBUG: Full extracted text preview:\nFirst 500 characters: {full_text[:500]}")
    
    # --- THIS IS THE CORRECTED PART ---
    patterns = {
        'student_name': [r'Name\s*:?\s*([A-Z]+\s+[A-Z]+\s+[A-Z]+)', r'Name\s*([A-Z\s]+?)(?:Father|Reg|Roll)'], 
        'father_name': [r'Father\'?s?\s*Name\s*([A-Z\s]+?)(?:Mother|College|Institute)'], 
        'mother_name': [r'Mother\'?s?\s*Name\s*([A-Z\s]+?)(?:College|Institute|Roll)'], 
        # IMPROVED REGEX: Allows for 'O' or '0' in the number parts
        'roll_no': [r'Roll\s*No\.?\s*([0-9O]{2}[A-Z]{3}[0-9O]{3})', r'\b([0-9O]{2}[A-Z]{3}[0-9O]{3})\b'], 
        'reg_no': [r'Reg\s*No\.?\s*([A-Z0-9]+)'], 'apaar_id': [r'APAAR\s*ID\s*:?\s*([0-9]{12})'], 
        'sgpa': [r'SGPA\s*:?\s*([0-9]+\.?[0-9]*)'], 'cgpa': [r'CGPA\s*:?\s*([0-9]+\.?[0-9]*)'], 
        'semester': [r'SEMESTER\s*-?\s*([IVX]+)'], 
        'issue_date': [r'MONTH\s*&\s*YEAR\s*OF\s*PASSING\s*:?\s*([A-Z]+\s*-\s*[0-9]{4})'], 
        'digital_signature_date': [r'Digitally\s*signed\s*on\s*Date\s*:?\s*([0-9/\s:]+IST)']
    }
    # --- END OF CORRECTION ---

    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip().upper()
                
                # --- ADDED NORMALIZATION STEP ---
                # If we found a roll number, replace any 'O's with '0's
                if field == 'roll_no':
                    value = value.replace('O', '0')
                # ---------------------------------

                certificate_data[field] = value
                break

    if 'NIRMA UNIVERSITY' in full_text.upper():
        certificate_data['institution_name'] = 'INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY'
        
    # (The rest of your parsing logic for subjects remains the same)
    grade_to_marks = {'O': 100, 'A+': 95, 'A': 85, 'B+': 78, 'B': 75, 'C+': 68, 'C': 60, 'D': 50, 'F': 0}
    subject_patterns = {'environmental_science': [r'ENVIRONMENTAL\s+SCIENCE\s+([A-Z+]+)'], 'computer_programming': [r'COMPUTER\s+PROGRAMMING\s+([A-Z+]+)'], 'electrical_science': [r'ELECTRICAL\s+SCIENCE\s+([A-Z+]+)'], 'general_english': [r'GENERAL\s+ENGLISH\s+([A-Z+]+)'], 'mathematics': [r'MATHEMATICS\s*-?\s*I\s+([A-Z+]+)'], 'physics': [r'PHYSICS\s+([A-Z+]+)']}
    for subject, patterns_list in subject_patterns.items():
        for pattern in patterns_list:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                grade = match.group(1).strip().upper()
                if grade in grade_to_marks:
                    certificate_data['subjects'][subject] = grade_to_marks[grade]
                break
                
    return certificate_data
# In backend/verifier/ocr_logic.py

def find_student_by_multiple_criteria(certificate_data):
    """Finds the specific student record using both Roll Number and Semester."""
    roll_no = certificate_data.get('roll_no')
    norm_cert_sem = normalize_semester(certificate_data.get('semester'))

    if not roll_no:
        return None # Cannot search without a roll number

    # Fetch all records for the given roll number
    cursor.execute("SELECT * FROM marksheets WHERE roll_no = ?", (roll_no,))
    all_records_for_student = cursor.fetchall()

    if not all_records_for_student:
        return None # No records found at all for this roll number

    # If we couldn't parse a semester from the certificate, return the first record as a fallback.
    if not norm_cert_sem:
        print(f"⚠️ OCR did not find a semester. Falling back to first record for Roll No: {roll_no}")
        return all_records_for_student[0]

    # Loop through the found records to find the one with the matching semester
    for row in all_records_for_student:
        columns = [description[0] for description in cursor.description]
        db_record = dict(zip(columns, row))
        norm_db_sem = normalize_semester(db_record.get('semester'))
        
        if norm_cert_sem == norm_db_sem:
            print(f"✅ Found specific record for Roll No: {roll_no} and Semester: {norm_cert_sem}")
            return row # Return the exact matching row
            
    # If no specific semester match was found, return the first record as a fallback
    print(f"⚠️ Could not find a specific semester match for {norm_cert_sem}. Returning first available record.")
    return all_records_for_student[0]
def verify_with_database(certificate_data):
    row = find_student_by_multiple_criteria(certificate_data)
    if not row:
        return False, "No matching student record found in database.", None
    
    columns = [description[0] for description in cursor.description]
    db_record = dict(zip(columns, row))
    return True, "Database record found.", db_record

# --- NEW HELPER FUNCTION FOR SEMESTER NORMALIZATION ---
def normalize_semester(semester_string):
    """Converts various semester formats ('SEMESTER - II', '2', 'II') to a standard Roman numeral."""
    if not semester_string:
        return None
    
    s = str(semester_string).strip().upper()
    
    # Check for Roman numerals first
    roman_match = re.search(r'\b(I|II|III|IV|V|VI|VII|VIII)\b', s)
    if roman_match:
        return roman_match.group(1)
        
    # Check for Arabic numerals
    arabic_to_roman = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII'}
    arabic_match = re.search(r'\b([1-8])\b', s)
    if arabic_match:
        return arabic_to_roman.get(arabic_match.group(1))
        
    return None # Return None if no standard format is found

# ==============================
# 3. "TRANSLATOR" FOR THE FRONTEND
# ==============================
def build_frontend_response(is_valid, message, db_record, certificate_data):
    if not is_valid or not db_record:
        return {"isAuthentic": False, "confidence": 0, "overallStatus": "fraudulent", "error": message}

    verification_results = {'basic_info': [], 'academic_info': []}
    
    basic_checks = [('student_name', 'Student Name'), ('father_name', 'Father Name'), ('roll_no', 'Roll Number')]
    for cert_field, display_name in basic_checks:
        cert_val = certificate_data.get(cert_field)
        db_val = db_record.get(cert_field)
        if cert_val is not None and db_val is not None:
            is_match = str(cert_val).upper().strip() == str(db_val).upper().strip()
            verification_results['basic_info'].append((display_name, is_match, cert_val, db_val))

    academic_checks = [('sgpa', 'SGPA'), ('cgpa', 'CGPA'), ('semester', 'Semester')]
    for cert_field, display_name in academic_checks:
        cert_val = certificate_data.get(cert_field)
        db_val = db_record.get(cert_field)
        if cert_val is not None and db_val is not None:
            is_match = False
            # --- ENHANCED SEMESTER CHECK ---
            if cert_field == 'semester':
                norm_cert_sem = normalize_semester(cert_val)
                norm_db_sem = normalize_semester(db_val)
                if norm_cert_sem and norm_db_sem and norm_cert_sem == norm_db_sem:
                    is_match = True
            # --- END OF ENHANCEMENT ---
            elif cert_field in ['sgpa', 'cgpa']:
                try:
                    is_match = abs(float(cert_val) - float(db_val)) < 0.01
                except (ValueError, TypeError):
                    is_match = False
            else:
                is_match = str(cert_val).upper().strip() == str(db_val).upper().strip()
            
            verification_results['academic_info'].append((display_name, is_match, cert_val, db_val))

    final_checks = {}
    total_checks = 0; passed_checks = 0
    for category, results in verification_results.items():
        final_checks[category] = []
        for display_name, is_match, cert_val, db_val in results:
            total_checks += 1
            if is_match: passed_checks += 1
            final_checks[category].append({"field": display_name, "status": "passed" if is_match else "failed", "certificateValue": str(cert_val), "databaseValue": str(db_val)})
    
    confidence = round((passed_checks / total_checks) * 100) if total_checks > 0 else 0
    overall_status = "authentic" if confidence >= 80 else "fraudulent"

    return {
        "isAuthentic": overall_status == "authentic", "confidence": confidence,
        "studentInfo": { "name": db_record.get('student_name', 'N/A'), "rollNo": db_record.get('roll_no', 'N/A'), "fatherName": db_record.get('father_name', 'N/A') },
        "verificationDetails": [{"category": cat, "checks": chks} for cat, chks in final_checks.items() if chks],
        "overallStatus": overall_status
    }

# ==============================
# 4. MAIN "ENTRY POINT" FUNCTION
# ==============================
def process_and_verify_image(image_path):
    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")
        
    upscaled_path = upscale_image(image_path, scale=2)
    extracted_texts = extract_text_from_image(upscaled_path, reader)
    if upscaled_path != image_path and os.path.exists(upscaled_path):
        os.remove(upscaled_path)
    if not extracted_texts:
        raise ValueError("Could not extract any text from the image.")
        
    certificate_data = parse_certificate_data(extracted_texts)
    
    print("--- DEBUG: OCR PARSED DATA ---", certificate_data)
    
    is_valid, message, db_record = verify_with_database(certificate_data)
    print(f"\n--- TERMINAL REPORT ---\n{message}\n-----------------------\n")
    final_report = build_frontend_response(is_valid, message, db_record, certificate_data)
    return final_report

def normalize_semester(semester_string):
    # """Converts various semester formats ('SEMESTER - II', '2', 'II') to a standard Roman numeral."""
    if not semester_string:
        return None
    
    s = str(semester_string).strip().upper()
    
    # Check for Roman numerals first
    roman_match = re.search(r'\b(I|II|III|IV|V|VI|VII|VIII)\b', s)
    if roman_match:
        return roman_match.group(1)
        
    # Check for Arabic numerals
    arabic_to_roman = {'1': 'I', '2': 'II', '3': 'III', '4': 'IV', '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII'}
    arabic_match = re.search(r'\b([1-8])\b', s)
    if arabic_match:
        return arabic_to_roman.get(arabic_match.group(1))
        
    return None # Return None if no standard format is found