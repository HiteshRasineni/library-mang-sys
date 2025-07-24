from flask import Flask, render_template, request, redirect, url_for, jsonify
from db_config import get_db_connection
from datetime import date, timedelta

app = Flask(__name__, static_folder="static", template_folder="templates")


# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        adminno = request.form['adminno']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT EXISTS(SELECT * FROM students WHERE admin=%s OR name=%s)', (adminno, name))
        if cur.fetchone()[0]:
            return "Already signed up. <a href='/'>Go Back</a>"
        cur.execute('INSERT INTO students (name, admin, fine_amount) VALUES (%s, %s, 0)', (name, adminno))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Add Book
@app.route('/addbook', methods=['GET', 'POST'])
def addbook():
    if request.method == 'POST':
        bookname = request.form['bookname']
        bookid = request.form['bookid']
        author = request.form['author']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT EXISTS(SELECT * FROM books WHERE book_id=%s)", (bookid,))
        if cur.fetchone()[0]:
            return "Book ID already exists. <a href='/addbook'>Try Again</a>"
        data = (bookname, bookid, author)
        cur.execute('INSERT INTO books VALUES (%s, %s, %s)', data)
        cur.execute('INSERT INTO available_books VALUES (%s, %s, %s)', data)
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('addbook.html')

# Issue Book
@app.route('/issuebook', methods=['GET', 'POST'])
def issuebook():
    if request.method == 'POST':
        name = request.form['name']
        admin = request.form['admin']
        bookid = request.form['bookid']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT EXISTS(SELECT * FROM students WHERE admin=%s AND name=%s)', (admin, name))
        if not cur.fetchone()[0]:
            return "Please sign up first. <a href='/signup'>Signup</a>"

        cur.execute('SELECT fine_amount FROM students WHERE admin=%s', (admin,))
        if cur.fetchone()[0] > 0:
            return "Pay fine before issuing a new book."

        cur.execute('SELECT EXISTS(SELECT * FROM available_books WHERE book_id=%s)', (bookid,))
        if not cur.fetchone()[0]:
            return "Book not available. <a href='/dashboard'>Back</a>"

        issue_date = date.today()
        submit_date = issue_date + timedelta(days=7)
        cur.execute('INSERT INTO issue VALUES (%s, %s, %s, %s)', (name, admin, bookid, issue_date))
        cur.execute('INSERT INTO books_to_be_submitted VALUES (%s, %s, %s, %s)', (name, admin, bookid, submit_date))
        cur.execute('DELETE FROM available_books WHERE book_id=%s', (bookid,))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('issuebook.html')

# Submit Book
@app.route('/submitbook', methods=['GET', 'POST'])
def submitbook():
    if request.method == 'POST':
        name = request.form['name']
        admin = request.form['admin']
        bookid = request.form['bookid']
        submit_date = date.today()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT EXISTS(SELECT * FROM books_to_be_submitted WHERE book_id=%s)', (bookid,))
        if not cur.fetchone()[0]:
            return "Book not issued. <a href='/submitbook'>Try Again</a>"
        cur.execute('INSERT INTO submit VALUES (%s, %s, %s, %s)', (name, admin, bookid, submit_date))
        cur.execute('SELECT * FROM books WHERE book_id=%s', (bookid,))
        book = cur.fetchone()
        cur.execute('INSERT INTO available_books VALUES (%s, %s, %s)', (book[0], book[1], book[2]))
        cur.execute('DELETE FROM books_to_be_submitted WHERE book_id=%s', (bookid,))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('submitbook.html')

# Search Book
@app.route('/searchbook', methods=['GET', 'POST'])
def searchbook():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'POST':
        keyword = request.form['keyword'] + '%'
        cur.execute('SELECT * FROM books WHERE book_name LIKE %s', (keyword,))
        books = cur.fetchall()
        return render_template('searchbook.html', books=books)
    return render_template('searchbook.html', books=None)

# Display Books
@app.route('/displaybooks')
def displaybooks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books ORDER BY book_id')
    books = cur.fetchall()
    cur.execute('SELECT * FROM available_books ORDER BY book_id')
    available = cur.fetchall()
    return render_template('displaybooks.html', books=books, available=available)

# Delete Book
@app.route('/deletebook', methods=['GET', 'POST'])
def deletebook():
    if request.method == 'POST':
        bookid = request.form['bookid']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM books WHERE book_id=%s', (bookid,))
        cur.execute('DELETE FROM available_books WHERE book_id=%s', (bookid,))
        conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('deletebook.html')

# Issued Books
@app.route('/issuedbooks')
def issuedbooks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM issue')
    books = cur.fetchall()
    return render_template('issuedbooks.html', books=books)

# Submitted Books
@app.route('/submittedbooks')
def submittedbooks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM submit')
    books = cur.fetchall()
    return render_template('submittedbooks.html', books=books)

# Books Issued to a Student
@app.route('/studentbooks', methods=['GET', 'POST'])
def studentbooks():
    books = None
    if request.method == 'POST':
        admin = request.form['admin']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM issue WHERE admin=%s', (admin,))
        books = cur.fetchall()
    return render_template('studentbooks.html', books=books)

# Books to be Submitted
@app.route('/pendingbooks')
def pendingbooks():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM books_to_be_submitted')
    books = cur.fetchall()
    return render_template('pendingbooks.html', books=books)

# Fine Payment
@app.route('/finepayment', methods=['GET', 'POST'])
def finepayment():
    message = None
    if request.method == 'POST':
        admin = request.form['admin']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE students SET fine_amount = 0 WHERE admin=%s', (admin,))
        conn.commit()
        message = "Fine paid successfully."
    return render_template('finepayment.html', message=message)

# Signed Students
@app.route('/students')
def students():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM students')
    data = cur.fetchall()
    return render_template('students.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)
