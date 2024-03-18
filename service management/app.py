# app.py

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
#from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SECRET_KEY'] = '192198'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/flasksms'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'  # Database file will be created in the project folder
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True



db = SQLAlchemy(app)


login_manager = LoginManager(app)
login_manager.login_view = 'login'





# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(100), nullable=False, default='no address given')

# Create a user loader function required by flask_login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define the Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        address=request.form['address']
        #existing_user = User.query.filter_by(username=username).first()
        #if existing_user:
        #   flash('Username already exists. Please choose a different username.', 'danger')
        #  return redirect(url_for('register'))
        #new_user = User(username=username, password=generate_password_hash(password, method='sha256_crypt'))
        #new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        new_user = User(username=username, password=password, role=role, address=address)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
    

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            print("login block if condition is worked")
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

# Update 'Dashboard' route in app.py

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 1:  # Admin role
        tasks = Task.query.join(User).filter(Task.completed == False).add_columns(Task.id, Task.title, Task.description, Task.due_date, Task.completed, Task.user_id, User.username, User.address).all()
        completed_tasks = Task.query.filter_by(completed=True).join(User).add_columns(Task.id, Task.title, Task.description, Task.due_date, Task.completed, Task.user_id, User.username, User.address).all()
    else:  # User role
        tasks = Task.query.filter_by(user_id=current_user.id, completed=False).all()
        completed_tasks = Task.query.filter((Task.user_id == current_user.id) & (Task.completed == True)).join(User).add_columns(Task.id, Task.title, Task.description, Task.due_date, Task.completed, Task.user_id, User.username, User.address).all()

    return render_template('dashboard.html', tasks=tasks, completed_tasks=completed_tasks)

# Add Task route
@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']

        new_task = Task(title=title, description=description, due_date=due_date, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()

        flash('Task added successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_task.html')

# Add 'Complete Task' route in app.py
@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get(task_id)

    if task is None:
        flash('Task not found!', 'danger')
        return redirect(url_for('dashboard'))

    

    task.completed = True
    db.session.commit()

    flash('Task marked as completed!', 'success')
    return redirect(url_for('dashboard'))

# Edit Task route
@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('You are not authorized to edit this task.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = request.form['due_date']
        db.session.commit()

        flash('Task edited successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task)

# Delete Task route
@app.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id and current_user.role != 0:
        flash('You are not authorized to delete this task.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        db.session.delete(task)
        db.session.commit()

        flash('Task deleted successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('delete_task.html', task=task)


# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)