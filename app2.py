from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from datetime import date  # Import to get current date
from psycopg2 import Error as Psycopg2Error  # for catching trigger exceptions

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

# --- DB Credentials ---
USER_NAME = 'postgres'
PASSWORD = 'postgres'
PORT = 5432
DATABASE_NAME = 'UMS_final'
HOST = 'localhost'

# Initialize the database instance
db = PostgresqlDB(user_name=USER_NAME,
                  password=PASSWORD,
                  host=HOST,
                  port=PORT,
                  db_name=DATABASE_NAME)
engine = db.engine

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key in production

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
            with engine.connect() as conn:
                conn.execute(text(f"SET ROLE {role}"))
                
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
                return redirect(url_for('professor_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))
    
    return render_template('login.html')
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html', username=session.get('username'))

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

@app.route('/student/course_registration')
def course_registration():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
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
            WHERE startDate >= :date_of_joining
            ORDER BY startDate DESC
        """
        query_params = {'date_of_joining': date_of_joining}
    else:
        terms_query = """
            SELECT 
                termId as "termId", 
                termName as "termName"
            FROM AcademicTerm
            WHERE startDate >= :date_of_joining
              AND endDate <= :date_of_graduation
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
               AND e.status    = 'Pending'
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

@app.route('/student/grades')
def view_grades():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    
    student_id = session.get("user_id")
    username = session.get("username")
    
    # Get all terms for the dropdown
    terms_query = """
        SELECT termId, termName 
        FROM AcademicTerm 
        ORDER BY termId DESC
    """
    try:
        terms_result = db.execute_dql_commands(terms_query)
        terms = []
        if terms_result is not None:
            terms = [{"term_id": row[0], "term_name": row[1]} for row in terms_result]
        else:
            # Log the issue
            print("Warning: terms_result is None")
    except Exception as e:
        # Log the exception
        print(f"Error fetching terms: {e}")
        terms = []
    
    # Get selected term from query parameters
    selected_term_id = request.args.get('term_id')
    
    # Initialize variables
    grades = []
    sgpa = 0
    cgpa = 0
    total_credits = 0
    total_grade_points = 0
    
    if selected_term_id:
        # Get course enrollments for the selected term
        enrollments_query = """
            SELECT 
                c.courseId, 
                c.courseName, 
                c.credits, 
                d.deptName, 
                t.termName, 
                p.professorName, 
                e.status, 
                sg.grade as marks, 
                c.courseType
            FROM 
                Enrollment e
            JOIN 
                CourseOffering co ON e.offeringId = co.offeringId
            JOIN 
                Courses c ON co.courseId = c.courseId
            JOIN 
                Department d ON c.departmentId = d.departmentId
            JOIN 
                AcademicTerm t ON co.termId = t.termId
            JOIN 
                Professors p ON co.professorId = p.professorId
            LEFT JOIN
                StudentGrades sg ON e.enrollmentId = sg.enrollmentId
            WHERE 
                e.studentId = :student_id AND 
                e.status = 'Approved' AND 
                t.termId = :term_id
        """
        
        try:
            term_enrollments_result = db.execute_dql_commands(
                enrollments_query, 
                {"student_id": student_id, "term_id": selected_term_id}
            )
            
            if term_enrollments_result is not None:
                # Calculate SGPA for selected term
                term_credits = 0
                term_grade_points = 0
                
                for row in term_enrollments_result:
                    course_id, course_name, credits, dept_name, term_name, professor_name, status, marks, course_type = row
                    grade, grade_point = calculate_grade(marks)
                    
                    grades.append({
                        'courseId': course_id,
                        'courseName': course_name,
                        'credits': credits,
                        'deptName': dept_name,
                        'termName': term_name,
                        'professorName': professor_name,
                        'courseType': course_type,
                        'marks': marks,
                        'grade': grade,
                        'gradePoint': grade_point
                    })
                    
                    term_credits += credits
                    term_grade_points += (credits * grade_point)
                
                # Calculate SGPA for this term
                if term_credits > 0:
                    sgpa = round(term_grade_points / term_credits, 2)
        except Exception as e:
            print(f"Error fetching enrollments: {e}")
        
        # Calculate CGPA by getting all completed courses up to this term
        cgpa_query = """
            SELECT 
                c.credits, 
                sg.grade
            FROM 
                Enrollment e
            JOIN 
                CourseOffering co ON e.offeringId = co.offeringId
            JOIN 
                Courses c ON co.courseId = c.courseId
            JOIN 
                AcademicTerm t ON co.termId = t.termId
            JOIN 
                StudentGrades sg ON e.enrollmentId = sg.enrollmentId
            WHERE 
                e.studentId = :student_id AND 
                e.status = 'Approved' AND 
                t.termId <= :term_id
        """
        
        try:
            all_enrollments_result = db.execute_dql_commands(
                cgpa_query, 
                {"student_id": student_id, "term_id": selected_term_id}
            )
            
            if all_enrollments_result is not None:
                for row in all_enrollments_result:
                    credits, marks = row
                    _, grade_point = calculate_grade(marks)
                    total_credits += credits
                    total_grade_points += (credits * grade_point)
                
                if total_credits > 0:
                    cgpa = round(total_grade_points / total_credits, 2)
        except Exception as e:
            print(f"Error calculating CGPA: {e}")
    
    return render_template(
        "./student/grades.html",
        username=username,
        terms=terms,
        selected_term_id=selected_term_id,
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
    
if __name__ == '__main__':
    app.run(debug=True)
