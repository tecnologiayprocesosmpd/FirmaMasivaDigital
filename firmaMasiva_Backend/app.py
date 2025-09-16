from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import tempfile # Importa el módulo para manejar archivos temporales
from automation_script import firmador_automation
import pyodbc


app = Flask(__name__)
CORS(app)

# AGREGAR CONFIGURACIÓN BD
SERVER = 'DESKTOP-4PV1O46\\SQLEXPRESS'
DATABASE = 'Firmas'
DRIVER = '{ODBC Driver 17 for SQL Server}'

# AGREGAR FUNCIÓN DE VALIDACIÓN
def validar_cuil_y_obtener_ruta(cuil):
    """
    Valida si el CUIL existe y devuelve la ruta de descarga.
    Retorna la ruta si existe, None si no existe.
    """
    conn = None
    try:
        connection_string = (
            f'DRIVER={DRIVER};'
            f'SERVER={SERVER};'
            f'DATABASE={DATABASE};'
            f'Trusted_Connection=yes;'
        )
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        print(f"Validando CUIL: '{cuil}'")
        cursor.execute("SELECT path FROM dbo.signature WHERE cuil = ?", (cuil,))
        result = cursor.fetchone()
        
        if result:
            ruta = result[0]
            print(f"CUIL encontrado. Ruta: {ruta}")
            return ruta
        else:
            print("CUIL no encontrado")
            return None
            
    except pyodbc.Error as e:
        print(f"Error de Base de Datos: {e}")
        return None
        
    finally:
        if conn:
            conn.close()

@app.route('/firmar', methods=['POST'])
def handle_firmar_request():
    try:
        # Obtiene los datos del formulario
        cuit = request.form.get('cuit')
        password = request.form.get('password')
        pin = request.form.get('pin')
        otp_code = request.form.get('otpCode')
        
        # Obtiene los archivos que se enviaron
        uploaded_files = request.files.getlist('files[]') # 'files[]' es el nombre que le darás en el frontend

        if not all([cuit, password, pin, otp_code, uploaded_files]):
            return jsonify({"message": "Faltan datos o archivos requeridos."}), 400

         # AGREGAR VALIDACIÓN CUIL AQUÍ
        cuit_limpio = cuit.replace('-', '')
        
        if not cuit_limpio.isdigit() or len(cuit_limpio) != 11:
            return jsonify({"message": "El CUIL debe ser de 11 dígitos numéricos."}), 400
        
        download_path = validar_cuil_y_obtener_ruta(cuit_limpio)
        if download_path is None:
            return jsonify({"message": "Usted no tiene registrado el CUIL en el sistema."}), 403

        print(f"CUIL {cuit_limpio} autorizado. Ruta de descarga: {download_path}")


        # Resto de tu código igual...
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            file_paths.append(file_path)

        thread = threading.Thread(
            target=firmador_automation,
            args=(cuit, password, otp_code, pin, file_paths, download_path)
        )
        thread.start()
        
        return jsonify({"message": "Proceso de firma iniciado."}), 202
        
    except Exception as e:
        return jsonify({"message": f"Error al iniciar el proceso: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)