import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from datetime import date
from psycopg2 import Error as Psycopg2Error
import datetime
# --- Database Utility Class ---
class PostgresqlDB:
    def __init__(self, user_name, password, host, port, db_name):
        self.user_name = user_name
        self.password = password
        self.host = host
        self.port = port
        self.db_name = db_name
        self.engine = self.create_db_engine()

    def create_db_engine(self):
        try:
            db_uri = f"postgresql+psycopg2://{self.user_name}:{self.password}@{self.host}:{self.port}/{self.db_name}"
            return create_engine(db_uri)
        except Exception as err:
            raise RuntimeError(f'Failed to establish connection -- {err}') from err

    def execute_dql_commands(self, stmnt, values=None):
        try:
            with self.engine.connect() as conn:
                if values is not None:
                    result = conn.execute(text(stmnt), values)
                else:
                    result = conn.execute(text(stmnt))
            return result
        except Exception as err:
            print(f'Failed to execute dql commands -- {err}')

    def execute_ddl_and_dml_commands(self, stmnt, values=None):
        connection = self.engine.connect()
        trans = connection.begin()
        try:
            if values is not None:
                result = connection.execute(text(stmnt), values)
            else:
                result = connection.execute(text(stmnt))
            trans.commit()
            connection.close()
            print('Command executed successfully.')
        except Exception as err:
            trans.rollback()
            print(f'Failed to execute ddl and dml commands -- {err}')
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    class SimpleDB:
        def __init__(self, database_url):
            self.engine = create_engine(database_url)
        
        def execute_dql_commands(self, stmnt, values=None):
            try:
                with self.engine.connect() as conn:
                    if values is not None:
                        result = conn.execute(text(stmnt), values)
                    else:
                        result = conn.execute(text(stmnt))
                return result
            except Exception as err:
                print(f'Failed to execute dql commands -- {err}')
        
        def execute_ddl_and_dml_commands(self, stmnt, values=None):
            connection = self.engine.connect()
            trans = connection.begin()
            try:
                if values is not None:
                    result = connection.execute(text(stmnt), values)
                else:
                    result = connection.execute(text(stmnt))
                trans.commit()
                connection.close()
                print('Command executed successfully.')
            except Exception as err:
                trans.rollback()
                print(f'Failed to execute ddl and dml commands -- {err}')
    
    db = SimpleDB(DATABASE_URL)
    engine = db.engine
else:
    USER_NAME = 'postgres'
    PASSWORD = 'postgres'
    PORT = 5432
    DATABASE_NAME = 'UMS_final'
    HOST = 'localhost'
    
    db = PostgresqlDB(user_name=USER_NAME,
                      password=PASSWORD,
                      host=HOST,
                      port=PORT,
                      db_name=DATABASE_NAME)
    engine = db.engine
registration_status = {
    'student_enrollment': False,
    'professor_approval': False
}

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = 'your_secret_key' 

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        # For this implementation, the username field stores the user ID.
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        # Query the UserLogin table for matching credentials
        query = """
            SELECT * FROM UserLogin 
            WHERE userId = :user_id AND role = :role AND password = :password
        """
        result = db.execute_dql_commands(query, {
            'user_id': user_id,
            'role': role,
            'password': password
        })
        row = result.fetchone()
        
        if row:
            session['role'] = role
            # Set the database role for the current connection
            # with engine.connect() as conn:
            #     conn.execute(text(f"SET ROLE {role}"))
                
            # Redirect based on role
            if role == 'admin':
                session['username'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            elif role == 'student':
                query = "SELECT studentName FROM Students WHERE studentId = :user_id"
                session['username'] = db.execute_dql_commands(query, {'user_id': user_id}).fetchone()[0]
                session['user_id'] = user_id
                return redirect(url_for('student_dashboard', username=session.get('username')))
            
            elif role == 'professor':
                query=f"""
                    SELECT professorName FROM Professors WHERE professorId= {user_id};
                """
                session['username'] =  db.execute_dql_commands(query).fetchone()[0]
                session['user_id'] = user_id
                return redirect(url_for('professor_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        role = request.form.get('role')
        user_id = request.form.get('user_id')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('change_password'))
        
        # Validate current credentials
        query = """
            SELECT * FROM UserLogin 
            WHERE userId = :user_id AND role = :role AND password = :password
        """
        result = db.execute_dql_commands(query, {
            'user_id': user_id,
            'role': role,
            'password': old_password
        })
        user = result.fetchone()
        
        if not user:
            flash('Invalid credentials')
            return redirect(url_for('change_password'))
        
        # Update password
        update_query = """
            UPDATE UserLogin 
            SET password = :new_password 
            WHERE userId = :user_id AND role = :role
        """
        db.execute_ddl_and_dml_commands(update_query, {
            'new_password': new_password,
            'user_id': user_id,
            'role': role
        })
        
        flash('Password changed successfully!', "success")
        return redirect(url_for('login'))
    
    return render_template('change_password.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('./admin/admin.html', username=session.get('username'))

@app.route('/student_dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    return render_template('/student/student.html', username=session.get('username'))

@app.route('/professor_dashboard')
def professor_dashboard():
    if session.get('role') != 'professor':
        return redirect(url_for('login'))
    return render_template('professor.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/student/course_registration', methods=['GET'])
def course_registration():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    if request.args.get('registration_closed'):
        flash("Course Registration for student is not open yet", "warning")
    return render_template("./student/course_registration.html", username=session.get("username"))

@app.route('/student/courses', methods=['GET'])
def view_courses():
    if session.get('role') != 'student':
        return redirect(url_for("login"))

    user_id = session.get('user_id')
    if not user_id:
        flash('Session expired. Please login again.')
        return redirect(url_for('login'))

    student_query = """
        SELECT 
            departmentId as "departmentId", 
            dateOfJoining as "dateOfJoining",
            dateOfGraduation as "dateOfGraduation"
        FROM Students
        WHERE studentId = :student_id
    """
    student_row = db.execute_dql_commands(student_query, {'student_id': user_id}).fetchone()
    if not student_row:
        flash('Student information not found.')
        return redirect(url_for('student_dashboard'))

    student_dept, date_of_joining, date_of_graduation = student_row

    if date_of_graduation is None:
        terms_query = """
            SELECT 
                termId as "termId", 
                termName as "termName"
            FROM AcademicTerm
            ORDER BY startDate DESC
        """
        query_params = {'date_of_joining': date_of_joining}
    else:
        terms_query = """
            SELECT 
                termId as "termId", 
                termName as "termName"
            FROM AcademicTerm
            WHERE endDate <= :date_of_graduation
            ORDER BY startDate DESC
        """
        query_params = {'date_of_joining': date_of_joining, 'date_of_graduation': date_of_graduation}

    terms_result = db.execute_dql_commands(terms_query, query_params)
    terms = terms_result.mappings().all()

    selected_term_id = request.args.get('term_id')

    if selected_term_id:
        courses_result = db.execute_dql_commands(
            "SELECT * FROM get_approved_courses_from_view(:sid, :tid)",
            {'sid': user_id, 'tid': selected_term_id}
        )
    else:
        courses_result = None

    courses = courses_result.mappings().all() if courses_result else []

    return render_template(
        "./student/courses.html",
        username=session.get('username'),
        courses=courses,
        terms=terms,
        selected_term_id=int(selected_term_id) if selected_term_id else None
    )

@app.route("/student/profile")
def view_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    if not user_id:
        flash('Session expired. Please login again.')
        return redirect(url_for('login'))
    
    student_query = """
        SELECT 
            studentId AS "studentId",
            studentName AS "studentName",
            degreeId AS "degreeId",
            departmentId AS "departmentId",
            dateOfJoining AS "dateOfJoining",
            gender,
            dob,
            graduationStatus AS "graduationStatus"
        FROM Students
        WHERE studentId = :student_id
    """
    
    student_result = db.execute_dql_commands(student_query, {'student_id': user_id})
    student = student_result.mappings().first()
    
    if not student:
        flash('Student information not found')
        return redirect(url_for('student_dashboard'))
    
    dept_query = """
        SELECT deptName AS "deptName"
        FROM Department
        WHERE departmentId = :dept_id
    """
    dept_result = db.execute_dql_commands(dept_query, {'dept_id': student['departmentId']})
    dept_row = dept_result.mappings().first()
    department_name = dept_row['deptName'] if dept_row else "Not assigned"
    
    degree_query = """
        SELECT degreeName AS "degreeName"
        FROM Degree
        WHERE degreeId = :degree_id
    """
    degree_result = db.execute_dql_commands(degree_query, {'degree_id': student['degreeId']})
    degree_row = degree_result.mappings().first()
    degree_name = degree_row['degreeName'] if degree_row else "Not assigned"
    
    return render_template(
        './student/profile.html', 
        username=session.get('username'),
        student=student,
        department_name=department_name,
        degree_name=degree_name
    )

@app.route('/student/course_registration/add_courses', methods=['GET', 'POST'])
def add_courses():
    if registration_status["student_enrollment"]:

        if session.get('role') != 'student':
            return redirect(url_for('login'))

        user_id = session.get('user_id')
        if not user_id:
            flash('Session expired. Please log in again.', 'warning')
            return redirect(url_for('login'))

        # POST logic (add/drop)
        if request.method == 'POST':
            offering_id = request.form['offering_id']
            action = request.form.get('action')

            if action == 'add':
                dup = db.execute_dql_commands(
                    "SELECT status FROM Enrollment WHERE studentId = :sid AND offeringId = :oid",
                    {'sid': user_id, 'oid': offering_id}
                ).fetchone()

                if dup and dup[0] != 'Dropped':
                    return redirect(url_for('add_courses'))

                if dup and dup[0] == 'Dropped':
                    db.execute_ddl_and_dml_commands(
                        '''
                        UPDATE Enrollment
                        SET status = 'Pending', enrollmentDate = :edate
                        WHERE studentId = :sid AND offeringId = :oid
                        ''',
                        {'sid': user_id, 'oid': offering_id, 'edate': date.today()}
                    )
                else:
                    maxid_row = db.execute_dql_commands("SELECT COALESCE(MAX(enrollmentId),0) FROM Enrollment").fetchone()
                    next_id = maxid_row[0] + 1
                    db.execute_ddl_and_dml_commands(
                        '''
                        INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
                        VALUES (:eid, :sid, :oid, :edate, 'Pending')
                        ''',
                        {'eid': next_id, 'sid': user_id, 'oid': offering_id, 'edate': date.today()}
                    )            

            elif action == 'drop':
                db.execute_ddl_and_dml_commands(
                    '''
                    UPDATE Enrollment
                    SET status = 'Dropped'
                    WHERE studentId = :sid AND offeringId = :oid AND status = 'Pending'
                    ''',
                    {'sid': user_id, 'oid': offering_id}
                )
                return redirect(url_for('add_courses'))

        # GET logic
        today = date.today()
        term_row = db.execute_dql_commands(
            "SELECT termId FROM AcademicTerm WHERE startDate < :today AND endDate > :today",
            {'today': today}
        ).fetchone()

        courses = []
        if term_row:
            term_id = term_row[0]
            row = db.execute_dql_commands("""
                SELECT COALESCE(SUM(c.credits), 0)
                FROM Enrollment e
                JOIN CourseOffering co ON e.offeringId = co.offeringId
                JOIN Courses c ON co.courseId = c.courseId
                WHERE e.studentId = :sid
                AND (e.status = 'Pending' OR e.status = 'Approved')
                AND co.termId   = :tid
            """, {'sid': user_id, 'tid': term_id}).fetchone()
            pending_credits = row[0]

            courses = db.execute_dql_commands("""
                SELECT * FROM getAddDropCourses(:uid, :tid)
            """, {'uid': user_id, 'tid': term_id}).mappings().all()

            courses = [dict(c) for c in courses]
            for course in courses:
                course["can_add"] = (not course["enrollmentStatus"] or course["enrollmentStatus"] == "Dropped") and not course["previousTermName"]
                course["can_drop"] = (course["enrollmentStatus"] == "Pending") and not course["previousTermName"]

        return render_template('student/add_courses.html', username=session['username'], courses=courses, current_credits=pending_credits)
    else:
        return  redirect(url_for('course_registration', registration_closed=True))

@app.route('/student/course_registration/registration_log')
def registration_log():
    # 1. Ensure student
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    student_id = session.get("user_id")
    if not student_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("login"))

    today = date.today()

    term_row = db.execute_dql_commands(
        """
        SELECT termId, termName
          FROM AcademicTerm
         WHERE :today BETWEEN startDate AND endDate
        """,
        {"today": today}
    ).fetchone()

    if not term_row:
        flash("No active academic term at the moment.", "info")
        return render_template(
            "student/registration_log.html",
            username=session["username"],
            courses=[],
            terms=[],
            selected_term_id=None
        )

    term_id, term_name = term_row
    terms = [{"termId": term_id, "termName": term_name}]

    # 3. Fetch all enrollments via our new function
    rows = db.execute_dql_commands(
        "SELECT * FROM get_registration_log(:sid, :term_id)",
        {"sid": student_id, "term_id": term_id}
    ).mappings().all()

    courses = [dict(r) for r in rows]
    return render_template(
        "student/registration_log.html",
        username=session["username"],
        courses=courses,
        terms=terms,
        selected_term_id=term_id
    )

from flask import (
    session, redirect, url_for,
    request, render_template
)

@app.route('/student/grades')
def view_grades():
    # 1) Auth guard
    if session.get("role") != "student":
        return redirect(url_for("login"))

    student_id       = session.get("user_id")
    username         = session.get("username")
    selected_term_id = request.args.get("term_id", type=int)
    selected_term_name = None

    # 2) If a term is selected, fetch its name
    if selected_term_id is not None:
        term_name_sql = """
            SELECT "termName"
              FROM "AcademicTerm"
             WHERE "termId" = :tid
        """
        try:
            row = db.execute_dql_commands(term_name_sql, {"tid": selected_term_id}).fetchone()
            selected_term_name = row[0] if row else None
        except Exception as e:
            print(f"[Grades] Error fetching term name: {e}")

    # 3) Load dropdown terms
    terms = []
    try:
        tq = """
            SELECT termId, termName
              FROM AcademicTerm
             ORDER BY termId DESC
        """
        cur = db.execute_dql_commands(tq)
        for term_row in (cur.fetchall() if cur else []):
            terms.append({
                "term_id":   term_row[0],
                "term_name": term_row[1]
            })
    except Exception as e:
        print(f"[Grades] Error fetching terms: {e}")

    # 4) Initialize outputs
    grades = []
    sgpa   = None
    cgpa   = None

    if selected_term_id is not None:
        # 5) Fetch per-course details
        try:
            sql = "SELECT * FROM get_term_grades(:sid, :tid)"
            cur = db.execute_dql_commands(sql, {"sid": student_id, "tid": selected_term_id})
            rows = cur.fetchall() if cur else []
            for (
                course_id, course_name, credits,
                dept_name, professor_name, marks,
                letter_grade, grade_point, course_type
            ) in rows:
                grades.append({
                    "courseId":      course_id,
                    "courseName":    course_name,
                    "credits":       credits,
                    "deptName":      dept_name,
                    "professorName": professor_name,
                    "marks":         marks,
                    "grade":         letter_grade,
                    "gradePoint":    grade_point,
                    "courseType":    course_type
                })
        except Exception as e:
            print(f"[Grades] Error fetching term grades: {e}")

        # 6) Compute SGPA
        try:
            sql = "SELECT get_sgpa(:sid, :tid)"
            row = db.execute_dql_commands(sql, {"sid": student_id, "tid": selected_term_id}).fetchone()
            if row and row[0] is not None:
                sgpa = round(row[0], 2)
        except Exception as e:
            print(f"[Grades] Error fetching SGPA: {e}")

        # 7) Compute CGPA
        try:
            sql = "SELECT get_cgpa(:sid, :tid)"
            row = db.execute_dql_commands(sql, {"sid": student_id, "tid": selected_term_id}).fetchone()
            if row and row[0] is not None:
                cgpa = round(row[0], 2)
        except Exception as e:
            print(f"[Grades] Error fetching CGPA: {e}")

    # 8) Render
    return render_template(
        "student/grades.html",
        username=username,
        terms=terms,
        selected_term_id=selected_term_id,
        selected_term_name=selected_term_name,
        grades=grades,
        sgpa=sgpa,
        cgpa=cgpa
    )

def calculate_grade(marks):
    if marks >= 91 and marks <= 100:
        return "S", 10
    elif marks >= 81 and marks <= 90:
        return "A", 9
    elif marks >= 71 and marks <= 80:
        return "B", 8
    elif marks >= 61 and marks <= 70:
        return "C", 7
    elif marks >= 51 and marks <= 60:
        return "D", 6
    elif marks >= 35 and marks <= 50:
        return "E", 5
    else:
        return "F", 0

@app.route('/professor/pending_registrations/<int:offering_id>', methods=['GET', 'POST'])
def professor_pending_students(offering_id):
    """
    Displays students with 'Pending' enrollment status for a specific course offering
    and handles approval/rejection via POST requests, including capacity check.
    """
    # --- GET Request and Initial Authorization ---
    if session.get('role') != 'professor':
        flash('Access denied. Please log in as a professor.', 'warning')
        return redirect(url_for('login'))
    
    if registration_status['professor_approval']:
        professor_id = session.get('user_id')
        if not professor_id:
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('login'))

        # Get course offering details
        details_query = """
            SELECT
                c.courseName AS "courseName",
                at.termName  AS "termName",
                at.termId    AS "termId",
                co.professorId AS "professorId",
                co.maxCapacity AS "maxCapacity"
            FROM CourseOffering co
            JOIN Courses c ON co.courseId = c.courseId
            JOIN AcademicTerm at ON co.termId = at.termId
            WHERE co.offeringId = :offering_id
        """
        course_details = db.execute_dql_commands(details_query, {'offering_id': offering_id}).mappings().first()

        if not course_details:
            flash('Course offering not found.', 'danger')
            return redirect(url_for('professor_dashboard'))

        # Check if professor is authorized for this course
        if course_details['professorId'] != int(professor_id):
            flash('You are not authorized to manage this course offering.', 'danger')
            return redirect(url_for('professor_dashboard'))

        # --- Handle POST Request (Approve/Reject) ---
        if request.method == 'POST':
            try:
                enrollment_id_to_update = int(request.form.get('enrollment_id'))
                action = request.form.get('action')  # 'approve' or 'reject'

                if not enrollment_id_to_update or action not in ['approve', 'reject']:
                    flash('Invalid action or enrollment ID provided.', 'warning')
                    return redirect(url_for('professor_pending_students', offering_id=offering_id))

                if action == 'approve':
                    # First check capacity using SQL function
                    capacity_check_sql = "SELECT CheckCourseCapacity(:offering_id);"
                    result = db.execute_dql_commands(capacity_check_sql, {'offering_id': offering_id}).scalar()
                    
                    # Convert result to boolean if needed
                    is_space_available = bool(result)
                    
                    if is_space_available:
                        # Approve enrollment - trigger will handle StudentGrades creation
                        update_sql = """
                            UPDATE Enrollment
                            SET status = 'Approved'
                            WHERE enrollmentId = :enrollment_id
                            AND offeringId = :offering_id
                            AND status = 'Pending'
                        """
                        db.execute_ddl_and_dml_commands(
                            update_sql,
                            {'enrollment_id': enrollment_id_to_update, 'offering_id': offering_id}
                        )
                        flash('Enrollment successfully approved. Student grade record created.', 'success')
                    else:
                        flash('Cannot approve enrollment: Course capacity reached.', 'warning')
                
                elif action == 'reject':
                    # Reject enrollment
                    update_sql = """
                        UPDATE Enrollment
                        SET status = 'Rejected'
                        WHERE enrollmentId = :enrollment_id
                        AND offeringId = :offering_id
                        AND status = 'Pending'
                    """
                    db.execute_ddl_and_dml_commands(
                        update_sql,
                        {'enrollment_id': enrollment_id_to_update, 'offering_id': offering_id}
                    )
                    flash('Enrollment successfully rejected.', 'success')

            except ValueError:
                flash('Invalid Enrollment ID format.', 'danger')
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')

            return redirect(url_for('professor_pending_students', offering_id=offering_id))

        # Get pending students for this offering
        pending_students_sql = """
            SELECT
                e.enrollmentId AS "enrollmentId",
                s.studentId    AS "studentId",
                s.studentName  AS "studentName",
                e.enrollmentDate AS "enrollmentDate"
            FROM Enrollment e
            JOIN Students s ON e.studentId = s.studentId
            WHERE e.offeringId = :offering_id
            AND e.status     = 'Pending'
            ORDER BY s.studentName
        """
        pending_students = db.execute_dql_commands(pending_students_sql, {'offering_id': offering_id}).mappings().all()
        
        # Get current enrollment count for display
        enrollment_count_sql = """
            SELECT COUNT(*) AS current_count
            FROM Enrollment
            WHERE offeringId = :offering_id AND status = 'Approved'
        """
        current_enrollment = db.execute_dql_commands(enrollment_count_sql, {'offering_id': offering_id}).scalar()

        return render_template(
            './professor_pending_students.html',
            username=session.get('username'),
            course_name=course_details['courseName'],
            term_name=course_details['termName'],
            term_id=course_details['termId'],
            offering_id=offering_id,
            pending_students=pending_students,
            current_enrollment=current_enrollment,
            max_capacity=course_details['maxCapacity'],
            page_title=f"Pending Enrollments - {course_details['courseName']}"
        )
    else:
        return redirect(url_for('professor_pending_registrations', prof_reg_flag=True))

@app.route('/professor/courses_for_grading', methods=['GET'])
def courses_for_grading():
    if session.get('role') != 'professor':
        return redirect(url_for('login'))

    professor_id = session.get('user_id')
    # Find the active term (where today falls between startDate and endDate)
    term_query = """
        SELECT termId, termName
        FROM AcademicTerm
        order by termId desc
        LIMIT 1
    """
    term = db.execute_dql_commands(term_query).mappings().first()
    if not term:
        flash('No active term found.')
        return redirect(url_for('professor_dashboard'))

    # Fetch distinct offerings (courses) taught by professor in this term
    courses_query = """
        SELECT DISTINCT
            co.offeringId AS offeringId,
            c.courseid     AS courseId,
            c.coursename   AS courseName,
            c.coursetype   as courseType,
            c.credits      AS credits,
            d.deptname     AS deptName,
            co.termId      As termId
        FROM CourseOffering co
        JOIN Courses c    ON co.courseId    = c.courseId
        JOIN Department d ON c.departmentId = d.departmentId
        WHERE co.professorId = :prof_id
          AND co.termId      = :term_id
    """
    courses = db.execute_dql_commands(courses_query, {
        'prof_id':  professor_id,
        'term_id':  term['termid']
    }).mappings().all()
    print(courses)
    return render_template(
        './courses_for_grading.html',
        username   = session['username'],
        term       = term,
        courses    = courses
    )

from flask import Flask, render_template, request, redirect, url_for, session, flash
from decimal import Decimal, InvalidOperation # Import Decimal for grade handling




@app.route('/professor/grade/<int:offering_id>', methods=['GET', 'POST'])
def grade_students(offering_id):
    """
    Displays approved students for grading, handles grade updates,
    and shows class statistics by calling database functions.
    """
    # --- Authorization and Basic Setup ---
    if session.get('role') != 'professor':
        flash('Access denied. Please log in as a professor.', 'warning')
        return redirect(url_for('login'))

    professor_id = session.get('user_id')
    if not professor_id:
        flash('Session expired. Please login again.', 'warning')
        return redirect(url_for('login'))

    # --- Verify professor teaches this offering & Get Course Details ---
    details_query = """
        SELECT
            c.courseName AS "courseName",
            at.termName  AS "termName",
            co.professorId AS "professorId"
        FROM CourseOffering co
        JOIN Courses c ON co.courseId = c.courseId
        JOIN AcademicTerm at ON co.termId = at.termId
        WHERE co.offeringId = :offering_id
    """
    course_details_result = db.execute_dql_commands(details_query, {'offering_id': offering_id}).mappings().first()

    if not course_details_result:
        flash('Course offering not found.', 'danger')
        return redirect(url_for('professor_dashboard'))

    course_details = dict(course_details_result)

    if course_details['professorId'] != int(professor_id):
        flash('You are not authorized to manage this course offering.', 'danger')
        return redirect(url_for('professor_dashboard'))

    # --- Handle POST Request (Grade Submission) ---
    if request.method == 'POST':
        grades_updated_count = 0
        grades_error_count = 0

        for key, value in request.form.items():
            if key.startswith('grade_'):
                try:
                    enrollment_id = int(key.split('_')[1])
                    grade_value_str = value.strip()

                    if grade_value_str:
                        try:
                            new_grade = float(grade_value_str)
                            if 0 <= new_grade <= 100:
                                # Check if enrollment is valid and approved before attempting update/insert
                                enrollment_check_sql = """
                                   SELECT 1 FROM Enrollment
                                   WHERE enrollmentId = :enrollment_id AND offeringId = :offering_id AND status = 'Approved'
                                """
                                is_valid_enrollment = db.execute_dql_commands(enrollment_check_sql, {'enrollment_id': enrollment_id, 'offering_id': offering_id}).scalar_one_or_none()

                                if is_valid_enrollment:
                                    # Use UPSERT logic (Example: separate UPDATE then INSERT if not exists)
                                    # NOTE: This is NOT atomic without a transaction. Real UPSERT preferred.
                                    update_sql = """
                                        UPDATE StudentGrades SET grade = :new_grade WHERE enrollmentId = :enrollment_id;
                                    """
                                    insert_sql = """
                                        INSERT INTO StudentGrades (enrollmentId, grade)
                                        SELECT :enrollment_id, :new_grade
                                        WHERE NOT EXISTS (SELECT 1 FROM StudentGrades WHERE enrollmentId = :enrollment_id);
                                    """
                                    # Execute update, then potentially insert
                                    update_result = db.execute_ddl_and_dml_commands(update_sql, {'new_grade': new_grade, 'enrollment_id': enrollment_id})
                                    # Check if update affected rows, if not, try insert (depends on db helper capability)
                                    # Simplified: Assume success for now, refine if needed
                                    db.execute_ddl_and_dml_commands(insert_sql, {'new_grade': new_grade, 'enrollment_id': enrollment_id})
                                    grades_updated_count += 1
                                else:
                                    flash(f'Cannot update grade for invalid or non-approved enrollment ID {enrollment_id}.', 'danger')
                                    grades_error_count += 1
                                    continue # Skip to next item

                            else:
                                flash(f'Invalid grade "{grade_value_str}" for enrollment ID {enrollment_id}. Must be between 0 and 100.', 'warning')
                                grades_error_count += 1
                        except ValueError:
                            flash(f'Invalid input "{grade_value_str}" for enrollment ID {enrollment_id}. Grade must be a number.', 'warning')
                            grades_error_count += 1
                    # No grade entered, do nothing

                except (IndexError, ValueError):
                    flash(f'Error processing form field "{key}". Invalid format.', 'danger')
                    grades_error_count += 1

        if grades_updated_count > 0 and grades_error_count == 0:
            flash(f'Successfully updated {grades_updated_count} grade(s).', 'success')
        elif grades_updated_count == 0 and grades_error_count == 0:
            flash('No valid grades were submitted for update.', 'info')

        return redirect(url_for('grade_students', offering_id=offering_id))

    # --- Handle GET Request ---

    # Fetch Students for Grading
    students_to_grade_sql = """
        SELECT
            e.enrollmentId AS "enrollmentId",
            s.studentId    AS "studentId",
            s.studentName  AS "studentName",
            sg.grade       AS "currentGrade"
        FROM Enrollment e
        JOIN Students s ON e.studentId = s.studentId
        LEFT JOIN StudentGrades sg ON e.enrollmentId = sg.enrollmentId
        WHERE e.offeringId = :offering_id
          AND e.status = 'Approved'
        ORDER BY s.studentName
    """
    enrolled_students = db.execute_dql_commands(students_to_grade_sql, {'offering_id': offering_id}).mappings().all()

    # --- NEW: Fetch Class Statistics using DB Functions ---
    # Ensure the function names match EXACTLY what you created in your database
    stats_sql = """
        SELECT
            GetCourseAverageGrade(:offering_id) AS "averageGrade",
            GetCourseStdDevGrade(:offering_id) AS "stdDevGrade",
            CountGradedStudents(:offering_id) AS "gradedCount"
        -- No FROM clause needed here for most DBs when selecting function results
        -- Some might require FROM DUAL or a dummy table if functions can't be selected directly
    """
    stats_result = db.execute_dql_commands(stats_sql, {'offering_id': offering_id}).mappings().first()

    # Process stats results safely
    average_grade = None
    std_dev_grade = None
    graded_count = 0

    if stats_result:
        # Functions might return None/NULL directly
        average_grade = stats_result.get("averageGrade")
        std_dev_grade = stats_result.get("stdDevGrade")
        graded_count = stats_result.get("gradedCount", 0) # Default to 0 if NULL

    # Convert numeric stats from potential Decimal/DB types to float for template
    # Handle None values gracefully during conversion
    if average_grade is not None:
        try:
            average_grade = float(average_grade)
        except (TypeError, ValueError):
            average_grade = None # Reset if conversion fails
            flash('Warning: Could not interpret average grade from database function.', 'warning')

    if std_dev_grade is not None:
        try:
            std_dev_grade = float(std_dev_grade)
        except (TypeError, ValueError):
            std_dev_grade = None # Reset if conversion fails
            flash('Warning: Could not interpret standard deviation from database function.', 'warning')

    # Ensure graded_count is an integer
    graded_count = int(graded_count) if graded_count is not None else 0


    return render_template(
        'professor_grading_form.html',
        username=session.get('username'),
        course_name=course_details['courseName'],
        term_name=course_details['termName'],
        offering_id=offering_id,
        students=enrolled_students,
        # Pass stats to template
        average_grade=average_grade,
        std_dev_grade=std_dev_grade,
        graded_count=graded_count, # Pass the count obtained from the function
        page_title=f"Grade Students - {course_details['courseName']}"
    )

from flask import Flask, render_template, request, redirect, url_for, session, flash

@app.route('/professor/offer-courses', methods=['GET', 'POST'])
def offer_courses_list():
    """
    GET: Displays courses from the professor's department for the current term,
         indicating which are already offered and allowing input for capacity.
    POST: Handles adding a specific course offering with capacity for the current term.
    """
    # --- Authorization ---
    if session.get('role') != 'professor':
        flash('Access denied. Please log in as a professor.', 'warning')
        return redirect(url_for('login'))

    professor_id = session.get('user_id')
    if not professor_id:
        flash('Session expired. Please login again.', 'warning')
        return redirect(url_for('login'))

    # --- Get Current Term ---
    try:
        current_term_sql = "SELECT termId, termName FROM AcademicTerm ORDER BY termId DESC LIMIT 1;"
        current_term_result = db.execute_dql_commands(current_term_sql).mappings().first()
        if not current_term_result:
            flash('No active academic term found.', 'danger')
            return redirect(url_for('professor_dashboard'))
        
        current_term = dict(current_term_result)
        current_term_id = current_term.get('termid') or current_term.get('termId')
        current_term_name = current_term.get('termname') or current_term.get('termName')
        
        if not current_term_id or not current_term_name:
            flash('Error retrieving term information.', 'danger')
            return redirect(url_for('professor_dashboard'))
    except Exception as e:
        print(f"Database error getting current term: {e}")
        flash('Error retrieving academic term information.', 'danger')
        return redirect(url_for('professor_dashboard'))

    # --- Get Professor's Department ---
    try:
        prof_dept_sql = """
            SELECT p.departmentId
            FROM Professors p
            WHERE p.professorId = :professor_id;
            """
        prof_dept_result = db.execute_dql_commands(prof_dept_sql, {'professor_id': professor_id}).mappings().first()
        if not prof_dept_result:
            flash('Could not determine your department.', 'danger')
            return redirect(url_for('professor_dashboard'))
        
        professor_dept = dict(prof_dept_result)
        professor_dept_id = professor_dept['departmentid'] or professor_dept['departmentId']
        
        if professor_dept_id is None:
            flash('Department ID not found.', 'danger')
            return redirect(url_for('professor_dashboard'))
    except Exception as e:
        print(f"Database error getting professor department: {e}")
        flash('Error retrieving department information.', 'danger')
        return redirect(url_for('professor_dashboard'))

    # --- Handle POST Request (Add Offering Button Click) ---
        # --- Handle POST Request (Add Offering Button Click) ---
    if request.method == 'POST':
        print("\n--- DEBUG: POST request received ---") # Marker

        course_to_add_id_str = request.form.get('course_id')
        max_capacity_str = request.form.get('max_capacity')
        print(f"DEBUG: Form data - course_id: {course_to_add_id_str}, max_capacity: {max_capacity_str}")

        # --- Validation ---
        course_to_add_id = None
        int_max_capacity = None
        try:
            course_to_add_id = int(course_to_add_id_str)
            int_max_capacity = int(max_capacity_str)
            if int_max_capacity <= 0:
                raise ValueError("Capacity must be positive")
            print(f"DEBUG: Validation passed - course_id: {course_to_add_id}, max_capacity: {int_max_capacity}")
        except (ValueError, TypeError):
            print(f"DEBUG: Validation FAILED.") # See if it fails here
            flash('Invalid Course ID or Max Capacity (must be a positive number).', 'danger')
            return redirect(url_for('offer_courses_list'))

        # --- Check for Duplicates (Existing Offering) ---
        try:
            print(f"DEBUG: Checking duplicates for course_id: {course_to_add_id}, term_id: {current_term_id}")
            check_existing_sql = "SELECT 1 FROM CourseOffering WHERE courseId = :course_id AND termId = :term_id;"
            existing = db.execute_dql_commands(check_existing_sql, {
                'course_id': course_to_add_id,
                'term_id': current_term_id
            }).first() # .first() is appropriate here

            if existing:
                print(f"DEBUG: Duplicate check FAILED - Course already offered.") # See if it fails here
                flash('This course is already offered in the current term.', 'warning')
                return redirect(url_for('offer_courses_list'))
            else:
                 print("DEBUG: Duplicate check PASSED - Course not offered yet.")
        except Exception as e:
            print(f"DEBUG: ERROR during duplicate check: {e}") # Catch errors here too
            flash('Error checking for existing course offerings.', 'danger')
            return redirect(url_for('offer_courses_list'))

        # --- Check Course Department ---
        try:
            print(f"DEBUG: Checking department for course_id: {course_to_add_id}, dept_id: {professor_dept_id}")
            check_course_dept_sql = "SELECT 1 FROM Courses WHERE courseId = :course_id AND departmentId = :dept_id;"
            course_in_dept = db.execute_dql_commands(check_course_dept_sql, {
                'course_id': course_to_add_id,
                'dept_id': professor_dept_id
            }).first() # .first() is appropriate here

            if not course_in_dept:
                print(f"DEBUG: Department check FAILED - Course not in professor's department.") # See if it fails here
                flash('Cannot offer a course outside your department.', 'danger')
                return redirect(url_for('offer_courses_list'))
            else:
                 print("DEBUG: Department check PASSED.")
        except Exception as e:
            print(f"DEBUG: ERROR during department check: {e}") # Catch errors here too
            flash('Error verifying course department.', 'danger')
            return redirect(url_for('offer_courses_list'))

        next_offering_id = None
        try:
            # Query the current maximum offeringId
            max_id_sql = "SELECT MAX(offeringId) FROM CourseOffering;"
            # .scalar() fetches the first column of the first row, or None
            current_max_id = db.execute_dql_commands(max_id_sql).scalar()

            # If the table is empty, max_id will be None. Start at 1 (or your preferred start).
            if current_max_id is None:
                next_offering_id = 1
            else:
                next_offering_id = int(current_max_id) + 1

        except Exception as e:
            print(f"Database error getting MAX(offeringId): {e}")
            flash(f'Error calculating next offering ID: {e}', 'danger')
            return redirect(url_for('offer_courses_list')) # Stop if we can't get the ID

        if next_offering_id is None: # Should not happen if logic above is correct, but safety check
             flash('Failed to determine the next offering ID.', 'danger')
             return redirect(url_for('offer_courses_list'))

        # --- Insert the new course offering (including MANUALLY calculated offeringId) ---
        insert_sql = """
            INSERT INTO CourseOffering (offeringId, courseId, termId, professorId, maxCapacity)
            VALUES (:offering_id, :course_id, :term_id, :professor_id, :max_capacity);
        """
        try:
            db.execute_ddl_and_dml_commands(insert_sql, {
                'offering_id': next_offering_id, # Pass the calculated ID
                'course_id': course_to_add_id,
                'term_id': current_term_id,
                'professor_id': professor_id,
                'max_capacity': int_max_capacity
            })


            # Fetch course name for flash message (only after potential commit)
            print("DEBUG: Fetching course name for flash message...")
            course_name_sql = "SELECT courseName FROM Courses WHERE courseId = :course_id"
            course_name_result = db.execute_dql_commands(course_name_sql, {'course_id': course_to_add_id}).scalar_one_or_none()
            course_name = course_name_result if course_name_result else f"Course ID {course_to_add_id}"

            print(f"DEBUG: INSERT seemingly successful for {course_name}.")
            flash(f'Successfully added "{course_name}" with Capacity: {int_max_capacity} for {current_term_name}.', 'success')

        except Exception as e:
            print(f"--- DEBUG: Database error during INSERT execution: {e} ---") # Make error obvious
            flash(f'Failed to add course offering due to a database error: {e}', 'danger')

        # Redirect back to the list page after POST attempt
        print("--- DEBUG: Redirecting after POST attempt ---")
        return redirect(url_for('offer_courses_list'))

    # --- Handle GET Request (Display List) ---
    else:
        # ... (Keep the GET part as is, potentially with its own debug prints if needed) ...
        # ... (rest of GET handler from your previous code) ...

        # Example of ensuring GET part is okay (replace with your full GET logic)
        print("\n--- DEBUG: Handling GET Request ---")
        # Fetch department courses
        try:
            department_courses_sql = """
                SELECT c.courseId, c.courseName
                FROM Courses c WHERE c.departmentId = :dept_id ORDER BY c.courseName;
            """
            department_courses = db.execute_dql_commands(department_courses_sql, {'dept_id': professor_dept_id}).mappings().all()
        except Exception as e:
            print(f"ERROR fetching courses in GET: {e}")
            department_courses = []
            flash("Error fetching courses list.", "danger")

        # Fetch courses already offered in the current term
        try:
            offered_in_term_sql = "SELECT co.courseId FROM CourseOffering co WHERE co.termId = :term_id;"
            offered_results = db.execute_dql_commands(offered_in_term_sql, {'term_id': current_term_id}).mappings().all()
            offered_course_ids = {row.get('courseid') or row.get('courseId') for row in offered_results if row.get('courseid') or row.get('courseId') is not None}
        except Exception as e:
            print(f"ERROR fetching offered courses in GET: {e}")
            offered_course_ids = set()
            flash("Error fetching offered courses list.", "danger")

        # Get department name
        try:
            dept_name_sql = "SELECT deptName FROM Department WHERE departmentId = :dept_id;" # Verify table/column name
            dept_name = db.execute_dql_commands(dept_name_sql, {'dept_id': professor_dept_id}).scalar_one_or_none() or "Unknown Department"
        except Exception as e:
            print(f"ERROR fetching dept name in GET: {e}")
            dept_name = "Unknown Department"

        return render_template(
            'professor_offer_courses_list.html',
            username=session.get('username'),
            current_term_name=current_term_name,
            department_name=dept_name,
            department_courses=department_courses,
            offered_course_ids=offered_course_ids,
            page_title="Offer Courses from Department"
        )

@app.route('/professor/courses', methods=['GET'])
def professor_courses():
    if session.get('role') != 'professor':
        return redirect(url_for('login'))
    
    professor_id = session.get('user_id')
    if not professor_id:
        flash('Session expired. Please login again.')
        return redirect(url_for('login'))
    terms_query = """
            SELECT 
                termId as "termId", 
                termName as "termName"
            FROM AcademicTerm
            ORDER BY startDate DESC
        """
    terms_result = db.execute_dql_commands(terms_query)
    terms = terms_result.mappings().all()

    selected_term_id = request.args.get('term_id')
    if selected_term_id:
    # Query the Courses table for courses taught by the professor.
        query = """
            SELECT 
                DISTINCT "courseId" AS "courseId", 
                "courseName" AS"courseName", 
                "credits" AS "credits", 
                "deptName" AS "deptName", 
                "termName" AS "termName",
                "courseType" AS "courseType"
            FROM 
                vw_ProfessorCourseDetails
            WHERE 
                "professorId" = :professor_id 
            AND 
                "termId" = :selected_term_id; 
        """
        result = db.execute_dql_commands(query,
                         {'professor_id': professor_id,
                          'selected_term_id': selected_term_id})
    else :
        result = None
    courses = result.mappings().all() if result else []

    return render_template("professor_courses.html", 
                           username=session.get("username"), 
                           courses=courses,
                           terms=terms,
                           selected_term_id=int(selected_term_id) if selected_term_id else None
                           )


@app.route("/professor/profile")
def view_profile_professor():
    if session.get('role') != 'professor':
        return redirect(url_for('login'))

    professor_id = session.get('user_id')
    if not professor_id:
        flash('Session expired. Please login again.')
        return redirect(url_for('login'))

    # Get basic professor info
    professor_query = """
        SELECT 
            professorId AS "professorId",
            professorName AS "professorName",
            departmentId AS "departmentId",
            dob,
            gender
        FROM Professors
        WHERE professorId = :professor_id
    """
    professor_result = db.execute_dql_commands(professor_query, {'professor_id': professor_id})
    professor = professor_result.mappings().first()

    if not professor:
        flash('Professor information not found')
        return redirect(url_for('professor_dashboard'))

    # Get department name and head of department name
    dept_query = """
        SELECT 
            d.deptName AS "deptName",
            p.professorName AS "headName"
        FROM Department d
        LEFT JOIN Professors p ON d.headOfDeptId = p.professorId
        WHERE d.departmentId = :dept_id
    """
    dept_result = db.execute_dql_commands(dept_query, {'dept_id': professor['departmentId']})
    dept_row = dept_result.mappings().first()
    department_name = dept_row['deptName'] if dept_row else "Not assigned"
    head_name = dept_row['headName'] if dept_row and dept_row['headName'] else "Not Assigned"

    return render_template(
        './professor_profile.html',
        username=session.get('username'),
        professor=professor,
        department_name=department_name,
        head_name=head_name
    )
@app.route('/professor/pending_registrations', methods=['GET'])
def professor_pending_registrations():
    if session.get('role') != 'professor':
        return redirect(url_for('login'))
    if request.args.get('prof_reg_flag'):
        flash("Professor Approval page is not open yet", "warning")
    professor_id = session.get('user_id')
    # Find the active term (where today falls between startDate and endDate)
    term_query = """
        SELECT termId, termName
        FROM AcademicTerm
        order by termId desc
        LIMIT 1
    """
    term = db.execute_dql_commands(term_query).mappings().first()
    if not term:
        flash('No active term found.')
        return redirect(url_for('professor_dashboard'))

    # Fetch distinct offerings (courses) taught by professor in this term
    courses_query = """
        SELECT DISTINCT
            co.offeringId AS offeringId,
            c.courseid     AS courseId,
            c.coursename   AS courseName,
            c.coursetype   as courseType,
            c.credits      AS credits,
            d.deptname     AS deptName,
            co.termId      As termId
        FROM CourseOffering co
        JOIN Courses c    ON co.courseId    = c.courseId
        JOIN Department d ON c.departmentId = d.departmentId
        WHERE co.professorId = :prof_id
        AND co.termId      = :term_id
    """
    courses = db.execute_dql_commands(courses_query, {
        'prof_id':  professor_id,
        'term_id':  term['termid']
    }).mappings().all()
    print(courses)
    return render_template(
        'professor_cr.html',
        username   = session['username'],
        term       = term,
        courses    = courses
    )

@app.route('/admin_student', methods=['GET','POST'])
def admin_student():
    return render_template('./admin/student/student.html')

@app.route('/admin_course', methods=['GET','POST'])
def admin_course():
    return render_template('./admin/courses/coursepage.html')

@app.route('/admin_student/AorD_students', methods=['GET','POST'])
def AorD_students():
    return render_template('./admin/student/Addordelete_students.html')


@app.route('/admin_student/view_all_students', methods=['GET','POST'])
def view_all_students():
    # Get filter parameters from the request - as strings
    degree_filter = request.args.get('degree', 'all')
    department_filter = request.args.get('department', 'all')
    
    # print(f"DEBUG: Received filters - degree: {degree_filter}, department: {department_filter}")
    
    # Get all degrees for the dropdown menu
    degrees_query = """
        SELECT degreeId, degreeName, ugPgType 
        FROM Degree 
        ORDER BY degreeName
    """
    degrees_result = db.execute_dql_commands(degrees_query)
    degrees = []
    for row in degrees_result:
        degrees.append({
            'degreeId': row[0],
            'degreeName': row[1],
            'ugPgType': row[2]
        })
    
    # Get all departments for the dropdown menu
    departments_query = """
        SELECT departmentId, deptName 
        FROM Department 
        ORDER BY deptName
    """
    departments_result = db.execute_dql_commands(departments_query)
    departments = []
    for row in departments_result:
        departments.append({
            'departmentId': row[0],
            'deptName': row[1]
        })
    
    # Build the base query to get students with joins
    students_query = """
        SELECT 
            s.studentId,
            s.studentName,
            s.dateOfJoining,
            s.gender,
            s.dob,
            s.dateOfGraduation,
            s.graduationStatus,
            d.degreeName,
            d.ugPgType,
            dept.deptName
        FROM 
            Students s
        JOIN 
            Degree d ON s.degreeId = d.degreeId
        JOIN 
            Department dept ON s.departmentId = dept.departmentId
    """
    
    # Add where clauses based on filters
    where_clauses = []
    
    if degree_filter != 'all':
        try:
            degree_id = int(degree_filter)
            where_clauses.append(f"s.degreeId = {degree_id}")
        except ValueError:
            print(f"Invalid degree_filter value: {degree_filter}")
    
    if department_filter != 'all':
        try:
            department_id = int(department_filter)
            where_clauses.append(f"s.departmentId = {department_id}")
        except ValueError:
            print(f"Invalid department_filter value: {department_filter}")
    
    # Add WHERE clause if any filters are applied
    if where_clauses:
        students_query += " WHERE " + " AND ".join(where_clauses)
    
    # Add ordering
    students_query += " ORDER BY s.studentId"
    
    # print(f"DEBUG: Executing query: {students_query}")
    
    # Execute the query
    students_result = db.execute_dql_commands(students_query)
    
    # Convert to a list of dictionaries for easier template handling
    students_list = []
    for row in students_result:
        try:
            student = {
                'studentId': row[0],
                'studentName': row[1],
                'dateOfJoining': row[2].strftime('%d-%m-%Y') if row[2] else 'N/A',
                'gender': row[3],
                'dob': row[4].strftime('%d-%m-%Y') if row[4] else 'N/A',
                'dateOfGraduation': row[5].strftime('%d-%m-%Y') if row[5] else 'N/A',
                'graduationStatus': row[6],
                'degreeName': row[7],
                'ugPgType': row[8],
                'deptName': row[9]
            }
            students_list.append(student)
        except Exception as e:
            print(f"Error processing student row: {e}")
    
    # print(f"DEBUG: Found {len(students_list)} students")
    
    # Render the template with all necessary data
    return render_template(
        './admin/student/view_all_students.html',
        students=students_list,
        degrees=degrees,
        departments=departments,
        selected_degree=degree_filter,
        selected_department=department_filter
    )
@app.route('/admin_student/view_student/<int:student_id>')
def view_student(student_id):
    # Query to get the student details with degree and department info
    student_query = """
        SELECT 
            s.studentId,
            s.studentName,
            s.dateOfJoining,
            s.gender,
            s.dob,
            s.dateOfGraduation,
            s.graduationStatus,
            d.degreeName,
            d.ugPgType,
            dept.deptName
        FROM 
            Students s
        JOIN 
            Degree d ON s.degreeId = d.degreeId
        JOIN 
            Department dept ON s.departmentId = dept.departmentId
        WHERE
            s.studentId = :student_id
    """
    
    # Execute the query with the student_id parameter
    result = db.execute_dql_commands(student_query, {'student_id': student_id})
    
    # Check if student exists
    student_data = result.fetchone()
    if not student_data:
        flash(f"Student with ID {student_id} not found.", "danger")
        return redirect(url_for('view_all_students'))
    
    # Format the student data
    student = {
        'studentId': student_data[0],
        'studentName': student_data[1],
        'dateOfJoining': student_data[2].strftime('%d-%m-%Y') if student_data[2] else 'N/A',
        'gender': student_data[3],
        'dob': student_data[4].strftime('%d-%m-%Y') if student_data[4] else 'N/A',
        'dateOfGraduation': student_data[5].strftime('%d-%m-%Y') if student_data[5] else 'N/A',
        'graduationStatus': student_data[6],
        'degreeName': student_data[7],
        'ugPgType': student_data[8],
        'deptName': student_data[9]
    }
    
    return render_template('./admin/student/view_student.html', student=student)

@app.route('/admin_student/edit_student/<int:student_id>')
def edit_student(student_id):
    degrees = []
    departments = []
    student = None # Initialize student
    error_message = None # Initialize error message

    try:
        # Get all degrees for the dropdown
        degrees_query = "SELECT degreeId, degreeName, ugPgType FROM Degree ORDER BY degreeName"
        degrees_result = db.execute_dql_commands(degrees_query).fetchall()
        degrees = [{'degreeId': row[0], 'degreeName': row[1], 'ugPgType': row[2]} for row in degrees_result]

        # Get all departments for the dropdown
        departments_query = "SELECT departmentId, deptName FROM Department ORDER BY deptName"
        departments_result = db.execute_dql_commands(departments_query).fetchall()
        departments = [{'departmentId': row[0], 'deptName': row[1]} for row in departments_result]

        # Query to get the student details *and* required credits from Degree
        student_query = """
        SELECT
            s.studentId,
            s.studentName,
            s.degreeId,
            s.departmentId,
            s.dateOfJoining,
            s.gender,
            s.dob,
            s.dateOfGraduation,
            s.graduationStatus,
            d.totalCreditsRequired,  -- Added
            d.coreCreditsRequired    -- Added
        FROM
            Students s
        JOIN
            Degree d ON s.degreeId = d.degreeId -- Join Degree table
        WHERE
            s.studentId = :student_id
        """
        student_data = db.execute_dql_commands(student_query, {'student_id': student_id}).fetchone()

        if not student_data:
            flash(f"Student with ID {student_id} not found.", "danger")
            return redirect(url_for('view_all_students')) # Ensure this route exists
        print(type(student_id))
        # --- Calculate Achieved Credits ---
        achieved_total_credits = db.execute_dql_commands(
            "SELECT get_student_passed_credits(:sid);", {'sid': student_id}
        ).scalar() or 0 # Use scalar() or fetchone()[0], default to 0 if None

        achieved_core_credits = db.execute_dql_commands(
            "SELECT get_student_passed_core_credits(:sid);", {'sid': student_id}
        ).scalar() or 0 # Use scalar() or fetchone()[0], default to 0 if None
        # --- End Credit Calculation ---


        # Format the student data including credit info
        student = {
            'studentId': student_data[0],
            'studentName': student_data[1],
            'degreeId': student_data[2],
            'departmentId': student_data[3],
            'dateOfJoining': student_data[4].strftime('%d-%m-%Y') if student_data[4] else 'N/A',
            'dateOfJoining_raw': student_data[4].strftime('%Y-%m-%d') if student_data[4] else '',
            'gender': student_data[5],
            'dob': student_data[6].strftime('%d-%m-%Y') if student_data[6] else 'N/A',
            'dob_raw': student_data[6].strftime('%Y-%m-%d') if student_data[6] else '',
            'dateOfGraduation': student_data[7].strftime('%d-%m-%Y') if student_data[7] else 'N/A',
            'dateOfGraduation_raw': student_data[7].strftime('%Y-%m-%d') if student_data[7] else '',
            'graduationStatus': student_data[8],
            # Add credit info to the dictionary
            'requiredTotalCredits': student_data[9],
            'requiredCoreCredits': student_data[10],
            'achievedTotalCredits': achieved_total_credits,
            'achievedCoreCredits': achieved_core_credits
        }

    except Exception as e:
         error_message = f"Error loading student data: {str(e)}"
         app.logger.error(f"Error in edit_student route for ID {student_id}: {e}")
         # Flash a generic message, the specific error is passed to the template
         flash("An error occurred while loading student details.", "danger")
         # Allow rendering the template shell even if data fetching failed partially
         if student is None: student = {'studentId': student_id} # Pass ID at least
         if not degrees: degrees = []
         if not departments: departments = []


    return render_template('./admin/student/edit_student.html',
                           student=student,
                           degrees=degrees,
                           departments=departments,
                           error_message=error_message) # Pass specific error
# Update student information
@app.route('/admin_student/update_student/<int:student_id>', methods=['POST'])
def update_student(student_id):
    try:
        # Extract form data
        student_name = request.form.get('studentName')
        degree_id = request.form.get('degreeId')
        department_id = request.form.get('departmentId')
        date_of_joining = request.form.get('dateOfJoining')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        graduation_status = request.form.get('graduationStatus')
        date_of_graduation = request.form.get('dateOfGraduation') if request.form.get('dateOfGraduation') else None
        
        # Validate graduation date if status is 'Graduated'
        if graduation_status == 'Graduated' and not date_of_graduation:
            flash("Date of graduation is required for graduated students.", "danger")
            return redirect(url_for('edit_student', student_id=student_id))
        
        # Update query
        update_query = """
            UPDATE Students
            SET studentName = :student_name,
                degreeId = :degree_id,
                departmentId = :department_id,
                dateOfJoining = :date_of_joining,
                gender = :gender,
                dob = :dob,
                graduationStatus = :graduation_status,
                dateOfGraduation = :date_of_graduation
            WHERE studentId = :student_id
        """
        
        # Execute update
        db.execute_ddl_and_dml_commands(update_query, {
            'student_name': student_name,
            'degree_id': degree_id,
            'department_id': department_id,
            'date_of_joining': date_of_joining,
            'gender': gender,
            'dob': dob,
            'graduation_status': graduation_status,
            'date_of_graduation': date_of_graduation,
            'student_id': student_id
        })
        
        flash("Student information updated successfully!", "success")
        return redirect(url_for('view_student', student_id=student_id))
        
    except Exception as e:
        flash(f"Error updating student information: {str(e)}", "danger")
        return redirect(url_for('edit_student', student_id=student_id))

@app.route('/AorDstudent/add_student', methods=['GET', 'POST'])
def add_student():
    # You might want to fetch departments and degrees here for dropdowns as well
    departments = []
    degrees = []
    try:
        departments_result = db.execute_dql_commands("SELECT departmentId, deptName FROM Department").fetchall()
        departments = [{"departmentId": row[0], "deptName": row[1]} for row in departments_result]
        degrees_result = db.execute_dql_commands("SELECT degreeId, degreeName FROM Degree").fetchall()
        degrees = [{"degreeId": row[0], "degreeName": row[1]} for row in degrees_result]
    except Exception as e:
         flash(f'Error fetching departments or degrees: {str(e)}', 'error')

    if request.method == 'POST':
        try:
            # Get form data
            student_data = {
                'p_studentName': request.form['name'],
                'p_degreeId': int(request.form['degree_id']),
                'p_departmentId': int(request.form['department_id']),
                'p_dateOfJoining': request.form['join_date'],
                'p_gender': request.form['gender'],
                'p_dob': request.form['dob'],
                # Default values as per the procedure definition in the original code
                'p_dateOfGraduation': None,
                'p_graduationStatus': 'In Progress'
            }

            # Call the stored procedure using CALL
            db.execute_ddl_and_dml_commands(
                """CALL insert_student(
                       :p_studentName, :p_degreeId, :p_departmentId,
                       :p_dateOfJoining, :p_gender, :p_dob,
                       :p_dateOfGraduation, :p_graduationStatus
                   )""",
                student_data
            )

            flash('Student added successfully!', 'success')
            return redirect(url_for('add_student')) # Redirect to clear form

        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
            # Optionally, log the error: app.logger.error(f"Error adding student: {e}")

    # Pass dropdown data to the template
    return render_template('./admin/student/Add_students.html', departments=departments, degrees=degrees)


@app.route('/AorDstudent/delete_student', methods=['GET', 'POST'])
def del_student():
    if request.method == 'POST':
        try:
            p_student_id = request.form['student_id']

            if not p_student_id:
                 flash('Student ID is required.', 'warning')
                 return render_template('./admin/student/Del_students.html')

            # Call the stored procedure using CALL
            db.execute_ddl_and_dml_commands(
                "CALL delete_student(:p_student_id)",
                {'p_student_id': int(p_student_id)} # Ensure ID is an integer
            )
            flash(f'Student with ID {p_student_id} deleted successfully!', 'success')
            return redirect(url_for('del_student')) # Redirect to the same page

        except Exception as e:
            flash(f'Error deleting student: {str(e)}', 'error')
            # Optionally, log the error: app.logger.error(f"Error deleting student: {e}")

    # For GET request, just render the form
    return render_template('./admin/student/Del_students.html')


@app.route('/AorDstudent', methods=['GET'])
def AorD():
    return render_template('./admin/student/AorD.html')

@app.route('/admin_professor', methods=['GET','POST'])
def admin_professor():
    return render_template('./admin/professor/professor.html')

@app.route('/admin_professor/a_d')
def add_or_delete_professors():
    return render_template('./admin/professor/AorD_professors.html')

# —————— Professor Management ——————

@app.route('/admin_professor/view_all_professors', methods=['GET', 'POST'])
def view_all_professors():
    # get filter
    dept_filter = request.args.get('department', 'all')

    # fetch departments for dropdown
    dept_sql = "SELECT departmentId, deptName FROM Department ORDER BY deptName"
    depts = [{'departmentId': r[0], 'deptName': r[1]} for r in db.execute_dql_commands(dept_sql)]

    # base professor query
    prof_sql = """
        SELECT p.professorId,
               p.professorName,
               p.dob,
               p.gender,
               p.WorkingStatus,
               dept.deptName
        FROM Professors p
        JOIN Department dept ON p.departmentId = dept.departmentId
    """
    where = []
    if dept_filter != 'all':
        try:
            did = int(dept_filter)
            where.append(f"p.departmentId = {did}")
        except ValueError:
            pass
    if where:
        prof_sql += " WHERE " + " AND ".join(where)
    prof_sql += " ORDER BY p.professorId"

    rows = db.execute_dql_commands(prof_sql)
    profs = []
    for r in rows:
        profs.append({
            'professorId': r[0],
            'professorName': r[1],
            'dob': r[2].strftime('%d-%m-%Y'),
            'gender': r[4],
            'deptName': r[5],
            'WorkingStatus':r[3]
        })

    return render_template(
        'admin/professor/view_all_professors.html',
        professors=profs,
        departments=depts,
        selected_department=dept_filter
    )
# —————— Professor Management ——————

@app.route('/admin_professor/view_professor/<int:professor_id>')
def view_professor(professor_id):
    # fetch professor + dept
    sql = """
      SELECT p.professorId, p.professorName, p.dob, p.gender, dept.deptName
      FROM Professors p
      JOIN Department dept ON p.departmentId = dept.departmentId
      WHERE p.professorId = :pid
    """
    row = db.execute_dql_commands(sql, {'pid': professor_id}).fetchone()
    if not row:
        flash(f"Professor {professor_id} not found", "danger")
        return redirect(url_for('view_all_professors'))

    prof = {
        'professorId': row[0],
        'professorName': row[1],
        'dob': row[2].strftime('%d-%m-%Y'),
        'gender': row[3],
        'deptName': row[4]
    }

    # check if this prof is HOD
    hod_row = db.execute_dql_commands(
      "SELECT 1 FROM Department WHERE headOfDeptId = :pid",
      {'pid': professor_id}
    ).fetchone()
    is_hod = bool(hod_row)

    return render_template(
      'admin/professor/view_professors.html',
      professor=prof,
      is_hod=is_hod
    )



@app.route('/admin_professor/edit_professor/<int:professor_id>')
def edit_professor(professor_id):
    # 1) Fetch departments
    depts = [
      {'departmentId': r[0], 'deptName': r[1]}
      for r in db.execute_dql_commands(
        "SELECT departmentId, deptName FROM Department ORDER BY deptName"
      )
    ]

    # 2) Fetch professor data
    sql = """
      SELECT professorId, professorName, departmentId, dob, gender
      FROM Professors
      WHERE professorId = :pid
    """
    row = db.execute_dql_commands(sql, {'pid': professor_id}).fetchone()
    if not row:
        flash(f"Professor {professor_id} not found", "danger")
        return redirect(url_for('view_all_professors'))

    prof = {
        'professorId':    row[0],
        'professorName':  row[1],
        'departmentId':   row[2],
        'dob_raw':        row[3].strftime('%Y-%m-%d'),
        'gender':         row[4]
    }

    # 3) Check if this professor is a Head of any department
    hod_row = db.execute_dql_commands(
      "SELECT 1 FROM Department WHERE headOfDeptId = :pid",
      {'pid': professor_id}
    ).fetchone()
    is_hod = bool(hod_row)  # True if professor is HOD

    return render_template(
        'admin/professor/edit_professor.html',
        professor=prof,
        departments=depts,
        is_hod=is_hod
    )


@app.route('/admin_professor/update_professor/<int:professor_id>', methods=['POST'])
def update_professor(professor_id):
    name    = request.form['professorName']
    dob     = request.form['dob']
    gender  = request.form['gender']

    # Determine department: if HOD, keep original; otherwise accept form value
    hod_row = db.execute_dql_commands(
      "SELECT departmentId FROM Department WHERE headOfDeptId = :pid",
      {'pid': professor_id}
    ).fetchone()

    if hod_row:
        # professor is HOD → preserve original departmentId
        dept_id = db.execute_dql_commands(
          "SELECT departmentId FROM Professors WHERE professorId = :pid",
          {'pid': professor_id}
        ).fetchone()[0]
        flash("As Head of Department, your department cannot be changed.", "info")
    else:
        dept_id = request.form['departmentId']

    # Perform update
    sql = """
      UPDATE Professors
      SET professorName = :name,
          departmentId = :dept,
          dob          = :dob,
          gender       = :gender
      WHERE professorId = :pid
    """
    db.execute_ddl_and_dml_commands(sql, {
        'name':   name,
        'dept':   dept_id,
        'dob':    dob,
        'gender': gender,
        'pid':    professor_id
    })

    flash("Professor information updated successfully!", "success")
    return redirect(url_for('view_professor', professor_id=professor_id))

@app.route('/admin_professor/add_professor', methods=['GET', 'POST'])
def add_prof():
    departments = []
    try:
        # Get all departments for the dropdown
        # Assuming execute_dql_commands returns a list of tuples or similar iterable
        departments_result = db.execute_dql_commands("SELECT departmentId, deptName FROM Department").fetchall()
        # Convert to list of dictionaries for easier template handling (optional but good practice)
        departments = [{"departmentId": row[0], "deptName": row[1]} for row in departments_result]
    except Exception as e:
        flash(f'Error fetching departments: {str(e)}', 'error')

    if request.method == 'POST':
        try:
            # Get form data
            p_professorName = request.form['professor_name']
            p_departmentId = request.form['department_id']
            p_dob = request.form['dob']
            p_gender = request.form['gender']
            # p_Workingstatus = 'Active'
            # Call the stored procedure to insert the professor
            # The procedure internally calls get_next_professor_id()
            db.execute_ddl_and_dml_commands(
                "CALL insert_professor(:p_professorName, :p_departmentId, :p_dob, :p_gender)",
                {
                    'p_professorName': p_professorName,
                    'p_departmentId': int(p_departmentId), # Ensure ID is an integer
                    'p_dob': p_dob,
                    'p_gender': p_gender
                }
            )

            flash('Professor added successfully!', 'success')
            return redirect(url_for('add_prof')) # Redirect to clear form

        except Exception as e:
            # Catch potential errors (e.g., invalid departmentId, database errors)
            flash(f'Error adding professor: {str(e)}', 'error')
            # Optionally, log the error: app.logger.error(f"Error adding professor: {e}")

    # Pass departments to the template for the dropdown
    return render_template('./admin/professor/add_professor.html', departments=departments)


# @app.route('/admin_professor/del_professor', methods=['GET', 'POST'])
# def del_prof():
#     if request.method == 'POST':
#         try:
#             p_professor_id = request.form['professor_id']

#             if not p_professor_id:
#                  flash('Professor ID is required.', 'warning')
#                  return render_template('./admin/professor/delete_professor.html')

#             # Call the stored procedure to delete the professor
#             db.execute_ddl_and_dml_commands(
#                 "CALL delete_professor(:p_professor_id)",
#                 {'p_professor_id': int(p_professor_id)} # Ensure ID is an integer
#             )

#             flash(f'Professor with ID {p_professor_id} deleted successfully!', 'success')
#             return redirect(url_for('del_prof')) # Redirect to the same page (or a professor list page)

#         except Exception as e:
#             # Catch potential errors, including the EXCEPTION raised by the procedure
#             flash(f'Error deleting professor: {str(e)}', 'error')
#             # Optionally, log the error: app.logger.error(f"Error deleting professor: {e}")

#     # For GET request, just render the form
#     return render_template('./admin/professor/delete_professor.html')


@app.route('/admin_professor/del_professor', methods=['GET', 'POST'])
def del_prof():
    professor_id_to_render = None # Initialize for GET request
    if request.method == 'POST':
        p_professor_id_str = request.form.get('professor_id')
        professor_id_to_render = p_professor_id_str

        try:
            # 1. Validate Input Presence
            if not p_professor_id_str:
                 flash('Professor ID is required.', 'warning')
                 return render_template('./admin/professor/delete_professor.html', professor_id=professor_id_to_render)

            # 2. Validate Input Format (Integer)
            try:
                p_professor_id = int(p_professor_id_str)
            except ValueError:
                 flash('Invalid Professor ID format. Please enter a number.', 'danger')
                 return render_template('./admin/professor/delete_professor.html', professor_id=professor_id_to_render)

            # 3. Check if the professor is a Head of Department (HOD) directly
            hod_check_query = """
            SELECT EXISTS (
                SELECT 1
                FROM Department
                WHERE headOfDeptId = :p_professor_id
            );
            """
            # Assuming your db wrapper can execute this and return a boolean scalar
            # Adjust .scalar() based on your specific database library (e.g., .fetchone()[0])
            is_head = db.execute_dql_commands(hod_check_query, {'p_professor_id': p_professor_id}).scalar()

            # 4. If they are an HOD, flash error and stop
            if is_head:
                hod_error_text = f'Cannot mark professor {p_professor_id} as departed. They are currently assigned as a department head.'
                flash(hod_error_text, 'danger')
                # Re-render the form with the error and the entered ID
                return render_template('./admin/professor/delete_professor.html', professor_id=professor_id_to_render)

            # 5. If NOT an HOD, proceed to call the procedure to mark as departed
            # (The procedure itself might still raise other errors, but not the HOD one)
            db.execute_ddl_and_dml_commands(
                "CALL delete_professor(:p_professor_id)",
                {'p_professor_id': p_professor_id}
            )

            # 6. Success
            flash(f'Professor with ID {p_professor_id} marked as departed successfully!', 'success')
            return redirect(url_for('del_prof')) # Redirect on success

        # 7. Catch other potential exceptions (e.g., database connection errors,
        #    errors from the procedure *other* than the HOD check if any exist)
        except Exception as e:
            app.logger.error(f"Error processing professor {p_professor_id_str}: {e}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            # Re-render form even on unexpected errors
            return render_template('./admin/professor/delete_professor.html', professor_id=professor_id_to_render)

    # For GET request, just render the form
    return render_template('./admin/professor/delete_professor.html', professor_id=professor_id_to_render)




@app.route('/admin_department/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        try:
            dept_name = request.form['dept_name']

            if not dept_name:
                flash('Department Name cannot be empty.', 'warning')
                return render_template('admin/department/add_department.html') # Re-render form

            db.execute_ddl_and_dml_commands(
                "CALL insert_department(:p_deptName)",
                {'p_deptName': dept_name}
            )

            flash(f'Department "{dept_name}" added successfully!', 'success')
            return redirect(url_for('add_department')) # Redirect to clear form

        except Exception as e:
            flash(f'Error adding department: {str(e)}', 'error')

    return render_template('admin/department/department.html')

@app.route('/admin_department/add_degree', methods=['GET', 'POST'])
def add_degree():
    if request.method == 'POST':
        try:
            # Get form data
            degree_data = {
                'p_degreeName': request.form['degree_name'],
                'p_ugPgType': request.form['ug_pg_type'],
                # Convert numeric fields to integers, handle potential ValueError
                'p_maxYears': int(request.form['max_years']),
                'p_totalCreditsRequired': int(request.form['total_credits']),
                'p_coreCreditsRequired': int(request.form['core_credits'])
            }

            # Basic validation (can add more specific checks)
            if not all(degree_data.values()):
                 flash('All fields are required.', 'warning')
                 return render_template('admin/degree/add_degree.html') # Re-render form

            if degree_data['p_ugPgType'] not in ('UG', 'PG'):
                flash('Invalid Degree Type selected.', 'warning')
                return render_template('admin/degree/add_degree.html')

            if degree_data['p_maxYears'] <= 0 or \
               degree_data['p_totalCreditsRequired'] <= 0 or \
               degree_data['p_coreCreditsRequired'] < 0: # Core can be 0, but not negative
                 flash('Years and Credits must be positive numbers.', 'warning')
                 return render_template('admin/degree/add_degree.html')

            # Note: The check for core <= total is also in the procedure,
            # but catching it here can provide quicker feedback.
            if degree_data['p_coreCreditsRequired'] > degree_data['p_totalCreditsRequired']:
                flash('Core Credits cannot exceed Total Credits.', 'warning')
                return render_template('admin/degree/add_degree.html')


            # Call the stored procedure to insert the degree
            db.execute_ddl_and_dml_commands(
                """CALL insert_degree(
                        :p_degreeName, :p_ugPgType, :p_maxYears,
                        :p_totalCreditsRequired, :p_coreCreditsRequired
                   )""",
                degree_data
            )

            flash(f'Degree "{degree_data["p_degreeName"]}" added successfully!', 'success')
            return redirect(url_for('add_degree')) # Redirect to clear form

        except ValueError:
            flash('Invalid input: Years and Credits must be valid numbers.', 'error')
        except Exception as e:
            # Catch potential errors (database connection, procedure errors like the core > total check)
            flash(f'Error adding degree: {str(e)}', 'error')
            # Optionally, log the error: app.logger.error(f"Error adding degree: {e}")

    # For GET request, just render the form
    return render_template('admin/degree/degree.html')

@app.route('/courses_by_term', methods=['GET'])
def view_courses_by_term():
    terms = []
    offerings = []
    selected_term_id = None
    selected_term_name = "None" # Default display name

    try:
        # 1. Fetch all available academic terms (ordered by most recent first)
        terms_result = db.execute_dql_commands(
            "SELECT termId, termName, startDate FROM AcademicTerm ORDER BY startDate DESC"
        ).fetchall()
        # Convert to list of dictionaries for easier template access
        terms = [{"termId": row[0], "termName": row[1], "startDate": row[2]} for row in terms_result]

        # 2. Determine which term to display offerings for
        requested_term_id = request.args.get('term_id', type=int) # Get term_id from URL query parameter

        if requested_term_id:
            # If a specific term was requested via URL parameter
            selected_term_id = requested_term_id
        elif terms:
            # If no specific term requested, default to the latest term
            selected_term_id = terms[0]['termId'] # The first one due to ORDER BY

        # 3. Fetch course offerings IF a term is selected using the SQL function
        if selected_term_id:
            # Find the name of the selected term for display
            for term in terms:
                if term['termId'] == selected_term_id:
                    selected_term_name = term['termName']
                    break

            # Call the SQL function
            # Note: The exact syntax might depend slightly on your DB wrapper
            # We select the columns defined in the function's RETURNS TABLE
            offerings_result = db.execute_dql_commands(
                """SELECT offering_id, course_id, course_name, course_type,
                          ug_pg_type, credits, dept_name, professor_id,
                          professor_name, max_capacity
                   FROM get_course_offerings_by_term(:selected_term_id);
                """,
                {'selected_term_id': selected_term_id}
            ).fetchall()

            # Convert results to list of dictionaries - column names match function output
            offerings = [
                {
                    "offeringId": row[0], "courseId": row[1], "courseName": row[2],
                    "courseType": row[3], "ugPgType": row[4], "credits": row[5],
                    "deptName": row[6], "professorId": row[7], "professorName": row[8],
                    "maxCapacity": row[9]
                } for row in offerings_result
            ]

    except Exception as e:
        flash(f'Error fetching course data: {str(e)}', 'error')
        # Optionally log the error: app.logger.error(f"Error fetching courses: {e}")
        terms = [] # Prevent potential issues in template if terms fetch failed partially
        offerings = []


    return render_template(
        'admin/courses/view_course_offerings.html', # Adjust path as needed
        terms=terms,
        offerings=offerings,
        selected_term_id=selected_term_id,
        selected_term_name=selected_term_name
    )

@app.route('/course_registration_control', methods=['GET', 'POST'])
def course_registration_control():
    global registration_status # Use the global dictionary

    if request.method == 'POST':
        action = request.form.get('action') # Get which button was pressed

        if action == 'toggle_student':
            if registration_status['student_enrollment']:
                # Closing student enrollment - always allowed
                registration_status['student_enrollment'] = False
                flash('Student enrollment window CLOSED.', 'info')
            else:
                # Attempting to open student enrollment
                # RULE: Can only open if professor approval is CLOSED
                if not registration_status['professor_approval']:
                    registration_status['student_enrollment'] = True
                    # No need to explicitly close prof approval, as it's already checked to be false
                    flash('Student enrollment window OPENED.', 'info')
                else:
                    # This case should ideally be prevented by disabling the button in HTML,
                    # but handle it defensively.
                    flash('Cannot open student enrollment while professor approval is active.', 'danger')

        elif action == 'toggle_prof':
            if registration_status['professor_approval']:
                # Closing professor approval - always allowed
                registration_status['professor_approval'] = False
                flash('Professor approval window CLOSED.', 'info')
            else:
                # Attempting to open professor approval
                # RULE: Can only open if student enrollment is CLOSED
                if not registration_status['student_enrollment']:
                    registration_status['professor_approval'] = True
                     # No need to explicitly close student enrollment, as it's already checked to be false
                    flash('Professor approval window OPENED.', 'info')
                else:
                    # This case should ideally be prevented by disabling the button in HTML,
                    # but handle it defensively.
                    flash('Cannot open professor approval while student enrollment is active.', 'danger')

        return redirect(url_for('course_registration_control')) # Redirect to refresh view

    # For GET request, pass the current statuses to the template
    return render_template(
        './admin/course_registration/course_registration.html',
        student_status=registration_status['student_enrollment'],
        prof_status=registration_status['professor_approval']
    )
@app.route('/add_courses', methods=['GET', 'POST'])
def admin_add_courses():
    departments = []
    try:
        # Fetch departments for the dropdown
        dept_result = db.execute_dql_commands(
            "SELECT departmentId, deptName FROM Department ORDER BY deptName"
        ).fetchall()
        departments = [{"departmentId": row[0], "deptName": row[1]} for row in dept_result]
    except Exception as e:
        flash(f'Error fetching departments: {str(e)}', 'error')
        # Optionally log the error: app.logger.error(f"Error fetching departments: {e}")

    if request.method == 'POST':
        try:
            # Get form data
            course_data = {
                'p_courseName': request.form.get('course_name'),
                'p_departmentId': request.form.get('department_id'),
                'p_typeOfCourse': request.form.get('ug_pg_type'), # UG/PG
                'p_courseType': request.form.get('course_type'),   # Theory/Lab
                'p_credits': request.form.get('credits')
            }

            # Basic Server-side Validation
            if not all(course_data.values()):
                flash('All fields are required.', 'warning')
                return render_template('admin/courses/add_courses.html', departments=departments)

            if course_data['p_typeOfCourse'] not in ('UG', 'PG'):
                 flash('Invalid Course Level (UG/PG) selected.', 'warning')
                 return render_template('admin/courses/add_courses.html', departments=departments)

            if course_data['p_courseType'] not in ('Theory', 'Lab'):
                 flash('Invalid Course Type (Theory/Lab) selected.', 'warning')
                 return render_template('admin/courses/add_courses.html', departments=departments)

            # Convert numeric fields after checking existence
            try:
                course_data['p_departmentId'] = int(course_data['p_departmentId'])
                course_data['p_credits'] = int(course_data['p_credits'])
            except ValueError:
                 flash('Invalid number format for Department ID or Credits.', 'error')
                 return render_template('admin/courses/add_course.html', departments=departments)

            # Check credits range (though DB constraint also exists)
            if not (0 < course_data['p_credits'] <= 5):
                 flash('Credits must be between 1 and 5.', 'warning')
                 return render_template('admin/courses/add_courses.html', departments=departments)


            # Call the stored procedure to insert the course
            db.execute_ddl_and_dml_commands(
                """CALL insert_course(
                        :p_courseName, :p_departmentId, :p_typeOfCourse,
                        :p_courseType, :p_credits
                   )""",
                course_data
            )

            flash(f'Course "{course_data["p_courseName"]}" added successfully!', 'success')
            return redirect(url_for('admin_add_courses')) # Redirect to clear form

        except Exception as e:
            flash(f'Error adding course: {str(e)}', 'error')
            # Optionally log the error: app.logger.error(f"Error adding course: {e}")
            # Re-render form with departments if error occurs
            return render_template('admin/courses/add_courses.html', departments=departments)


    # For GET request, just render the form with departments
    return render_template('./admin/courses/add_courses.html', departments=departments)
# Ensure these imports are at the top (if not already present)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# Assuming 'db' is your database connection/wrapper object initialized elsewhere
# from your_db_connector import db # Example import
# Assuming 'app' is your Flask app instance initialized elsewhere
# app = Flask(__name__)
# app.secret_key = 'your secret key' # Make sure secret key is set

@app.route('/admin_department/assign_hod', methods=['GET', 'POST'])
def assign_hod_route():
    departments = []
    professors = []
    selected_department_id = None # Keep track for re-rendering form on error

    try:
        # Fetch all departments for the first dropdown
        dept_result = db.execute_dql_commands(
            "SELECT departmentId, deptName, headOfDeptId FROM Department ORDER BY deptName"
        ).fetchall()
        # Include current HOD ID for display/logic
        departments = [{"departmentId": row[0], "deptName": row[1], "headOfDeptId": row[2]} for row in dept_result]

        # Fetch all ACTIVE professors for the second dropdown (initially unfiltered)
        prof_result = db.execute_dql_commands(
            """SELECT professorId, professorName, departmentId
               FROM Professors
               WHERE WorkingStatus = 'Active' ORDER BY professorName"""
        ).fetchall()
        professors = [{"professorId": row[0], "professorName": row[1], "departmentId": row[2]} for row in prof_result]

    except Exception as e:
        flash(f'Error fetching initial data: {str(e)}', 'error')
        # Log error
        app.logger.error(f"Error fetching data for assign HOD: {e}")
        # Ensure lists are empty to avoid template errors
        departments = []
        professors = []

    if request.method == 'POST':
        try:
            dept_id_str = request.form.get('department_id')
            prof_id_str = request.form.get('professor_id')
            selected_department_id = dept_id_str # Store for potential re-render

            # --- Server-side Validation ---
            if not dept_id_str or not prof_id_str:
                flash('Both Department and Professor must be selected.', 'warning')
                return render_template('./admin/department/assign_hod.html',
                                       departments=departments, professors=professors,
                                       selected_department_id=selected_department_id)

            try:
                p_departmentId = int(dept_id_str)
                p_professorId = int(prof_id_str)
            except ValueError:
                flash('Invalid Department or Professor ID.', 'danger')
                return render_template('./admin/department/assign_hod.html',
                                       departments=departments, professors=professors,
                                       selected_department_id=selected_department_id)

            # Optional but recommended: Re-verify professor belongs to the department on server side
            # (Although the procedure does this, catching it here is cleaner)
            selected_prof = next((p for p in professors if p['professorId'] == p_professorId), None)
            if not selected_prof or selected_prof['departmentId'] != p_departmentId:
                 flash(f'Selected Professor does not belong to the selected Department or is inactive.', 'danger')
                 return render_template('./admin/department/assign_hod.html',
                                        departments=departments, professors=professors,
                                        selected_department_id=selected_department_id)
            # --- End Validation ---


            # Call the stored procedure
            db.execute_ddl_and_dml_commands(
                "CALL assign_hod(:p_departmentId, :p_professorId)",
                {'p_departmentId': p_departmentId, 'p_professorId': p_professorId}
            )

            # Find names for success message
            dept_name = next((d['deptName'] for d in departments if d['departmentId'] == p_departmentId), 'Unknown Dept')
            prof_name = selected_prof['professorName'] if selected_prof else 'Unknown Prof'

            flash(f'Successfully assigned {prof_name} as Head of {dept_name}!', 'success')
            return redirect(url_for('assign_hod_route')) # Redirect to refresh data

        except Exception as e:
            # Catch errors from the procedure (like prof not active, etc.) or DB issues
            flash(f'Error assigning Head of Department: {str(e)}', 'danger')
            app.logger.error(f"Error calling assign_hod procedure: {e}")
            # Re-render form with selected department to help user
            return render_template('./admin/department/assign_hod.html',
                                   departments=departments, professors=professors,
                                   selected_department_id=selected_department_id)


    # For GET request or if POST fails and re-renders
    return render_template('./admin/department/assign_hod.html',
                           departments=departments, professors=professors,
                           selected_department_id=selected_department_id)

@app.route('/admin/department', methods=['GET'])
def dept():
    return render_template('./admin/department/main_dept.html')


@app.route('/admin/add_term', methods=['GET', 'POST'])
def add_term():
    # Check if adding a term is currently allowed using the SQL function
    try:
        # Assumes .scalar() or similar returns a boolean from the function call
        is_add_allowed = db.execute_dql_commands("SELECT can_add_new_term();").scalar()
    except Exception as e:
        app.logger.error(f"Error checking if term can be added: {e}")
        flash("Error checking term addition permissions. Please try again later.", "danger")
        is_add_allowed = False # Default to not allowed on error

    # --- GET Request ---
    if request.method == 'GET':
        if not is_add_allowed:
            flash("Cannot add a new term until the most recently defined term has ended.", "warning")
            # Option 1: Redirect to dashboard
            # return redirect(url_for('admin_dashboard'))
            # Option 2: Render the template but disable the form / show message
            return render_template('admin/term/add_term.html', add_allowed=False)
        else:
            # Prepare data for the form (e.g., feasible years)
            current_year = datetime.date.today().year
            # Allow selecting current year up to 5 years in the future
            feasible_years = list(range(current_year, current_year + 6))
            return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)

    # --- POST Request ---
    if request.method == 'POST':
        # Re-check permission on POST for security
        if not is_add_allowed:
             flash("Term addition is currently blocked.", "danger")
             return redirect(url_for('add_term')) # Redirect back to GET which will show message

        # Get form data
        season = request.form.get('season')
        year_str = request.form.get('year')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        # --- Server-side Validation ---
        if not all([season, year_str, start_date_str, end_date_str]):
            flash("All fields are required.", "warning")
            # Need to regenerate year list for re-render
            current_year = datetime.date.today().year
            feasible_years = list(range(current_year, current_year + 6))
            return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)

        if season not in ['Spring', 'Fall', 'Summer', 'Winter']: # Add more if needed
            flash("Invalid season selected.", "warning")
            # Regenerate years list
            current_year = datetime.date.today().year
            feasible_years = list(range(current_year, current_year + 6))
            return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)

        try:
            year = int(year_str)
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

            if end_date <= start_date:
                flash("End Date must be after Start Date.", "danger")
                # Regenerate years list
                current_year = datetime.date.today().year
                feasible_years = list(range(current_year, current_year + 6))
                return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)

        except ValueError:
            flash("Invalid year or date format.", "danger")
            # Regenerate years list
            current_year = datetime.date.today().year
            feasible_years = list(range(current_year, current_year + 6))
            return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)
        # --- End Validation ---

        # Construct term name
        term_name = f"{season} {year}"

        try:
            # Call the procedure to insert the term
            db.execute_ddl_and_dml_commands(
                "CALL insert_academic_term(:name, :start, :end)",
                {'name': term_name, 'start': start_date, 'end': end_date}
            )
            flash(f"Academic Term '{term_name}' added successfully!", "success")
            return redirect(url_for('add_term')) # Redirect to clear form and re-check status

        except Exception as e:
            flash(f"Error adding academic term: {str(e)}", "danger")
            app.logger.error(f"Error calling insert_academic_term: {e}")
            # Regenerate years list on error
            current_year = datetime.date.today().year
            feasible_years = list(range(current_year, current_year + 6))
            return render_template('admin/term/add_term.html', add_allowed=True, years=feasible_years)

    # Fallback for GET if somehow missed (shouldn't happen with explicit returns)
    return render_template('admin/term/add_term.html', add_allowed=is_add_allowed)


# if __name__ == '__main__':
#     app.run(debug=True)#, host='10.32.5.70', port=5000)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
