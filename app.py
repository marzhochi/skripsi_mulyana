from flask import Flask, render_template, make_response, flash, redirect, url_for, session, request, logging
import random
from flask_mysqldb import MySQL
from flask_wtf import Form
from wtforms import Form, StringField, SelectField, DateField, TextAreaField, PasswordField, validators
from wtforms.validators import InputRequired
from passlib.hash import sha256_crypt
from functools import wraps

import pdfkit
from datetime import date
import os
import cv2
from os import environ

from wtforms.fields.choices import SelectField

app = Flask(__name__)
app.secret_key = os.urandom(32)

PATH = '\\'.join(os.path.abspath(__file__).split('\\')[0:-1])
DATASET_PATH = os.path.join(PATH, "dataset")

# Konfigurasi Untuk Database
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "flask_user_manager"
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)

# Root Langung ke Halaman Login
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        session['username'] = username

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM tbl_user WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            # print(data['username'])
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(request.form['password'], password):
                # Jika password sesuai
                session['logged_in'] = True
                session['username'] = username
                session['role'] = data['role']
                session['nama'] = data['nama']

                flash('Berhasil masuk aplikasi!', 'success')
                if data['role'] == 'admin':
                    return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('home'))

            else:
                error = 'Login gagal, silahkan masukkan username dan kata sandi dengan benar.'
                return render_template('login.html', error=error)

            cur.close()

        else:
            error = 'Username tidak ditemukan.'
            return render_template('login.html', error=error)

    else:
        if 'logged_in' in session:
            if session['role'] == 'admin':
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('home'))
        else:
            return render_template('login.html')

# Permissin Untuk Admin
def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session and 'role' in session:
            if session['role'] == 'admin':
                return (f(*args, **kwargs))
            else:
                return redirect(url_for('login'))
        else:
            flash('Akses ditolak! Anda tidak memilik akses ke halaman ini.', 'danger')
            return redirect(url_for('login'))

    return wrap

# Permission Untuk Guru
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return (f(*args, **kwargs))
        else:
            flash('Akses ditolak! Anda tidak memilik akses ke halaman ini.', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route('/logout')
def logout():
    session.clear()
    flash('Berhasil keluar dari member panel', 'success')
    return redirect('/')

# SECTION ADMIN
# Dashboard
@app.route('/dashboard')
@is_admin
def dashboard():
    return render_template('admin/dashboard.html')

# List Kelas
@app.route('/kelas')
@is_logged_in
def kelas():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_kelas")

    kelas = cur.fetchall()

    if result > 0:
        return render_template('admin/kelas/list.html', kelas=kelas)
    else:
        # flash('Tidak ada kelas', 'danger')
        redirect(url_for('add_kelas'))

    cur.close()
    return render_template('admin/kelas/list.html')

class KelasForm(Form):
    nama_kelas = StringField('Nama Kelas', [validators.Length(min=1, max=10)])

@app.route('/add_kelas', methods=['GET', 'POST'])
# @is_logged_in
def add_kelas():
    form = KelasForm(request.form)

    if request.method == 'POST' and form.validate():
        nama_kelas = form.nama_kelas.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO tbl_kelas(nama_kelas) VALUES(%s)", (nama_kelas, ))

        mysql.connection.commit()

        cur.close()

        flash('Berhasil menambahkan kelas.', 'success')

        return redirect(url_for('kelas'))

    return render_template('admin/kelas/tambah.html', form=form)

@app.route('/edit_kelas/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_kelas(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_kelas WHERE id_kelas=%s", [id])

    kelas = cur.fetchone()

    form = KelasForm()

    form.nama_kelas.data = kelas['nama_kelas']

    if request.method=='POST':#form.validate_on_submit():
        nama_kelas = request.form['nama_kelas']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE tbl_kelas SET nama_kelas=%s WHERE id_kelas=%s", (nama_kelas, id))

        mysql.connection.commit()

        cur.close()

        flash('Kelas berhasil diperbaharui.', 'success')

        return redirect(url_for('edit_kelas', id=id))

    return render_template('admin/kelas/edit.html', form=form, id=id)

@app.route('/delete_kelas/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_kelas(id):
    cur=mysql.connection.cursor()

    cur.execute("DELETE FROM tbl_kelas WHERE id_kelas=%s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Berhasil menghapus kelas.', 'success')

    return redirect(url_for('kelas'))

# List Siswa
@app.route('/siswa')
@is_logged_in
def siswa():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_siswa")

    siswa = cur.fetchall()

    if result > 0:
        return render_template('admin/siswa/list.html', siswa=siswa)
    else:
        # flash('Tidak ada kelas', 'danger')
        redirect(url_for('add_siswa'))

    cur.close()
    return render_template('admin/siswa/list.html')

class SiswaForm(Form):
    nis = StringField('NIS', [validators.Length(min=1, max=11)])
    nama_siswa = StringField('Nama Siswa', [validators.Length(min=1, max=255)])
    tanggal_lahir = DateField('Tanggal Lahir', format="%Y-%m-%d", validators=[InputRequired(message="Tanggal Lahir wajib diisi.")])
    jenis_kelamin = StringField('Jenis Kelamin', validators=[InputRequired(message="Jenis Kelamin wajib diisi.")])
    kelas = SelectField('Pilih Kelas', choices=[])

@app.route('/add_siswa', methods=['GET', 'POST'])
# @is_logged_in
def add_siswa():
    form = SiswaForm(request.form)

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_kelas, nama_kelas FROM tbl_kelas")
    kelas_data = cur.fetchall()
    cur.close()

    print(kelas_data)
    form.kelas.choices = [(str(row['id_kelas']), row['nama_kelas']) for row in kelas_data]

    if request.method == 'POST' and form.validate():
        nis = form.nis.data
        nama_siswa = form.nama_siswa.data
        tanggal_lahir = form.tanggal_lahir.data
        jenis_kelamin = form.jenis_kelamin.data
        id_kelas = form.kelas.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tbl_siswa(nis, nama_siswa, tanggal_lahir, jenis_kelamin, id_kelas) VALUES(%s, %s, %s, %s, %s)", (nis, nama_siswa, tanggal_lahir, jenis_kelamin, id_kelas,))
        mysql.connection.commit()
        cur.close()

        flash('Berhasil menambahkan siswa.', 'success')

        return redirect(url_for('siswa'))


    return render_template('admin/siswa/tambah.html', form=form)

@app.route('/edit_siswa/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_siswa(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_siswa WHERE nis=%s", [id])

    siswa = cur.fetchone()

    form = SiswaForm()

    form.nis.data = siswa['nis']
    form.nama_siswa.data = siswa['nama_siswa']
    form.tanggal_lahir.data = siswa['tanggal_lahir']
    form.jenis_kelamin.data = siswa['jenis_kelamin']
    form.kelas.data = siswa['id_kelas']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id_kelas, nama_kelas FROM tbl_kelas")
    kelas_data = cur.fetchall()
    cur.close()

    print(kelas_data)
    form.kelas.choices = [(str(row['id_kelas']), row['nama_kelas']) for row in kelas_data]
    form.kelas.data = str(siswa['id_kelas'])

    if request.method=='POST':#form.validate_on_submit():
        nis = request.form['nis']
        nama_siswa = request.form['nama_siswa']
        tanggal_lahir = request.form['tanggal_lahir']
        jenis_kelamin = request.form['jenis_kelamin']
        kelas = request.form['kelas']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE tbl_siswa SET nama_siswa=%s, tanggal_lahir=%s, jenis_kelamin=%s, id_kelas=%s  WHERE nis=%s", (nama_siswa, tanggal_lahir,jenis_kelamin,kelas, id))

        mysql.connection.commit()

        cur.close()

        flash('Siswa berhasil diperbaharui.', 'success')

        return redirect(url_for('edit_siswa', id=id))

    return render_template('admin/siswa/edit.html', form=form, id=id)

@app.route('/delete_siswa/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_siswa(id):
    cur=mysql.connection.cursor()

    cur.execute("DELETE FROM tbl_siswa WHERE nis=%s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Berhasil menghapus siswa.', 'success')

    return redirect(url_for('siswa'))

# DATASET
class DatasetForm(Form):
    siswa = SelectField('Pilih Siswa', choices=[], render_kw={"class": "form-control", "id": "nis_siswa"})

@app.route('/dataset', methods=['GET', 'POST'])
# @is_logged_in
def dataset():
    form = DatasetForm(request.form)

    cur = mysql.connection.cursor()
    cur.execute("SELECT nis, nama_siswa FROM tbl_siswa")
    siswa_data = cur.fetchall()
    cur.close()

    print(siswa_data)
    form.siswa.choices = [(str(row['nis']), row['nama_siswa']) for row in siswa_data]

    if request.method == 'POST' and form.validate():
        nama_kelas = form.nama_kelas.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO tbl_kelas(nama_kelas) VALUES(%s)", (nama_kelas, ))

        mysql.connection.commit()

        cur.close()

        flash('Berhasil menambahkan dataset siswa.', 'success')

        return redirect(url_for('dataset'))

    return render_template('admin/siswa/dataset.html', form=form)


# List Mata Pelajaran
@app.route('/mapel')
@is_logged_in
def mapel():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_mata_pelajaran")

    mapel = cur.fetchall()

    if result > 0:
        return render_template('admin/mata_pelajaran/list.html', mapel=mapel)
    else:
        # flash('Tidak ada mata pelajaran', 'danger')
        redirect(url_for('add_mapel'))

    cur.close()
    return render_template('admin/mata_pelajaran/list.html')

class MapelForm(Form):
    nama_mata_pelajaran = StringField('Nama Mata Pelajaran', [validators.Length(min=3, max=50)])

@app.route('/add_mapel', methods=['GET', 'POST'])
# @is_logged_in
def add_mapel():
    form = MapelForm(request.form)

    if request.method == 'POST' and form.validate():
        nama_mata_pelajaran = form.nama_mata_pelajaran.data

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO tbl_mata_pelajaran(nama_mata_pelajaran) VALUES(%s)", (nama_mata_pelajaran, ))

        mysql.connection.commit()

        cur.close()

        flash('Berhasil menambahkan mata pelajaran.', 'success')

        return redirect(url_for('mapel'))

    return render_template('admin/mata_pelajaran/tambah.html', form=form)

@app.route('/edit_mapel/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_mapel(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM tbl_mata_pelajaran WHERE id_mapel=%s", [id])

    mapel = cur.fetchone()

    form = MapelForm()

    form.nama_mata_pelajaran.data = mapel['nama_mata_pelajaran']

    if request.method=='POST':#form.validate_on_submit():
        nama_mata_pelajaran = request.form['nama_mata_pelajaran']

        cur = mysql.connection.cursor()

        cur.execute("UPDATE tbl_mata_pelajaran SET nama_mata_pelajaran=%s WHERE id_mapel=%s", (nama_mata_pelajaran, id))

        mysql.connection.commit()

        cur.close()

        flash('Nama pelajaran berhasil diperbaharui.', 'success')

        return redirect(url_for('edit_mapel', id=id))

    return render_template('admin/mata_pelajaran/edit.html', form=form, id=id)

@app.route('/delete_mapel/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def delete_mapel(id):
    cur=mysql.connection.cursor()

    cur.execute("DELETE FROM tbl_mata_pelajaran WHERE id_mapel=%s", [id])

    mysql.connection.commit()

    cur.close()

    flash('Berhasil menghapus mata pelajaran.', 'success')

    return redirect(url_for('mapel'))

# SECTION GURU
@app.route('/home')
@is_logged_in
def home():
    return render_template('admin/dashboard.html')


@app.route("/upload_photo", methods=['POST'])
def upload_photo():
    nis_siswa = request.args.get('nis')
    path_new_nis = os.path.join(DATASET_PATH, nis_siswa)

    # create directory label if not exist
    if not os.path.exists(path_new_nis):
        os.mkdir(path_new_nis)

    # save uploaded image
    filename = nis_siswa + '%04d.jpg' % (len(os.listdir(path_new_nis)) + 1)
    file = request.files['webcam']
    file.save(os.path.join(path_new_nis, filename))

    # resize
    img = cv2.imread(os.path.join(path_new_nis, filename))
    img = cv2.resize(img, (250, 250))
    cv2.imwrite(os.path.join(path_new_nis, filename), img)

    return '', 200

if __name__ == "__main__":
    SECRET_KEY = os.urandom(32)
    app.config['WTF_CSRF_SECRET_KEY'] = SECRET_KEY
    app.run(debug=True, port=5001)
