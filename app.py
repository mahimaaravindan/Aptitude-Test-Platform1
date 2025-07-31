from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
db_config = {
    'user': 'test',
    'password': '12345',
    'host': 'localhost',
    'database': 'aptitude_test'
}

def create_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            flash('Login successful!', 'success')
            return redirect(url_for('test'))
        else:
            flash('Login failed. Check your username and password.', 'danger')
    return render_template('login.html')

@app.route('/test', methods=['GET'])
def test():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, question, option1, option2, option3, option4 FROM questions LIMIT 10")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    questions_dict = []
    for question in questions:
        questions_dict.append({
            'id': question[0],
            'question': question[1],
            'option1': question[2],
            'option2': question[3],
            'option3': question[4],
            'option4': question[5]
        })
    
    return render_template('test.html', questions=questions_dict)

@app.route('/submit_test', methods=['POST'])
def submit_test():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, correct_option FROM questions LIMIT 10")
    questions = cursor.fetchall()

    score = 0
    for question in questions:
        qid = question[0]
        correct_option = question[1]
        selected_option = request.form.get(f'q{qid}')
        if selected_option and int(selected_option) == correct_option:
            score += 1

    cursor.execute("INSERT INTO scores (user_id, score) VALUES (%s, %s)", (user_id, score))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('score.html', score=score)

if __name__ == '__main__':
    app.run(debug=True)
