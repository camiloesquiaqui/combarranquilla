from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymysql import MySQL
from dotenv import load_dotenv
import os

# --- Cargar variables de entorno desde .env ---
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'clave_por_defecto')

# --- Configuración de conexión a MySQL (Aiven) ---
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_SSL_CA'] = os.getenv('MYSQL_SSL_CA')

# --- Inicializar MySQL ---
mysql = MySQL(app)

# --- Login ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usuario, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['usuario'] = usuario
            return redirect('/tareas')
        else:
            flash("Usuario o contraseña incorrectos")

    return render_template('login.html')

# --- CRUD de tareas ---
@app.route('/tareas', methods=['GET', 'POST'])
def tareas():
    if 'usuario' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    if request.method == 'POST':
        accion = request.form['accion']
        id_tarea = request.form.get('id')
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        fecha = request.form['fecha']
        estado = request.form['estado']

        if not titulo or not descripcion or not fecha or not estado:
            flash("Todos los campos son obligatorios")
        else:
            if accion == 'Agregar':
                cur.execute("INSERT INTO tareas (titulo, descripcion, fecha_vencimiento, estado) VALUES (%s, %s, %s, %s)",
                            (titulo, descripcion, fecha, estado))
            elif accion == 'Actualizar':
                cur.execute("UPDATE tareas SET titulo=%s, descripcion=%s, fecha_vencimiento=%s, estado=%s WHERE id=%s",
                            (titulo, descripcion, fecha, estado, id_tarea))
            elif accion == 'Eliminar':
                cur.execute("DELETE FROM tareas WHERE id = %s", (id_tarea,))
            mysql.connection.commit()

    cur.execute("SELECT * FROM tareas")
    tareas = cur.fetchall()
    cur.close()

    return render_template('tareas.html', tareas=tareas)

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/')

@app.route('/conexion')
def conexion():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        return "Conexión a Aiven exitosa"
    except Exception as e:
        return f"Error de conexión: {e}"

if __name__ == '__main__':
    app.run(debug=True)
