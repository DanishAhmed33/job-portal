from flask import Flask, render_template, request, redirect, session
import mysql.connector
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="Danahm@7863",
    database="job_portal"
)
cursor = db.cursor()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        user_type = request.form['user_type']

        if user_type == 'candidate':
            cursor.execute("SELECT id FROM candidates WHERE email = %s AND password = %s", (email, password))
        elif user_type == 'employer':
            cursor.execute("SELECT id FROM employers WHERE email = %s AND password = %s", (email, password))
        
        user = cursor.fetchone()
        if user:
            session['user_id'] = user[0]
            session['user_type'] = user_type
            return redirect('/')
        else:
            return "Login failed, please check your credentials"
    
    return render_template('login.html')

# Route to view all jobs
@app.route('/jobs')
def jobs():
    cursor.execute("""
        SELECT jobs.id, jobs.title, jobs.description, employers.company_name, jobs.location, jobs.salary 
        FROM jobs 
        JOIN employers ON jobs.employer_id = employers.id
    """)
    jobs = cursor.fetchall()
    return render_template('jobs.html', jobs=jobs)

@app.route('/register-candidate', methods=['GET', 'POST'])
def register_candidate():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        cursor.execute("INSERT INTO candidates (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
        db.commit()
        candidate_id = cursor.lastrowid
        return render_template('candidate_success.html', candidate_id=candidate_id)

    return render_template('register_candidate.html')

@app.route('/register-employer', methods=['GET', 'POST'])
def register_employer():
    if request.method == 'POST':
        name = request.form['name']
        company_name = request.form['company_name']
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        cursor.execute("INSERT INTO employers (name, company_name, email, password) VALUES (%s, %s, %s, %s)", (name, company_name, email, password))
        db.commit()
        employer_id = cursor.lastrowid
        return render_template('employer_success.html', employer_id=employer_id)

    return render_template('register_employer.html')

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        employer_id = session['user_id']
        location = request.form['location']
        salary = request.form['salary']

        cursor.execute("INSERT INTO jobs (title, description, employer_id, location, salary) VALUES (%s, %s, %s, %s, %s)", 
                       (title, description, employer_id, location, salary))
        db.commit()
        return redirect('/jobs')

    return render_template('post_job.html')

@app.route('/apply-job', methods=['GET', 'POST'])
def apply_job():
    if 'user_id' not in session or session['user_type'] != 'candidate':
        return redirect('/login')

    if request.method == 'POST':
        job_id = request.form['job_id']
        candidate_id = session['user_id']

        cursor.execute("INSERT INTO applications (job_id, candidate_id) VALUES (%s, %s)", (job_id, candidate_id))
        db.commit()
        return redirect('/jobs')

    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()
    return render_template('apply_job.html', jobs=jobs)

@app.route('/job-status', methods=['GET', 'POST'])
def job_status():
    if 'user_id' not in session or session['user_type'] != 'candidate':
        return redirect('/login')

    if request.method == 'POST':
        candidate_id = session['user_id']

        cursor.execute("""
            SELECT jobs.title, jobs.description, employers.company_name, applications.application_date
            FROM applications
            JOIN jobs ON applications.job_id = jobs.id
            JOIN employers ON jobs.employer_id = employers.id
            WHERE applications.candidate_id = %s
        """, (candidate_id,))
        applications = cursor.fetchall()
        return render_template('job_status.html', applications=applications)

    return render_template('job_status.html')

@app.route('/employer-applications', methods=['GET'])
def employer_applications():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect('/login')

    employer_id = session['user_id']
    cursor.execute("""
        SELECT applications.id, candidates.name, jobs.title, applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN candidates ON applications.candidate_id = candidates.id
        WHERE jobs.employer_id = %s
    """, (employer_id,))
    applications = cursor.fetchall()
    return render_template('employer_applications.html', applications=applications)

@app.route('/update-application-status', methods=['POST'])
def update_application_status():
    if 'user_id' not in session or session['user_type'] != 'employer':
        return redirect('/login')

    application_id = request.form['application_id']
    status = request.form['status']
    cursor.execute("UPDATE applications SET status = %s WHERE id = %s", (status, application_id))
    db.commit()
    return redirect('/employer-applications')

if __name__ == '__main__':
    app.run(debug=True)
