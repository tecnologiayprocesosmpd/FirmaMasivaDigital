from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import tempfile
import uuid
import shutil
# Importar desde tu archivo firma.py
from firma import firmador_automation
# NUEVO: Importar desde conexion.py
from conexion import validate_user, create_session, update_session_progress, complete_session, log_activity, create_processed_file, complete_processed_file

app = Flask(__name__)
CORS(app)

# Diccionario global para almacenar el progreso de cada sesión
progress_data = {}

def update_progress(session_id, current, total, current_file, message, status='processing'):
    """Función helper para actualizar el progreso"""
    if session_id in progress_data:
        progress_data[session_id] = {
            'current': current,
            'total': total,
            'status': status,
            'current_file': current_file,
            'message': message
        }
    
    # NUEVO: También actualizar en la base de datos
    try:
        update_session_progress(session_id, current)
        log_activity(session_id, 'INFO', message)
        if status == 'completed':
            complete_session(session_id, 'completed')
        elif status == 'error':
            complete_session(session_id, 'error', message)
    except Exception as e:
        print(f"Error actualizando BD: {e}")

def create_user_directory(path):
    """Crea el directorio del usuario si no existe"""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            return True, f"Directorio creado: {path}"
        return True, f"Directorio ya existe: {path}"
    except Exception as e:
        return False, f"Error creando directorio: {str(e)}"

def firmador_automation_wrapper(cuit, password, code, pin, file_paths, session_id, user_data):
    """Wrapper que ejecuta tu función original y actualiza el progreso"""
    try:
        update_progress(session_id, 0, len(file_paths), '', 'Iniciando proceso de firma...')
        
        # Registrar archivos en BD
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            create_processed_file(session_id, filename, file_size)
        
        # Agregar callback a la función para reportar progreso
        def progress_callback(current, total, filename, message):
            update_progress(session_id, current, total, filename, message)
            
            # Si completó un archivo, actualizarlo en BD
            if filename and 'completado' in message.lower():
                signed_filename = f"{os.path.splitext(filename)[0]}_firmado{os.path.splitext(filename)[1]}"
                complete_processed_file(session_id, filename, signed_filename, None, 'completed')
        
        # Asignar el callback a tu función
        firmador_automation.progress_callback = progress_callback
        
        # LLAMAR A TU FUNCIÓN ORIGINAL
        firmador_automation(cuit, password, code, pin, file_paths)
        
        update_progress(session_id, len(file_paths), len(file_paths), '', f'Proceso completado exitosamente. Archivos guardados en {user_data["path_carpetas"]}', 'completed')
        
    except Exception as e:
        update_progress(session_id, 0, len(file_paths), '', f'Error: {str(e)}', 'error')

# NUEVO ENDPOINT: Validar usuario
@app.route('/validate-user', methods=['POST'])
def validate_user_endpoint():
    """Endpoint para validar si un usuario puede usar el sistema"""
    try:
        data = request.get_json()
        cuil = data.get('cuil', '').strip()

        #sba agrego esta validacion
        cuil = ''.join(filter(str.isdigit, cuil))
        
        if not cuil:
            return jsonify({
                "valid": False,
                "message": "CUIL es requerido"
            }), 400

        # Validar usuario en la base de datos
        user_data = validate_user(cuil)
        
        if not user_data:
            return jsonify({
                "valid": False,
                "message": "Usuario no autorizado. Comuníquese con el área de sistemas para obtener acceso."
            }), 403

        # Verificar y crear directorio si es necesario
        directory_success, directory_message = create_user_directory(user_data['path_carpetas'])
        
        if not directory_success:
            return jsonify({
                "valid": False,
                "message": f"Error con el directorio del usuario: {directory_message}"
            }), 500

        return jsonify({
            "valid": True,
            "message": "Usuario autorizado",
            "user_data": {
                "cuil": user_data['cuil'],
                "responsable": user_data['responsable'],
                "path_carpetas": user_data['path_carpetas']
            },
            "directory_status": directory_message
        }), 200

    except Exception as e:
        return jsonify({
            "valid": False,
            "message": f"Error validando usuario: {str(e)}"
        }), 500

@app.route('/firmar', methods=['POST'])
def handle_firmar_request():
    try:
        # Generar ID único para esta sesión
        session_id = str(uuid.uuid4())
        
        # Obtener datos del formulario
        cuit = request.form.get('cuit')
        password = request.form.get('password')
        pin = request.form.get('pin')
        otp_code = request.form.get('otpCode')
        uploaded_files = request.files.getlist('files[]')

        if not all([cuit, password, pin, otp_code, uploaded_files]):
            return jsonify({"message": "Faltan datos o archivos requeridos."}), 400

        # NUEVO: VALIDAR USUARIO ANTES DE PROCESAR
        user_data = validate_user(cuit)
        if not user_data:
            return jsonify({
                "message": "Usuario no autorizado para utilizar el sistema. Comuníquese con el área de sistemas."
            }), 403

        # Verificar/crear directorio del usuario
        directory_success, directory_message = create_user_directory(user_data['path_carpetas'])
        if not directory_success:
            return jsonify({
                "message": f"Error preparando directorio del usuario: {directory_message}"
            }), 500

        # CREAR SESIÓN EN BD
        create_session(session_id, cuit, user_data['responsable'], user_data['path_carpetas'], len(uploaded_files))
        log_activity(session_id, 'INFO', f'Nueva sesión iniciada para {user_data["responsable"]} con {len(uploaded_files)} archivos')

        # Inicializar progreso
        progress_data[session_id] = {
            'current': 0,
            'total': len(uploaded_files),
            'status': 'initializing',
            'current_file': '',
            'message': 'Preparando archivos...',
            'responsable': user_data['responsable'],
            'path_carpetas': user_data['path_carpetas']
        }

        # Crear directorio temporal y guardar archivos
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        for file in uploaded_files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({"message": f"El archivo {file.filename} no es un PDF válido."}), 400
            
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            file_paths.append(file_path)

        # Iniciar proceso en hilo separado
        thread = threading.Thread(
            target=firmador_automation_wrapper,
            args=(cuit, password, otp_code, pin, file_paths, session_id, user_data)
        )
        thread.start()
        
        return jsonify({
            "message": "Proceso de firma iniciado.",
            "session_id": session_id,
            "responsable": user_data['responsable'],
            "directory_status": directory_message
        }), 202
        
    except Exception as e:
        return jsonify({"message": f"Error al iniciar el proceso: {str(e)}"}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Endpoint para obtener el progreso actual de una sesión"""
    if session_id in progress_data:
        return jsonify(progress_data[session_id])
    else:
        return jsonify({
            "error": "Sesión no encontrada",
            "current": 0,
            "total": 0,
            "status": "not_found",
            "current_file": "",
            "message": "Sesión no encontrada"
        }), 404

@app.route('/cleanup/<session_id>', methods=['DELETE'])
def cleanup_session(session_id):
    """Endpoint para limpiar los datos de una sesión terminada"""
    if session_id in progress_data:
        del progress_data[session_id]
        return jsonify({"message": "Sesión limpiada"}), 200
    return jsonify({"message": "Sesión no encontrada"}), 404

@app.route('/finish', methods=['POST'])
def finish_process():
    """Endpoint para finalizar el proceso y cerrar el navegador"""
    try:
        return jsonify({"message": "Proceso finalizado correctamente"}), 200
    except Exception as e:
        return jsonify({"message": f"Error al finalizar: {str(e)}"}), 500

@app.route('/reset', methods=['POST'])
def reset_process():
    """Endpoint para reiniciar el proceso y limpiar estados"""
    try:
        # Limpiar todos los datos de progreso
        global progress_data
        progress_data.clear()
        
        return jsonify({"message": "Sistema reiniciado correctamente"}), 200
    except Exception as e:
        return jsonify({"message": f"Error al reiniciar: {str(e)}"}), 500

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)