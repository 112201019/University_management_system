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
        username = request.form.get('username')
        password = request.form.get('password')

        if role == 'admin':
            if username == 'admin' and password == 'admin':
                session['role'] = 'admin'
                session['username'] = username
                # Set DB role for current connection
                with engine.connect() as conn:
                    conn.execute(text("SET ROLE admin"))
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials')
                return redirect(url_for('login'))

        elif role == 'student':
            query = "SELECT * FROM Students WHERE studentName = :username"
            result = db.execute_dql_commands(query, {'username': username})
            row = result.fetchone()
            if row:
                session['role'] = 'student'
                session['username'] = username
                with engine.connect() as conn:
                    conn.execute(text("SET ROLE student"))
                return redirect(url_for('student'))
            else:
                flash('Invalid student credentials')
                return redirect(url_for('login'))

        elif role == 'professor':
            query = "SELECT * FROM Professors WHERE professorName = :username"
            result = db.execute_dql_commands(query, {'username': username})
            row = result.fetchone()
            if row:
                session['role'] = 'professor'
                session['username'] = username
                with engine.connect() as conn:
                    conn.execute(text("SET ROLE professor"))
                return redirect(url_for('professor_dashboard'))
            else:
                flash('Invalid professor credentials')
                return redirect(url_for('login'))
        else:
            flash('Please select a valid role')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html', username=session.get('username'))

@app.route('/student')
def student():
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

if __name__ == '__main__':
    app.run(debug=True)
