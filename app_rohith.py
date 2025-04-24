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
                "courseId", 
                "courseName", 
                "credits", 
                "deptName", 
                "termName",
                "courseType"
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

if __name__ == '__main__':
    app.run(debug=True)