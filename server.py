from flask import Flask, request, redirect, render_template, make_response, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.secret_key = "employee-management-secret-key"


# =========================================
# DATABASE CONNECTION
# =========================================

def get_database_connection():
    connection = sqlite3.connect("users.db")
    connection.row_factory = sqlite3.Row
    return connection


# =========================================
# CREATE DATABASE AND TABLES
# =========================================

def create_database():

    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Employees table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            department TEXT NOT NULL,
            salary INTEGER NOT NULL,
            joining_date TEXT NOT NULL,
            address TEXT
        )
    """)

    connection.commit()
    connection.close()

    print("Database and tables created successfully!")


# =========================================
# CHANGE THEME
# =========================================

@app.route("/set-theme/<theme>")
def set_theme(theme):

    if theme not in ["light", "dark"]:
        theme = "light"

    previous_page = request.referrer or url_for("home")

    response = make_response(
        redirect(previous_page)
    )

    response.set_cookie(
        "theme",
        theme,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="Lax"
    )

    return response


# =========================================
# HOME
# =========================================

@app.route("/")
def home():

    theme = request.cookies.get("theme", "light")

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "navbar.html",
        theme=theme,
        username=username,
        fullname=fullname
    )


# =========================================
# REGISTER PAGE
# =========================================

@app.route("/register", methods=["GET"])
def register_page():

    theme = request.cookies.get("theme", "light")

    return render_template(
        "register.html",
        theme=theme
    )


# =========================================
# REGISTER USER
# =========================================

@app.route("/register", methods=["POST"])
def register():

    fullname = request.form.get("fullname", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not fullname:
        return """
        <h2>Full name is required!</h2>
        <a href="/register">Try Again</a>
        """

    if not username:
        return """
        <h2>Username is required!</h2>
        <a href="/register">Try Again</a>
        """

    if not password:
        return """
        <h2>Password is required!</h2>
        <a href="/register">Try Again</a>
        """

    hashed_password = generate_password_hash(password)

    connection = get_database_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (fullname, username, password)
            VALUES (?, ?, ?)
        """, (
            fullname,
            username,
            hashed_password
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        connection.close()

        return """
        <h2>Username already exists!</h2>
        <p>Please choose another username.</p>
        <a href="/register">Try Again</a>
        """

    connection.close()

    return redirect(url_for("login_page"))


# =========================================
# LOGIN PAGE
# =========================================

@app.route("/login", methods=["GET"])
def login_page():

    theme = request.cookies.get("theme", "light")

    return render_template(
        "login.html",
        theme=theme
    )


# =========================================
# LOGIN USER
# =========================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()

    connection.close()

    if user and check_password_hash(
        user["password"],
        password
    ):

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["fullname"] = user["fullname"]

        return redirect(url_for("home"))

    return """
    <h2>Login failed!</h2>
    <p>Username or password is incorrect.</p>
    <a href="/login">Try Again</a>
    """


# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


# =========================================
# ADD EMPLOYEE PAGE
# =========================================

@app.route("/add-employee", methods=["GET"])
def add_employee_page():

    theme = request.cookies.get("theme", "light")

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "Add-Employee.html",
        theme=theme,
        username=username,
        fullname=fullname
    )


# =========================================
# ADD EMPLOYEE
# =========================================

@app.route("/add-employee", methods=["POST"])
def add_employee():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    department = request.form.get("department", "").strip()
    salary_text = request.form.get("salary", "").strip()
    joining_date = request.form.get("joining_date", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        return "<h2>Name is required!</h2><a href='/add-employee'>Go Back</a>"

    if not email:
        return "<h2>Email is required!</h2><a href='/add-employee'>Go Back</a>"

    if not phone:
        return "<h2>Phone is required!</h2><a href='/add-employee'>Go Back</a>"

    if not department:
        return "<h2>Department is required!</h2><a href='/add-employee'>Go Back</a>"

    if not salary_text:
        return "<h2>Salary is required!</h2><a href='/add-employee'>Go Back</a>"

    if not joining_date:
        return "<h2>Joining date is required!</h2><a href='/add-employee'>Go Back</a>"

    try:
        salary = int(salary_text)

    except ValueError:
        return """
        <h2>Salary must be a number!</h2>
        <a href="/add-employee">Go Back</a>
        """

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO employees
        (
            name,
            email,
            phone,
            department,
            salary,
            joining_date,
            address
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        phone,
        department,
        salary,
        joining_date,
        address
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("employees"))


# =========================================
# EMPLOYEES
# =========================================

@app.route("/employees")
def employees():

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM employees
        ORDER BY id DESC
    """)

    employees = cursor.fetchall()

    connection.close()

    theme = request.cookies.get("theme", "light")

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "employees.html",
        employees=employees,
        theme=theme,
        username=username,
        fullname=fullname
    )


# =========================================
# SEARCH EMPLOYEES
# =========================================

@app.route("/search")
def search():

    search_text = request.args.get("q", "").strip()

    connection = get_database_connection()
    cursor = connection.cursor()

    if search_text:

        search_value = f"%{search_text}%"

        cursor.execute("""
            SELECT *
            FROM employees
            WHERE
                name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
                OR department LIKE ?
            ORDER BY id DESC
        """, (
            search_value,
            search_value,
            search_value,
            search_value
        ))

    else:

        cursor.execute("""
            SELECT *
            FROM employees
            ORDER BY id DESC
        """)

    employees = cursor.fetchall()

    connection.close()

    theme = request.cookies.get("theme", "light")

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "employees.html",
        employees=employees,
        theme=theme,
        username=username,
        fullname=fullname,
        search_text=search_text
    )


# =========================================
# DELETE EMPLOYEE
# =========================================

@app.route("/delete-employee/<int:id>")
def delete_employee(id):

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM employees
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    return redirect(url_for("employees"))


# =========================================
# EDIT EMPLOYEE PAGE
# =========================================

@app.route("/edit-employee/<int:id>")
def edit_employee_page(id):

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM employees
        WHERE id = ?
    """, (id,))

    employee = cursor.fetchone()

    connection.close()

    if employee is None:

        return """
        <h2>Employee not found!</h2>
        <a href="/employees">Back to Employees</a>
        """

    theme = request.cookies.get("theme", "light")

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "edit-employee.html",
        employee=employee,
        theme=theme,
        username=username,
        fullname=fullname
    )


# =========================================
# UPDATE EMPLOYEE
# =========================================

@app.route("/edit-employee/<int:id>", methods=["POST"])
def edit_employee(id):

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    department = request.form.get("department", "").strip()
    salary_text = request.form.get("salary", "").strip()
    joining_date = request.form.get("joining_date", "").strip()
    address = request.form.get("address", "").strip()

    if not name:
        return f"""
        <h2>Name is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    if not email:
        return f"""
        <h2>Email is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    if not phone:
        return f"""
        <h2>Phone is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    if not department:
        return f"""
        <h2>Department is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    if not salary_text:
        return f"""
        <h2>Salary is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    if not joining_date:
        return f"""
        <h2>Joining date is required!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    try:
        salary = int(salary_text)

    except ValueError:
        return f"""
        <h2>Salary must be a number!</h2>
        <a href="/edit-employee/{id}">Go Back</a>
        """

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE employees
        SET
            name = ?,
            email = ?,
            phone = ?,
            department = ?,
            salary = ?,
            joining_date = ?,
            address = ?
        WHERE id = ?
    """, (
        name,
        email,
        phone,
        department,
        salary,
        joining_date,
        address,
        id
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("employees"))


# =========================================
# RUN SERVER
# =========================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )