from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecreto")

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        ssl={'ca': os.getenv("MYSQL_SSL_CA")} if os.getenv("MYSQL_SSL_CA") else None,
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    titulo VARCHAR(100) NOT NULL,
                    descripcion TEXT NOT NULL,
                    fecha_vencimiento DATE NOT NULL,
                    estado ENUM('pendiente', 'completada') NOT NULL,
                    usuario_id INT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                );
            """)
            cursor.execute("SELECT * FROM usuarios WHERE username = %s", ('camilo',))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", ('camilo', '12345'))
        conn.commit()
    finally:
        conn.close()

# Inicializar la base de datos al cargar la app
init_db()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user['id']
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciales incorrectas')
                return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tareas WHERE usuario_id=%s", (session['user_id'],))
            tareas = cursor.fetchall()
        return render_template('dashboard.html', tareas=tareas)
    finally:
        conn.close()

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    fecha = request.form['fecha_vencimiento']
    estado = request.form['estado']

    if not titulo or not descripcion or not fecha or not estado:
        flash('Todos los campos son obligatorios')
        return redirect(url_for('dashboard'))

    try:
        datetime.strptime(fecha, "%Y-%m-%d")
    except ValueError:
        flash('Fecha inválida. Formato correcto: AAAA-MM-DD')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tareas (titulo, descripcion, fecha_vencimiento, estado, usuario_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (titulo, descripcion, fecha, estado, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM tareas WHERE id=%s AND usuario_id=%s", (id, session['user_id']))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
