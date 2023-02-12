
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import datetime
import os.path
import sys
import subprocess, json
import logging

#Importing Google API libraries
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__,static_url_path='/static')

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'lowiezapp'

# Intialize MySQL
mysql = MySQL(app)

#http://localhost:5000- this is the entry page/landing page
@app.route('/',methods=['GET', 'POST'])
def index():
    
    return render_template('index.html')

# http://localhost:5000/login - this will be the login page, we need to use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password, ))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

# http://localhost:5000/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if all fields in the POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form and 'firstname' in request.form and 'lastname' in request.form:
        # Create variables for easy access
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Username Already taken'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s,%s,%s,%s)', (firstname,lastname,username, password, email,phone ))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            redirect(url_for('login'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/logout - this is the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('index'))

# http://localhost:5000/home - this is the home page, only accessible for loggedin users
@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        def view_tasks():
    # Check if user is loggedin
    
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("""SELECT * FROM tasks WHERE userid = %s""", (session['id'],))
            tasks = cursor.fetchall()
            cursor.close()
        #debugging
            print(tasks, file=sys.stderr)
            return tasks
        #Show tasks on the homepage 
        tasks = view_tasks()
        return render_template('home.html', username=session['username'],tasks=tasks)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))




#profile page. view profile
@app.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
    
        # show data in the profile page
        return render_template('profile.html',  account=account)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

#Edit profile
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form and 'phone' in request.form and 'firstname' in request.form and 'lastname' in request.form:
            # Create variables for easy access
            firstname = request.form['firstname']
            lastname = request.form['lastname']
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            phone = request.form['phone']
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
            account = cursor.fetchone()
            # If account exists show error and validation checks
            if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z0-9]+', username):
                msg = 'Username must contain only characters and numbers!'
            elif not username or not email:
                msg = 'Please fill out the form!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                cursor.execute('UPDATE accounts SET Firstname=%s,Lastname=%s,username=%s,email=%s,phone=%s WHERE id=%s', (firstname,lastname,username, email,phone,session['id'] ))
                mysql.connection.commit()
                msg = 'You have successfully updated your profile!'
                redirect(url_for('profile'))
        return render_template('edit_profile.html')
    # redirect user to homepage
    return redirect(url_for('home'))

#ADD tasks
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if request.method == 'POST' and 'task' in request.form and 'description' in request.form and 'date' in request.form and 'time' in request.form and 'status' in request.form:
            # Create variables for easy access
            task = request.form['task']
            description = request.form['description']
            date = request.form['date']
            time = request.form['time']
            status = request.form['status']
            userid = session['id']
            # Creating a Cursor to store the tasks in the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # validation checks
            if not task or not description or not date or not time:
                msg = 'Please fill out the form!'
            else:
                #insert new Task into Tasks table
                cursor.execute('INSERT INTO tasks VALUES (NULL,%s, %s, %s,%s,%s,%s)', (task,description,date,time,userid,status))
                mysql.connection.commit()
                msg = 'You have successfully added a task!'
        return render_template('add_task_sucess.html')
    # redirect user to homepage
    return redirect(url_for('home'))




#edit tasks
@app.route('/edit_task', methods=['GET', 'POST'])
def edit_task():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if request.method == 'POST' and 'task' in request.form and 'description' in request.form and 'date' in request.form and 'time' in request.form:
            # Create variables for easy access
            task = request.form['task']
            description = request.form['description']
            date = request.form['date']
            time = request.form['time']
            status= request.form['status']
            # Check if account exists using MySQL
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM tasks WHERE task = % s', (task, ))
            task = cursor.fetchone()
            # If account exists show error and validation checks
            if not task or not description or not date or not time:
                msg = 'Please fill out the form!'
            else:
                # Account doesnt exists and the form data is valid, now insert new account into accounts table
                cursor.execute('UPDATE tasks SET task=%s,description=%s,date=%s,duetime=%s,status=%s WHERE userid=%s', (task,description,date,time,session['id'] ))
                mysql.connection.commit()
                msg = 'You have successfully updated your task!'
        return render_template('edit_task.html')
    # redirect user to homepage
    return redirect(url_for('home'))

#delete tasks
@app.route('/delete_task', methods=['GET', 'POST'])
def delete_task():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if request.method == 'POST' and 'task' in request.form:
            # Create variables for easy access
            task = request.form['task']
            # selecting task to be deleted from database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM tasks WHERE task = % s', (task, ))
            task = cursor.fetchone()
            #deleting the task using the delete Query
            cursor.execute('DELETE FROM tasks WHERE task=%s', (task, ))
            mysql.connection.commit()
            msg = 'You have successfully deleted your task!'
        return render_template('delete_task.html')
    # redirect user to homepage
    return redirect(url_for('home'))

#Add task to Google calendar
@app.route('/add_to_calendar', methods=['GET', 'POST'])
def add_to_calendar():
#google calendar api
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            #connection timeout error
            # for i in range(15000):
            #     self.client.insert(Self.test_flow)
            #     response = self.client.delete(self.test_flow)
            #     time.sleep(1)
            #     SelfReg.assertEqual(response, 'ok')
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            cred = flow.run_local_server(port=8080)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        if request.method == 'POST' and 'task' in request.form and 'description' in request.form and 'date' in request.form and 'time' in request.form:
            # Create variables for easy access
            task = request.form['task']
            description = request.form['description']
            date = request.form['date']
            time = request.form['time']
            # selecting tasks from the database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM tasks WHERE task = % s', (task, ))
            task = cursor.fetchone()
            # validation checks
            if not task or not description or not date or not time:
                msg = 'Task not Found!'
            else:
                event = {
                    'summary': task,
                    'description': description,
                    'start': {
                        'dateTime': date+'T'+time,
                        'timeZone': 'Africa/Nairobi',
                    },
                    'end': {
                        'dateTime': date+'T'+time,
                        'timeZone': 'Africa/Nairobi',
                    },
                }
                event = service.events().insert(calendarId='primary', body=event).execute()
                msg = 'You have successfully added a task to your Google Calendar!'
        return render_template('add_to_calendar.html')



if __name__ == '__main__':
    app.run(debug=True) 
