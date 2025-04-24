from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from datetime import date  # Import to get current date

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

@app.route('/student/grades')
def view_grades():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    return render_template("./student/grades.html", username=session.get("username"))

@app.route('/student/course_registation')
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
        query = """
            SELECT 
                c.courseId AS "courseId", 
                c.courseName AS "courseName", 
                c.credits AS "credits", 
                d.deptName AS "deptName", 
                at.termName AS "termName", 
                p.professorName AS "professorName",
                CASE 
                    WHEN c.departmentId = :student_dept THEN 'Core Course' 
                    ELSE 'Elective Course' 
                END AS "courseType"
            FROM Enrollment e
            JOIN CourseOffering co ON e.offeringId = co.offeringId
            JOIN Courses c ON co.courseId = c.courseId
            JOIN Department d ON c.departmentId = d.departmentId
            JOIN AcademicTerm at ON co.termId = at.termId
            JOIN Professors p ON co.professorId = p.professorId
            WHERE e.studentId = :student_id 
              AND e.status = 'Approved'
              AND at.termId = :selected_term_id;
        """
        courses_result = db.execute_dql_commands(query, {
            'student_id': user_id,
            'student_dept': student_dept,
            'selected_term_id': selected_term_id
        })
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

    # Handle POST: Add or Drop
    if request.method == 'POST':
        offering_id = request.form['offering_id']
        action = request.form.get('action')

        if action == 'add':
            # Duplicate check (excluding dropped)
            dup = db.execute_dql_commands(
                "SELECT status FROM Enrollment WHERE studentId = :sid AND offeringId = :oid",
                {'sid': user_id, 'oid': offering_id}
            ).fetchone()

            if dup and dup[0] != 'Dropped':
                flash("You've already requested or completed this course.", "warning")
                return redirect(url_for('add_courses'))

            if dup and dup[0] == 'Dropped':
                # Reactivate the dropped row
                db.execute_ddl_and_dml_commands(
                    '''
                    UPDATE Enrollment
                    SET status = 'Pending', enrollmentDate = :edate
                    WHERE studentId = :sid AND offeringId = :oid
                    ''',
                    {'sid': user_id, 'oid': offering_id, 'edate': date.today()}
                )
            else:
                # Compute next enrollmentId
                maxid_row = db.execute_dql_commands("SELECT COALESCE(MAX(enrollmentId),0) FROM Enrollment").fetchone()
                next_id = maxid_row[0] + 1
                db.execute_ddl_and_dml_commands(
                    '''
                    INSERT INTO Enrollment (enrollmentId, studentId, offeringId, enrollmentDate, status)
                    VALUES (:eid, :sid, :oid, :edate, 'Pending')
                    ''',
                    {'eid': next_id, 'sid': user_id, 'oid': offering_id, 'edate': date.today()}
                )

            flash("Course request submitted (pending approval).", "success")
            return redirect(url_for('add_courses'))

        elif action == 'drop':
            db.execute_ddl_and_dml_commands(
                '''
                UPDATE Enrollment
                SET status = 'Dropped'
                WHERE studentId = :sid AND offeringId = :oid AND status = 'Pending'
                ''',
                {'sid': user_id, 'oid': offering_id}
            )
            flash("Course request dropped.", "info")
            return redirect(url_for('add_courses'))

    # GET → find the active term
    today = date.today()
    term_row = db.execute_dql_commands(
        "SELECT termId FROM AcademicTerm WHERE startDate < :today AND endDate > :today",
        {'today': today}
    ).fetchone()

    courses = []
    if term_row:
        term_id = term_row[0]
        stud_dept = db.execute_dql_commands(
            "SELECT departmentId FROM Students WHERE studentId = :sid",
            {'sid': user_id}
        ).fetchone()[0]

        courses = db.execute_dql_commands("""
            SELECT
                co.offeringId AS "offeringId", 
                c.courseId AS "courseId", 
                c.courseName AS "courseName", 
                c.credits AS "credits",
                d.deptName AS "deptName", 
                at.termName AS "termName", 
                p.professorName AS "professorName",
                CASE 
                    WHEN c.departmentId = :stud_dept 
                        THEN 'Core Course' 
                        ELSE 'Elective Course' 
                END AS "courseType",
                (SELECT e.status 
                    FROM Enrollment e 
                    WHERE e.studentId = :uid 
                        AND e.offeringId = co.offeringId) 
                AS "enrollmentStatus",
                (SELECT at2.termName
                FROM Enrollment e2
                JOIN CourseOffering co2 ON e2.offeringId = co2.offeringId
                JOIN AcademicTerm at2 ON co2.termId = at2.termId
                JOIN StudentGrades sg2 ON e2.enrollmentId = sg2.enrollmentId
                WHERE e2.studentId = :uid AND co2.courseId = c.courseId
                    AND e2.status = 'Approved' AND sg2.grade > 35
                ORDER BY at2.startDate DESC LIMIT 1) AS "previousTermName"
            FROM CourseOffering co
            JOIN Courses c ON co.courseId = c.courseId
            JOIN Department d ON c.departmentId = d.departmentId
            JOIN AcademicTerm at ON co.termId = at.termId
            JOIN Professors p ON co.professorId = p.professorId
            WHERE co.termId = :tid
        """, {'stud_dept': stud_dept, 'tid': term_id, 'uid': user_id}).mappings().all()

        courses = [dict(c) for c in courses]
        for course in courses:
            course["can_add"] = (not course["enrollmentStatus"] or course["enrollmentStatus"] == "Dropped") and not course["previousTermName"]
            course["can_drop"] = course["enrollmentStatus"] == "Pending"

    return render_template('student/add_courses.html', username=session['username'], courses=courses)

@app.route('/student/course_registation/registration_log')
def registration_log():
    # 1. Ensure student
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    student_id = session.get("user_id")
    if not student_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for("login"))

    today = date.today()

    # 2. Find current term
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

    # 3. (Optional) load the single-term list for the dropdown
    terms = [{"termId": term_id, "termName": term_name}]

    # 4. Fetch the student’s department (for courseType)
    stud_dept = db.execute_dql_commands(
        "SELECT departmentId FROM Students WHERE studentId = :sid",
        {"sid": student_id}
    ).fetchone()[0]

    # 5. Fetch all enrollments in this term
    rows = db.execute_dql_commands("""
        SELECT
          co.offeringId       AS "offeringId",
          c.courseId          AS "courseId",
          c.courseName        AS "courseName",
          c.credits           AS "credits",
          d.deptName          AS "deptName",
          at.termName         AS "termName",
          p.professorName     AS "professorName",
          CASE
            WHEN c.departmentId = :stud_dept THEN 'Core Course'
            ELSE 'Elective Course'
          END                  AS "courseType",
          e.status            AS "status"
        FROM Enrollment e
        JOIN CourseOffering co ON e.offeringId = co.offeringId
        JOIN Courses        c  ON co.courseId    = c.courseId
        JOIN Department     d  ON c.departmentId = d.departmentId
        JOIN AcademicTerm   at ON co.termId       = at.termId
        JOIN Professors     p  ON co.professorId  = p.professorId
        WHERE e.studentId = :sid
          AND co.termId    = :term_id
    """, {
        "sid":       student_id,
        "term_id":   term_id,
        "stud_dept": stud_dept
    }).mappings().all()

    # 6. Turn each RowMapping into a dict
    courses = [dict(r) for r in rows]
    return render_template(
        "student/registration_log.html",
        username=session["username"],
        courses=courses,
        terms=terms,
        selected_term_id=term_id
    )

if __name__ == '__main__':
    app.run(debug=True)
