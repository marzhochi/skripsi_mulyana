from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = "Skripsi absensi sekolah menggunakan Face"

# Konfigurasi Untuk Database
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flask_user_manager"

mysql = MySQL(app)

# Route Login
@app.route("/")
@app.route("/login", methods=["GET", "POST"])
def login():
    mesage = ""

    if request.method == "POST" and "email" in request.form and "password" in request.form:
        email = request.form["email"]
        password = request.form["password"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM tbl_user WHERE email=%s and password=%s", (email, password, ))
        user = cursor.fetchone()

        if user:
            if user["role"] == "admin":
                session["loggedin"] = True
                session["userid"] = user["userid"]
                session["nama"] = user["nama"]
                session["email"] = user["email"]
                mesage = "Login berhasil. . ."
                return redirect(url_for("home"))
            else:
                mesage = "hanya admin yang dapat Login..."
        else:
            mesage = "Email atau Password Salahh..."
    return render_template("login.html", mesage=mesage)

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    mesage = ""

    if request.method == "POST" and "nama" in request.form and "password" in request.form and "email" in request.form:
        userName = request.form["nama"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user WHERE email=%s", (email, ))

        account = cursor.fetchone()
        if account:
            mesage = "User sudah ada."
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = "Email Address Salah."
        elif not userName or not password or not email:
            mesage = "Silahkan lengkapi data dengan benar."
        else:
            cursor.execute("INSERT INTO tbl_user VALUES (NULL, %s, %s, %s, %s, 1)",
                           (userName, email, password, role))
            mysql.connection.commit()
            mesage = "Berhasil menambahkan user baru."
            return render_template("add_user.html", mesage=mesage)
    elif request.method == "POST":
        mesage = "Silahkan isi data dengan benar."
    else:
        return render_template("add_user.html", mesage=mesage)

@app.route("/home", methods=["GET", "POST"])
def home():
    if "loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user")
        users = cursor.fetchall()
        return render_template("admin/index.html", users=users)
    else:
        return redirect(url_for("login"))

@app.route("/users", methods=["GET", "POST"])
def users():
    if "loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user")
        users = cursor.fetchall()
        return render_template("users.html", users=users)
    else:
        return redirect(url_for("login"))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/view", methods=["GET", "POST"])
def view():
    if "loggedin" in session:
        viewUserId = request.args.get("userid")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM user WHERE userid=%s", (viewUserId, ))

        user = cursor.fetchone()
        return render_template("view.html", user=user)
    else:
        return redirect(url_for("login"))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    msg = ""

    if "loggedin" in session:
        editUserId = request.args.get("userid")
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tbl_user WHERE userid=%s", (editUserId, ))
        editUser = cursor.fetchone()

        if request.method == "POST" and "nama" in request.form and "userid" in request.form and "role" in request.form and "country" in request.form:
            userName = request.form["nama"]
            role = request.form["role"]
            userId = request.form["userid"]

            if not re.match(r'[A-Za-z0-9]+', userName):
                msg = "Nama harus mengandung hanya karakter dan angka"
            else:
                cursor.execute("UPDATE user SET nama=%s, role=%s, country=%s WHERE userid=%s", (
                    userName, role, country, (userId, ), ))
                mysql.connection.commit()
                msg = "User Updated . . ."
                return redirect(url_for("users"))
        elif request.method == "POST":
            msg = "Tolong Isi Form . . ."
        else:
            return render_template("edit_user.html", msg=msg, editUser=editUser)
    else:
        return redirect(url_for("login"))


@app.route("/password_change", methods=["GET", "POST"])
def password_change():
    mesage = ""

    if 'loggedin' in session:
        changePassUserId = request.args.get('userid')

        if request.method == 'POST' and 'password' in request.form and 'confirm_pass' in request.form and 'userid' in request.form:
            password = request.form['password']
            confirm_pass = request.form['confirm_pass']
            userId = request.form['userid']

            if not password or not confirm_pass:
                mesage = 'Silakan isi formulirnya . . .'
            elif password != confirm_pass:
                mesage = 'Konfirmasi Password Tidak Sama . . .'
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(
                    'UPDATE user SET  password =% s WHERE userid =% s', (password, (userId, ), ))
                mysql.connection.commit()
                mesage = 'Password updated !'

        elif request.method == 'POST':
            mesage = 'Silakan isi formulirnya . . .'
        else:
            return render_template("password_change.html", mesage=mesage, changePassUserId=changePassUserId)

    else:
        return redirect(url_for('login'))


@app.route('/delete/<int:userid>', methods=['GET', 'POST'])
def delete(userid):

    if "loggedin" in session:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM tbl_user WHERE userid = %s", (userid,))
        mysql.connection.commit()
        cur.close()
        msg = 'Data berhasil dihapus . . .'
        return redirect(url_for('users'))
        # return render_template("users.html", mesage=msg)
    else:
        return "gagal hapus data"


if __name__ == "__main__":
    app.run(debug=True, port=5000)
