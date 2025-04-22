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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

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
    students_query += " ORDER BY s.studentName"
    
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
    prof_sql += " ORDER BY p.professorName"

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


@app.route('/admin_professor/del_professor', methods=['GET', 'POST'])
def del_prof():
    if request.method == 'POST':
        try:
            p_professor_id = request.form['professor_id']

            if not p_professor_id:
                 flash('Professor ID is required.', 'warning')
                 return render_template('./admin/professor/delete_professor.html')

            # Call the stored procedure to delete the professor
            db.execute_ddl_and_dml_commands(
                "CALL delete_professor(:p_professor_id)",
                {'p_professor_id': int(p_professor_id)} # Ensure ID is an integer
            )

            flash(f'Professor with ID {p_professor_id} deleted successfully!', 'success')
            return redirect(url_for('del_prof')) # Redirect to the same page (or a professor list page)

        except Exception as e:
            # Catch potential errors, including the EXCEPTION raised by the procedure
            flash(f'Error deleting professor: {str(e)}', 'error')
            # Optionally, log the error: app.logger.error(f"Error deleting professor: {e}")

    # For GET request, just render the form
    return render_template('./admin/professor/delete_professor.html')


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
        'admin/courses/courses.html', # Adjust path as needed
        terms=terms,
        offerings=offerings,
        selected_term_id=selected_term_id,
        selected_term_name=selected_term_name
    )

if __name__ == '__main__':
    app.run(debug=True)
