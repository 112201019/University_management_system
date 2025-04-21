from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import text
from sqlalchemy.engine import create_engine

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
                query = "SELECT professorName FROM Professors WHERE professorId = :user_id"
                session['username'] = db.execute_dql_commands(query, {'user_id': user_id}).fetchone()[0]
                session['user_id'] = user_id
                return redirect(url_for('professor_dashboard', username=session.get('username')))
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
                c.courseId AS "courseId", 
                c.courseName AS "courseName", 
                c.credits AS "credits", 
                d.deptName AS "deptName", 
                at.termName AS "termName",
                c.coursetype AS "courseType"
            FROM Enrollment e
            JOIN CourseOffering co ON e.offeringId = co.offeringId
            JOIN Courses c ON co.courseId = c.courseId
            JOIN Department d ON c.departmentId = d.departmentId
            JOIN AcademicTerm at ON co.termId = at.termId
            JOIN Professors p ON co.professorId = p.professorId
            WHERE p.professorId = :professor_id
            AND at.termId = :selected_term_id;
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

@app.route('/student/courses')
def view_courses():
    if session.get('role') != 'student':
        return redirect(url_for("login"))

    user_id = session.get('user_id')
    if not user_id:
        flash('Session expired. Please login again.')
        return redirect(url_for('login'))

    student_dept_query = """
        SELECT departmentId
        FROM Students
        WHERE studentId = :student_id
    """
    student_dept_result = db.execute_dql_commands(student_dept_query, {'student_id': user_id})
    student_dept_row = student_dept_result.fetchone()
    student_dept = student_dept_row[0] if student_dept_row else None

    if student_dept is None:
        flash('Student department information not found.')
        return redirect(url_for('student_dashboard'))

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
        WHERE e.studentId = :student_id AND e.status = 'Approved'
    """
    result = db.execute_dql_commands(query, {'student_id': user_id, 'student_dept': student_dept})
    courses = result.mappings().all()
    
    return render_template("./student/courses.html",
                           username=session.get('username'),
                           courses=courses)


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
            graduated
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

@app.route('/student/course_registation/add_courses')
def add_courses():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    return render_template("./student/drop_courses.html", username=session.get("username"))

@app.route('/student/course_registation/drop_courses')
def drop_courses():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    return render_template("./student/add_courses.html", username=session.get("username"))

if __name__ == '__main__':
    app.run(debug=True)
