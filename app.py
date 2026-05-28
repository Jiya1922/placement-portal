from flask import Flask, render_template, request, redirect, session
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "placement_portal_secret_key"
UPLOAD_FOLDER = 'uploads/resumes'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = pymysql.connect(
    host="localhost",
    user="root",
    password="jiyanna@2006",
    database="placement_portal"
)

@app.route('/')
def home():
    return '<h1>Placement & Internship Preparation Portal</h1><a href="/register">Register</a>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department = request.form['department']
        password = generate_password_hash(request.form['password'])

        cursor = db.cursor()

        sql = """
        INSERT INTO users(name,email,department,password_hash)
        VALUES(%s,%s,%s,%s)
        """

        cursor.execute(sql, (name, email, department, password))
        db.commit()

        return "Registration Successful"

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()
        cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user[3], password):
            # Save user info in session
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            return redirect('/dashboard')
        else:
            return "Invalid email or password"

    return render_template('login.html')


# Dashboard route
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jiyanna@2006',
        database='placement_portal',
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = conn.cursor()

    # Interview posts count
    cursor.execute(
        "SELECT COUNT(*) AS total_posts FROM interview_posts WHERE user_id=%s",
        (session['user_id'],)
    )

    posts = cursor.fetchone()

    # Aptitude tests count
    cursor.execute(
        "SELECT COUNT(*) AS total_tests FROM test_results WHERE user_id=%s",
        (session['user_id'],)
    )

    tests = cursor.fetchone()

    # Average score
    cursor.execute(
        """
        SELECT AVG(score*100/total_questions) AS average_score
        FROM test_results
        WHERE user_id=%s
        """,
        (session['user_id'],)
    )

    average = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        name=session['user_name'],
        total_posts=posts['total_posts'],
        total_tests=tests['total_tests'],
        average_score=round(average['average_score'] or 0)
    )
@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        file = request.files['resume']

        if file:

            filename = secure_filename(file.filename)

            file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    filename
                )
            )

            return "Resume Uploaded Successfully"

    return render_template('upload_resume.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')    

@app.route('/aptitude')
def aptitude():

    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jiyanna@2006',
        database='placement_portal',
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM aptitude_questions")

    questions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'aptitude.html',
        questions=questions
    )

@app.route('/submit_test', methods=['POST'])
def submit_test():

    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jiyanna@2006',
        database='placement_portal',
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM aptitude_questions")

    questions = cursor.fetchall()

    score = 0

    for q in questions:

        selected = request.form.get(f"q{q['id']}")

        if selected == q['correct_answer']:
            score += 1

    cursor.execute(
        """
        INSERT INTO test_results
        (user_id, score, total_questions)
        VALUES (%s, %s, %s)
        """,
        (
            session['user_id'],
            score,
            len(questions)
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    return render_template(
        'result.html',
        score=score,
        total=len(questions)
    )

@app.route('/interview_posts', methods=['GET', 'POST'])
def interview_posts():

    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='jiyanna@2006',
        database='placement_portal',
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = conn.cursor()

    if request.method == 'POST':

        company = request.form['company']
        role = request.form['role']
        experience = request.form['experience']

        sql = """
        INSERT INTO interview_posts
        (user_id, company_name, role, experience)
        VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                session['user_id'],
                company,
                role,
                experience
            )
        )

        conn.commit()

    cursor.execute(
        "SELECT * FROM interview_posts ORDER BY created_at DESC"
    )

    posts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'interview_posts.html',
        posts=posts
    )

if __name__ == '__main__':
    app.run(debug=True)