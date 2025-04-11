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
                query=f"""
                    SELECT studentName FROM Students WHERE studentId= {user_id};
                """
                session['username'] =  db.execute_dql_commands(query).fetchone()[0]
                # print(type(db.execute_dql_commands(query).fetchone()))
                return redirect(url_for('student_dashboard'))
            
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

@app.route('/student/courses')
def view_courses():
    if session.get('role') != 'student':
        return redirect(url_for("login"))
    return render_template("./student/courses.html", username=session.get("username"))

@app.route("/student/profile")
def view_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    return render_template('./student/profile.html', username=session.get('username'))

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
