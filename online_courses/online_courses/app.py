from flask import Flask, render_template, request, redirect, url_for, session
from peewee import *
from werkzeug.security import generate_password_hash, check_password_hash
from playhouse.shortcuts import model_to_dict

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'secretkey'  # Secret key for session management

# Database setup (using SQLite for simplicity)
db = SqliteDatabase('courses.db')

# Peewee models for managing course and enrollment data
class BaseModel(Model):
    class Meta:
        database = db

class Course(BaseModel):
    title = CharField()
    description = TextField()

class Student(BaseModel):
    name = CharField()
    email = CharField(unique=True)
    password = CharField()  # Add password field

class Enrollment(BaseModel):
    student = ForeignKeyField(Student, backref='enrollments')
    course = ForeignKeyField(Course, backref='enrollments')
    progress = IntegerField(default=0)

# Create tables in the database
db.connect()
db.create_tables([Course, Student, Enrollment])

# Home page - list all courses
@app.route('/')
def index():
    courses = Course.select()
    return render_template('index.html', courses=courses)

# Instructor creates a new course
@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        Course.create(title=title, description=description)
        return redirect(url_for('index'))
    return render_template('create_course.html')

# Course details page
@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.get(Course.id == course_id)
    students = Enrollment.select().where(Enrollment.course == course)
    current_student = None

    if 'student_id' in session:
        current_student = Student.get(Student.id == session['student_id'])

    return render_template('course_detail.html', course=course, students=students, current_student=current_student)

# Enroll in a course
@app.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if 'student_id' not in session:
        return redirect(url_for('login'))
    
    student = Student.get(Student.id == session['student_id'])
    course = Course.get(Course.id == course_id)
    
    Enrollment.create(student=student, course=course)
    
    return redirect(url_for('course_detail', course_id=course_id))

# Track progress for a course
@app.route('/progress/<int:enrollment_id>', methods=['POST'])
def track_progress(enrollment_id):
    progress = request.form['progress']
    enrollment = Enrollment.get(Enrollment.id == enrollment_id)
    enrollment.progress = progress
    enrollment.save()
    return redirect(url_for('course_detail', course_id=enrollment.course.id))

# Register a new student
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        try:
            student = Student.create(name=name, email=email, password=hashed_password)
            session['student_id'] = student.id
            return redirect(url_for('index'))
        except IntegrityError:
            return 'Email already exists.'
    
    return render_template('register.html')

# Login page for students
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        student = Student.select().where(Student.email == email).first()
        
        if student and check_password_hash(student.password, password):
            session['student_id'] = student.id
            return redirect(url_for('index'))
        else:
            return 'Invalid email or password.'
    
    return render_template('login.html')

# Logout a student
@app.route('/logout')
def logout():
    session.pop('student_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
