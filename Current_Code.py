import sqlite3
import easyocr
import re
import cv2
import numpy as np
from PIL import Image
from datetime import datetime


# ==============================
# STEP 1: SETUP DATABASE
# ==============================
# Use ':memory:' for temporary database or use 'marksheets.db' for persistent storage
conn = sqlite3.connect(':memory:')  # Change to 'marksheets.db' if you want persistent storage
cursor = conn.cursor()

# Create comprehensive table with composite primary key (roll_no + semester)
cursor.execute("""
CREATE TABLE marksheets (
    roll_no TEXT,
    semester TEXT,
    student_name TEXT NOT NULL,
    father_name TEXT,
    mother_name TEXT,
    institution_name TEXT NOT NULL,
    course_name TEXT,
    academic_year TEXT,
    apaar_id TEXT,
    reg_no TEXT,
    yoga INTEGER,
    environmental_science INTEGER,
    computer_programming INTEGER,
    electrical_science INTEGER,
    general_english INTEGER,
    mathematics INTEGER,
    physics INTEGER,
    sgpa REAL,
    cgpa REAL,
    issue_date TEXT,
    digital_signature_date TEXT,
    PRIMARY KEY (roll_no, semester)   -- ✅ composite key
)
""")
print("Database and table created successfully.")

# ==============================
# STEP 2: INSERT COMPREHENSIVE SAMPLE DATA
# ==============================
sample_data = [
    # Ved Changani - Semester I
    ("24BTM006", "SEMESTER - I", "CHANGANI VED PARESH", "PARESH CHANGANI", "ASMITA CHANGANI",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", 
     "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION",
     "2024-25", "672534463458", "24BTMBA293",
     100, 85, 95, 85, 95, 100, 95, 8.83, 8.83, "DECEMBER - 2024", "13/06/2025 10:36:04 IST"),

    #Vedika Shah- Semester I
    ("24BCE025", "SEMESTER - I", "VEDIKA SHAH", "HARDIK SHAH", "RADHIKA SHAH",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY",
     "B. TECH. IN COMPUTER SCIENCE AND ENGINEERING",
     "2024-25", "642754965939", "24BTE19479",
     100, 85, 85, 95, 95, 100, 85, 8.67, 8.67, "DECEMBER - 2024", "06/03/2025 22:31:40 IST"),

    # Yashvi Joshi - Semester I
    ("24BCE023", "SEMESTER - I", "JOSHI YASHVI KALPESHKUMAR", "KALPESHKUMAR BHALCHANDRA JOSHI", "TEJAL KALPESHKUMAR JOSHI",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY",
     "B. TECH. IN COMPUTER SCIENCE AND ENGINEERING",
     "2024-25", "630602333570", "24BTE19477",
     100, 95, 100, 95, 100, 100, 100, 9.67, 9.67, "DECEMBER - 2024", "19/05/2025 12:01:24 IST"),

    # Yashvi Joshi - Semester II
    ("24BCE023", "SEMESTER - II", "JOSHI YASHVI KALPESHKUMAR", "KALPESHKUMAR BHALCHANDRA JOSHI", "TEJAL KALPESHKUMAR JOSHI",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY",
     "B. TECH. IN COMPUTER SCIENCE AND ENGINEERING",
     "2024-25", "630602333570", "24BTE19477",
     100, 100, 95, 100, 100, 100, 100, 9.86, 9.77, "APRIL - 2025", "13/09/2025 10:58:05 IST"),

    # Maanush Raval - Semester I
    ("24BTM004", "SEMESTER - I", "MAANUSH TARANG RAVAL", "TARANG PRAVINCHANDRA RAVAL", "KHYATI TARANG RAVAL",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY",
     "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION",
     "2024-25", "293581074998", "24BTMBA291",
     100, 78, 100, 85, 95, 95, 85, 8.50, 8.50, "DECEMBER - 2024", "13/09/2025 11:35:17 IST"),

    # Jainish Shah - Semester I
    ("24BTM007", "SEMESTER - I", "JAINISH NIRAVKUMAR SHAH", "NIRAVKUMAR DINESHCHANDRA SHAH", "SWEETUBEN NIRAVKUMAR SHAH",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY",
     "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION",
     "2024-25", "509111879191", "24BTMBA294",
     95, 95, 85, 85, 85, 95, 95, 8.83, 8.83, "DECEMBER - 2024", "07/06/2025 13:02:57 IST"),

    # Sharma Rahul - Semester I
    ("24BTM008", "SEMESTER - I", "SHARMA RAHUL KUMAR", "KUMAR SHARMA", "PRIYA SHARMA",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", 
     "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION",
     "2024-25", "123456789012", "24BTMBA296",
     78, 85, 75, 85, 85, 100, 78, 7.95, 7.95, "DECEMBER - 2024", "13/06/2025 10:36:04 IST"),
    
    # Patel Priya - Semester I
    ("24BTM009", "SEMESTER - I", "PATEL PRIYA AMIT", "AMIT PATEL", "NEHA PATEL",
     "INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY", 
     "INTEGRATED BACHELOR OF TECHNOLOGY (COMPUTER SCIENCE AND ENGINEERING) - MASTER OF BUSINESS ADMINISTRATION",
     "2024-25", "987654321098", "24BTMBA295",
     90, 88, 92, 95, 87, 95, 89, 8.50, 8.50, "DECEMBER - 2024", "13/06/2025 10:36:04 IST"),
]

# Clear old data and insert new data
cursor.execute("DELETE FROM marksheets")
cursor.executemany("""
INSERT INTO marksheets
(roll_no, semester, student_name, father_name, mother_name, institution_name, course_name, academic_year, 
 apaar_id, reg_no, yoga, environmental_science, computer_programming, electrical_science, 
 general_english, mathematics, physics, sgpa, cgpa, issue_date, digital_signature_date)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", sample_data)

conn.commit()
print("✅ Comprehensive sample data inserted successfully.")


# ==============================
# STEP 3: OCR SETUP AND FUNCTIONS
# ==============================

def initialize_ocr():
    """Initialize EasyOCR reader"""
    try:
        # Initialize EasyOCR for English text
        reader = easyocr.Reader(['en'])
        print("✅ EasyOCR initialized successfully.")
        return reader
    except Exception as e:
        print(f"❌ Error initializing EasyOCR: {e}")
        return None

def preprocess_image(image_path):
    """Preprocess image for better OCR results"""
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load image: {image_path}")
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive threshold for better text contrast
        thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        return thresh
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        return None

def extract_text_from_image(image_path, reader):
    """Extract text from certificate image using EasyOCR"""
    try:
        # Try both original and preprocessed image
        results = []
        
        # Original image
        original_result = reader.readtext(image_path)
        
        # Preprocessed image
        processed_img = preprocess_image(image_path)
        if processed_img is not None:
            processed_result = reader.readtext(processed_img)
            # Combine results
            results.extend(original_result)
            results.extend(processed_result)
        else:
            results = original_result
        
        # Extract text from OCR results
        extracted_texts = []
        for (bbox, text, confidence) in results:
            if confidence > 0.3:  # Lower threshold for better detection
                extracted_texts.append(text.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_texts = []
        for text in extracted_texts:
            if text not in seen:
                unique_texts.append(text)
                seen.add(text)
        
        return unique_texts
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return []

def parse_certificate_data(extracted_texts):
    """Parse extracted text to find relevant certificate information"""
    certificate_data = {
        'student_name': None,
        'father_name': None,
        'mother_name': None,
        'roll_no': None,
        'reg_no': None,
        'apaar_id': None,
        'institution_name': None,
        'course_name': None,
        'academic_year': None,
        'semester': None,
        'subjects': {},
        'sgpa': None,
        'cgpa': None,
        'issue_date': None,
        'digital_signature_date': None
    }
    
    # Join all texts for easier pattern matching
    full_text = ' '.join(extracted_texts)
    
    print(f"\n🔍 DEBUG: Full extracted text preview:")
    print(f"Text length: {len(full_text)} characters")
    print(f"First 500 characters: {full_text[:500]}")
    
    # Enhanced patterns for different data extraction
    patterns = {
        'student_name': [
            r'Name\s*([A-Z\s]+?)(?:Father|Reg|Roll|Academic|APAAR)',
            r'NAME\s*([A-Z\s]+?)(?:FATHER|REG|ROLL|ACADEMIC|APAAR)',
            r'([A-Z]{3,}\s+[A-Z]{3,}\s+[A-Z]{3,})',  # Three consecutive uppercase words
        ],
        'father_name': [
            r'Father\'?s?\s*Name\s*([A-Z\s]+?)(?:Mother|College|Institute)',
            r'FATHER\'?S?\s*NAME\s*([A-Z\s]+?)(?:MOTHER|COLLEGE|INSTITUTE)',
        ],
        'mother_name': [
            r'Mother\'?s?\s*Name\s*([A-Z\s]+?)(?:College|Institute|Roll)',
            r'MOTHER\'?S?\s*NAME\s*([A-Z\s]+?)(?:COLLEGE|INSTITUTE|ROLL)',
        ],
        'roll_no': [
            r'Roll\s*No\.?\s*([0-9]{2}[A-Z]{3}[0-9]{3})',  # Pattern like 24BTM006
            r'ROLL\s*NO\.?\s*([0-9]{2}[A-Z]{3}[0-9]{3})',
            r'([0-9]{2}[A-Z]{3}[0-9]{3})',
        ],
        'reg_no': [
            r'Reg\s*No\.?\s*([A-Z0-9]+)',
            r'REG\s*NO\.?\s*([A-Z0-9]+)',
            r'Registration\s*No\.?\s*([A-Z0-9]+)',
        ],
        'apaar_id': [
            r'APAAR\s*ID\s*:?\s*([0-9]{12})',
            r'APAAR\s*([0-9]{12})',
        ],
        'sgpa': [
            r'SGPA\s*:?\s*([0-9]+\.?[0-9]*)',
        ],
        'cgpa': [
            r'CGPA\s*:?\s*([0-9]+\.?[0-9]*)',
        ],
        'academic_year': [
            r'ACADEMIC\s*YEAR\s*:?\s*([0-9-]+)',
            r'([0-9]{4}-[0-9]{2})',
        ],
        'semester': [
            r'SEMESTER\s*-?\s*([IVX]+)',
            r'SEM\s*-?\s*([IVX]+)',
        ],
        'issue_date': [
            r'MONTH\s*&\s*YEAR\s*OF\s*PASSING\s*:?\s*([A-Z]+\s*-\s*[0-9]{4})',
            r'DECEMBER\s*-\s*[0-9]{4}',
        ],
        'digital_signature_date': [
            r'Digitally\s*signed\s*on\s*Date\s*:?\s*([0-9/\s:]+IST)',
            r'([0-9]{2}/[0-9]{2}/[0-9]{4}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\s+IST)',
        ]
    }
    
    # Extract each field
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                certificate_data[field] = match.group(1).strip()
                print(f"✅ Found {field}: {certificate_data[field]}")
                break
    
    # Extract institution name
    if 'NIRMA UNIVERSITY' in full_text.upper():
        certificate_data['institution_name'] = 'INSTITUTE OF TECHNOLOGY, NIRMA UNIVERSITY'
        print(f"✅ Found institution_name: {certificate_data['institution_name']}")
    
    # Extract subject grades and convert to marks
    grade_to_marks = {'O': 100, 'A+': 95, 'A': 85, 'B+': 78, 'B': 75, 'C+': 68, 'C': 60, 'D': 50, 'F': 0}
    
    subject_patterns = {
        'environmental_science': [
            r'ENVIRONMENTAL\s+SCIENCE\s+([A-Z+]+)',
            r'1CL501CC22\s+ENVIRONMENTAL\s+SCIENCE\s+([A-Z+]+)',
        ],
        'computer_programming': [
            r'COMPUTER\s+PROGRAMMING\s+([A-Z+]+)',
            r'1CS501CC22\s+COMPUTER\s+PROGRAMMING\s+([A-Z+]+)',
        ],
        'electrical_science': [
            r'ELECTRICAL\s+SCIENCE\s+([A-Z+]+)',
            r'1EE801CC22\s+ELECTRICAL\s+SCIENCE\s+([A-Z+]+)',
        ],
        'general_english': [
            r'GENERAL\s+ENGLISH\s+([A-Z+]+)',
            r'1HS101CC22\s+GENERAL\s+ENGLISH\s+([A-Z+]+)',
        ],
        'mathematics': [
            r'MATHEMATICS\s*-?\s*I\s+([A-Z+]+)',
            r'1MH101CC22\s+MATHEMATICS\s*-?\s*I\s+([A-Z+]+)',
        ],
        'physics': [
            r'PHYSICS\s+([A-Z+]+)',
            r'1SP201CC22\s+PHYSICS\s+([A-Z+]+)',
        ],
    }
    
    for subject, patterns_list in subject_patterns.items():
        for pattern in patterns_list:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                grade = match.group(1).strip().upper()
                if grade in grade_to_marks:
                    certificate_data['subjects'][subject] = grade_to_marks[grade]
                    print(f"✅ Found {subject}: Grade {grade} = {grade_to_marks[grade]} marks")
                break
    
    return certificate_data

def find_student_by_multiple_criteria(certificate_data):
    """Find student using multiple identification criteria"""

    # Strategy 0: Roll number + Semester (most reliable if both are available)
    if certificate_data['roll_no'] and certificate_data['semester']:
        print(f"\n🔍 Searching by Roll Number + Semester: {certificate_data['roll_no']} | {certificate_data['semester']}")
        cursor.execute("""
        SELECT * FROM marksheets 
        WHERE roll_no = ? AND semester = ?
        """, (certificate_data['roll_no'], certificate_data['semester']))
        row = cursor.fetchone()
        if row:
            print("✅ Student found using Roll Number + Semester!")
            return row
        else:
            print("❌ No match found using Roll Number + Semester")

    # Strategy 1: Roll number
    if certificate_data['roll_no']:
        print(f"\n🔍 Searching by Roll Number: {certificate_data['roll_no']}")
        cursor.execute("SELECT * FROM marksheets WHERE roll_no = ?", (certificate_data['roll_no'],))
        row = cursor.fetchone()
        if row:
            print("✅ Student found using Roll Number!")
            return row
        else:
            print("❌ No match found using Roll Number")

    # Strategy 2: Registration number
    if certificate_data['reg_no']:
        print(f"\n🔍 Searching by Registration Number: {certificate_data['reg_no']}")
        cursor.execute("SELECT * FROM marksheets WHERE reg_no = ?", (certificate_data['reg_no'],))
        row = cursor.fetchone()
        if row:
            print("✅ Student found using Registration Number!")
            return row
        else:
            print("❌ No match found using Registration Number")

    # Strategy 3: APAAR ID
    if certificate_data['apaar_id']:
        print(f"\n🔍 Searching by APAAR ID: {certificate_data['apaar_id']}")
        cursor.execute("SELECT * FROM marksheets WHERE apaar_id = ?", (certificate_data['apaar_id'],))
        row = cursor.fetchone()
        if row:
            print("✅ Student found using APAAR ID!")
            return row
        else:
            print("❌ No match found using APAAR ID")

    # Strategy 4: Student name + institution (partial match)
    if certificate_data['student_name']:
        clean_name = re.sub(
            r'INTEGRATED|BACHELOR|TECHNOLOGY|MASTER|BUSINESS|ADMINISTRATION|COMPUTER|SCIENCE|ENGINEERING|AHMEDABAD',
            '', certificate_data['student_name'], flags=re.IGNORECASE)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()

        if clean_name:
            print(f"\n🔍 Searching by Student Name: {clean_name}")
            cursor.execute("""
            SELECT * FROM marksheets 
            WHERE UPPER(student_name) LIKE UPPER(?) 
            OR UPPER(?) LIKE '%' || UPPER(student_name) || '%'
            """, (f"%{clean_name}%", clean_name))
            row = cursor.fetchone()
            if row:
                print("✅ Student found using Student Name!")
                return row
            else:
                print("❌ No match found using Student Name")

    return None
 
  

def verify_with_database(certificate_data):
    """Comprehensive verification with detailed tampering detection"""
    
    print(f"\n📋 Certificate Data Extracted:")
    for key, value in certificate_data.items():
        if value:
            print(f"  {key}: {value}")
    
    # Find student record
    row = find_student_by_multiple_criteria(certificate_data)
    
    if not row:
        return False, "❌ No matching student record found in database. Possible reasons:\n" + \
               "  - Student not enrolled\n" + \
               "  - Completely fabricated certificate\n" + \
               "  - OCR failed to extract identifying information"
    
    # Get column names and create database record dict
    columns = [description[0] for description in cursor.description]
    db_record = dict(zip(columns, row))
    
    print(f"\n📂 Database Record Found:")
    for key, value in db_record.items():
        print(f"  {key}: {value}")
    
    # Detailed verification with tampering detection
    verification_results = {
        'basic_info': [],
        'academic_info': [],
        'subject_marks': [],
        'dates': []
    }
    
    # Basic Information Verification
    basic_checks = [
        ('student_name', 'Student Name'),
        ('father_name', 'Father Name'),
        ('mother_name', 'Mother Name'),
        ('roll_no', 'Roll Number'),
        ('reg_no', 'Registration Number'),
        ('apaar_id', 'APAAR ID'),
        ('institution_name', 'Institution'),
    ]
    
    for cert_field, display_name in basic_checks:
        if certificate_data[cert_field] and db_record[cert_field]:
            cert_val = str(certificate_data[cert_field]).upper().strip()
            db_val = str(db_record[cert_field]).upper().strip()
            
            # For names, allow partial matching
            if 'name' in cert_field.lower():
                # Clean up the certificate name by removing institution/course name parts
                if cert_field == 'student_name':
                    cert_val = re.sub(r'INTEGRATED|BACHELOR|TECHNOLOGY|MASTER|BUSINESS|ADMINISTRATION|COMPUTER|SCIENCE|ENGINEERING|AHMEDABAD', 
                                    '', cert_val, flags=re.IGNORECASE)
                    cert_val = re.sub(r'\s+', ' ', cert_val).strip()
                
                # Check if either name is contained in the other
                if cert_val in db_val or db_val in cert_val:
                    verification_results['basic_info'].append((display_name, True, cert_val, db_val))
                else:
                    verification_results['basic_info'].append((display_name, False, cert_val, db_val))
            else:
                if cert_val == db_val:
                    verification_results['basic_info'].append((display_name, True, cert_val, db_val))
                else:
                    verification_results['basic_info'].append((display_name, False, cert_val, db_val))
    
    # Academic Information Verification
    academic_checks = [
        ('sgpa', 'SGPA'),
        ('cgpa', 'CGPA'),
        ('academic_year', 'Academic Year'),
        ('semester', 'Semester'),
    ]
    
    for cert_field, display_name in academic_checks:
        if certificate_data[cert_field] and db_record[cert_field]:
            cert_val = certificate_data[cert_field]
            db_val = db_record[cert_field]
            
            if cert_field in ['sgpa', 'cgpa']:
                # Allow small floating point differences
                if abs(float(cert_val) - float(db_val)) < 0.01:
                    verification_results['academic_info'].append((display_name, True, cert_val, db_val))
                else:
                    verification_results['academic_info'].append((display_name, False, cert_val, db_val))
            elif cert_field == 'semester':
                # Extract just the numerical part for semester comparison
                cert_sem_num = re.search(r'([IVX]+)', str(cert_val).upper())
                db_sem_num = re.search(r'([IVX]+)', str(db_val).upper())
                
                if cert_sem_num and db_sem_num and cert_sem_num.group(1) == db_sem_num.group(1):
                    verification_results['academic_info'].append((display_name, True, cert_val, db_val))
                else:
                    verification_results['academic_info'].append((display_name, False, cert_val, db_val))
            else:
                if str(cert_val).upper() == str(db_val).upper():
                    verification_results['academic_info'].append((display_name, True, cert_val, db_val))
                else:
                    verification_results['academic_info'].append((display_name, False, cert_val, db_val))
    
    # Subject Marks Verification (Critical for tampering detection)
    subject_mappings = {
        'environmental_science': 'Environmental Science',
        'computer_programming': 'Computer Programming',
        'electrical_science': 'Electrical Science',
        'general_english': 'General English',
        'mathematics': 'Mathematics',
        'physics': 'Physics'
    }
    
    for cert_subject, display_name in subject_mappings.items():
        if cert_subject in certificate_data['subjects']:
            cert_marks = certificate_data['subjects'][cert_subject]
            db_marks = db_record[cert_subject]
            
            if cert_marks == db_marks:
                verification_results['subject_marks'].append((display_name, True, cert_marks, db_marks))
            else:
                verification_results['subject_marks'].append((display_name, False, cert_marks, db_marks))
    
    # Date Verification
    date_checks = [
        ('issue_date', 'Issue Date'),
        ('digital_signature_date', 'Digital Signature Date'),
    ]
    
    for cert_field, display_name in date_checks:
        if certificate_data[cert_field] and db_record[cert_field]:
            cert_val = str(certificate_data[cert_field]).strip()
            db_val = str(db_record[cert_field]).strip()
            
            if cert_val == db_val:
                verification_results['dates'].append((display_name, True, cert_val, db_val))
            else:
                verification_results['dates'].append((display_name, False, cert_val, db_val))
    
    # Generate detailed report
    report_lines = []
    total_checks = 0
    passed_checks = 0
    critical_failures = []
    
    for category, results in verification_results.items():
        if results:
            report_lines.append(f"\n📊 {category.replace('_', ' ').title()} Verification:")
            for display_name, is_match, cert_val, db_val in results:
                total_checks += 1
                if is_match:
                    passed_checks += 1
                    report_lines.append(f"  ✅ {display_name}: MATCH")
                else:
                    report_lines.append(f"  ❌ {display_name}: TAMPERED!")
                    report_lines.append(f"      Certificate: {cert_val}")
                    report_lines.append(f"      Database:    {db_val}")
                    
                    # Mark critical failures
                    if category in ['subject_marks', 'academic_info']:
                        critical_failures.append(display_name)
    
    # Final verdict
    if total_checks == 0:
        return False, "❌ Insufficient data extracted from certificate for verification"
    
    success_rate = (passed_checks / total_checks) * 100
    report_lines.append(f"\n📈 Verification Summary: {passed_checks}/{total_checks} checks passed ({success_rate:.1f}%)")
    
    if critical_failures:
        report_lines.append(f"\n🚨 CRITICAL TAMPERING DETECTED in: {', '.join(critical_failures)}")
        report_lines.append("   This certificate appears to be FRAUDULENT!")
        return False, "\n".join(report_lines)
    elif success_rate >= 80:
        report_lines.append("\n✅ Certificate appears AUTHENTIC")
        return True, "\n".join(report_lines)
    else:
        report_lines.append(f"\n⚠️  Certificate has SUSPICIOUS modifications")
        report_lines.append("   Manual verification recommended")
        return False, "\n".join(report_lines)

# ==============================
# STEP 4: MAIN VERIFICATION FUNCTION
# ==============================

def verify_certificate_from_image(image_path):
    """Main function to verify certificate from image"""
    print(f"\n🔍 Starting comprehensive verification for: {image_path}")
    print("="*70)
    
    # Check if image exists
    try:
        with open(image_path, 'rb'):
            pass
    except FileNotFoundError:
        print(f"❌ Image file not found: {image_path}")
        print("Please check the file path and try again.")
        return False
    
    # Initialize OCR
    reader = initialize_ocr()
    if not reader:
        return False
    
    # Extract text from image
    print("📸 Extracting text from image...")
    extracted_texts = extract_text_from_image(image_path, reader)
    
    if not extracted_texts:
        print("❌ No text could be extracted from the image.")
        print("Possible reasons:")
        print("  - Image quality too poor")
        print("  - Text is handwritten or in unsupported format")
        print("  - Image is corrupted")
        return False
    
    print(f"✅ Extracted {len(extracted_texts)} text elements.")
    print(f"Sample texts: {extracted_texts[:5]}")
    
    # Parse certificate data
    print("\n📋 Parsing certificate data...")
    certificate_data = parse_certificate_data(extracted_texts)
    
    # Verify with database
    print("\n🔐 Verifying with database...")
    is_valid, message = verify_with_database(certificate_data)
    
    print("\n" + "="*70)
    print("📊 FINAL VERIFICATION RESULT")
    print("="*70)
    print(message)
    
    return is_valid

# ==============================
# STEP 5: DISPLAY SAMPLE DATABASE
# ==============================

def display_database_contents():
    """Display current database contents"""
    print("\n📂 CURRENT DATABASE CONTENTS")
    print("="*70)
    
    cursor.execute("SELECT * FROM marksheets")
    records = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    
    for record in records:
        student_data = dict(zip(columns, record))
        print(f"\n👤 {student_data['student_name']} ({student_data['roll_no']})")
        print(f"    Father: {student_data['father_name']}")
        print(f"    Institution: {student_data['institution_name']}")
        print(f"    APAAR ID: {student_data['apaar_id']}")
        print(f"    Reg No: {student_data['reg_no']}")
        print(f"    SGPA: {student_data['sgpa']}, CGPA: {student_data['cgpa']}")
        print(f"    Issue Date: {student_data['issue_date']}")
        print(f"    Subjects: ENV={student_data['environmental_science']}, "
              f"COMP={student_data['computer_programming']}, "
              f"ELEC={student_data['electrical_science']}, "
              f"ENG={student_data['general_english']}, "
              f"MATH={student_data['mathematics']}, "
              f"PHY={student_data['physics']}")

# Display current database contents
display_database_contents()

# ==============================
# USAGE EXAMPLE
# ==============================

print("\n" + "="*70)
print("📋 USAGE INSTRUCTIONS")
print("="*70)
print("To verify a certificate image, use:")
print("verify_certificate_from_image('path_to_your_certificate_image.jpg')")
print("\nSupported image formats: JPG, PNG, JPEG, BMP, TIFF")
print("\nThe system will detect tampering in:")
print("  ✓ Student personal information")
print("  ✓ Subject marks and grades")
print("  ✓ SGPA/CGPA values")
print("  ✓ Issue dates and signatures")
print("  ✓ Academic year and semester")

# TEST YOUR IMAGES HERE - Uncomment and modify paths as needed:

# Test with Ved Changani's certificate
#verify_certificate_from_image('yashvi_sem1.jpg')

# Test with tampered certificate (should detect fraud)
verify_certificate_from_image('ved_certificate_tampered.jpg')
 
# Test with another certificate  
#verify_certificate_from_image('ved_certificate.jpg')

# ==============================
# CLOSE CONNECTION
# ==============================
# Note: Keep connection open for interactive use
# Uncomment the line below to close connection when done
# conn.close()