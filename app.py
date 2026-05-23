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

    return render_template(
        'dashboard.html',
        name=session['user_name']
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

if __name__ == '__main__':
    app.run(debug=True)


   