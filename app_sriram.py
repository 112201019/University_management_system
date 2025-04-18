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

enroll_open = {'status': False}  # Shared mutable state

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
    return render_template('/admin/admin.html', username=session.get('username'))

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

@app.route('/course_registration1', methods=['GET', 'POST'])
def course_registration1():
    if request.method == 'POST':
        # Toggle the enrollment flag
        enroll_open['status'] = not enroll_open['status']
        return redirect(url_for('course_registration1'))
    
    return render_template('./admin/course_registration/course_registration.html', enroll_status=enroll_open['status'])

@app.route('/admin_student', methods=['GET','POST'])
def admin_student():
    return render_template('./admin/student/student.html')

@app.route('/admin_professor', methods=['GET','POST'])
def admin_professor():
    return render_template('./admin/professor/professor.html')

@app.route('/admin_course', methods=['GET','POST'])
def admin_course():
    return render_template('./admin/courses/courses.html')

@app.route('/admin_student/AorD_students', methods=['GET','POST'])
def AorD_students():
    return render_template('./admin/student/Addordelete_students.html')


@app.route('/admin_student/view_all_students', methods=['GET','POST'])
def view_all_students():
    # Get filter parameters from the request - as strings
    degree_filter = request.args.get('degree', 'all')
    department_filter = request.args.get('department', 'all')
    
    print(f"DEBUG: Received filters - degree: {degree_filter}, department: {department_filter}")
    
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
    students_query += " ORDER BY s.studentName"
    
    print(f"DEBUG: Executing query: {students_query}")
    
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
    
    print(f"DEBUG: Found {len(students_list)} students")
    
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

# Edit student form
@app.route('/admin_student/edit_student/<int:student_id>')
def edit_student(student_id):
    # Get all degrees for the dropdown
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
    
    # Get all departments for the dropdown
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
    
    # Query to get the student details
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
            s.graduationStatus
        FROM 
            Students s
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
    
    # Format the student data with raw date values for the form
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
        'graduationStatus': student_data[8]
    }
    
    return render_template('./admin/student/edit_student.html', student=student, degrees=degrees, departments=departments)

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
    if request.method == 'POST':
        try:
            # Get form data
            student_data = {
                'p_studentName': request.form['name'],
                'p_degreeId': request.form['degree_id'],
                'p_departmentId': request.form['department_id'],
                'p_dateOfJoining': request.form['join_date'],
                'p_gender': request.form['gender'],
                'p_dob': request.form['dob'],
                'p_graduationStatus': request.form['status']
            }

            # Call the stored procedure
            db.execute_ddl_and_dml_commands(
                "SELECT insert_student(:p_studentName, :p_degreeId, :p_departmentId, "
                ":p_dateOfJoining, :p_gender, :p_dob, NULL, :p_graduationStatus)",
                student_data
            )
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('add_student'))
        
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
    
    return render_template('./admin/student/Add_students.html')

# app.py - Add this route
@app.route('/AorDstudent/delete_student', methods=['GET', 'POST'])
def del_student():
    if request.method == 'POST':
        try:
            student_id = request.form['student_id']
            db.execute_ddl_and_dml_commands(
                "SELECT delete_student(:p_student_id)",
                {'p_student_id': student_id}
            )
            flash('Student deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting student: {str(e)}', 'error')
        return redirect(url_for('del_student'))
    return render_template('./admin/student/Del_students.html')

@app.route('/AorDstudent', methods=['GET'])
def AorD():
    return render_template('./admin/student/AorD.html')
if __name__ == '__main__':
    app.run(debug=True)
