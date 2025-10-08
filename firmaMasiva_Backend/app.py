from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import tempfile
import uuid
import subprocess
import platform
import shutil
import socket
import time

# Importar desde tus archivos
from firma import firmador_automation
from conexionPosgre import validate_user, create_session, update_session_progress, complete_session, log_activity, create_processed_file, complete_processed_file

app = Flask(__name__)
CORS(app)

progress_data = {}

def update_progress(session_id, current, total, current_file, message, status):
    """Función helper para actualizar el progreso local y en la base de datos."""
    if session_id in progress_data:
        progress_data[session_id] = {
            'current': current,
            'total': total,
            'status': status,
            'current_file': current_file,
            'message': message
        }
    try:
        update_session_progress(session_id, current)
        log_activity(session_id, 'INFO', message)
        if status in ['completed', 'error']:
            complete_session(session_id, status, message)
    except Exception as e:
        if not check_internet_connection():
            # Si no hay internet, establecemos el mensaje de error amigable
            friendly_message = "Error de conexión a internet. Se perdió la conexión al intentar guardar el progreso."
            
            # Actualizamos el progreso local con el mensaje amigable (la BD no se actualizará)
            if session_id in progress_data:
                progress_data[session_id] = {
                    'current': current,
                    'total': total,
                    'status': 'error', # Cambia el estado a error
                    'current_file': current_file,
                    'message': friendly_message
                }
            
            print(f"ERROR: No se pudo actualizar la BD, se detectó pérdida de conexión a internet. Mensaje: {friendly_message}")
            
            # Lanzamos una excepción para detener el proceso en el hilo
            raise ConnectionError(friendly_message)
            
        else:
            # Si hay internet pero falla la BD, es un error de configuración de BD o servidor
            print(f"Error crítico actualizando BD, pero hay internet: {e}")
            raise Exception(f"Error crítico en la base de datos: {str(e)}")

def create_user_directory(path):
    """Crea el directorio del usuario si no existe."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            return True, f"Directorio creado: {path}"
        return True, f"Directorio ya existe: {path}"
    except Exception as e:
        return False, f"Error creando directorio: {str(e)}"

def firmador_automation_wrapper(cuit, password, code, pin, file_paths, session_id, user_data):
    """
    Wrapper que ejecuta la función de firma y maneja las actualizaciones de progreso.
    """
    temp_dir = os.path.dirname(file_paths[0]) if file_paths else None
    archivos_exitosos = 0  # Contador de archivos realmente completados
    
    try:
        if not check_internet_connection():
            raise Exception("No hay conexión a internet. Verifique su red.")
            
        total_files = len(file_paths)
        update_progress(session_id, 0, total_files, '', 'Iniciando proceso de firma...', 'initializing')
        
        # Registrar archivos en BD
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            create_processed_file(session_id, filename, file_size, cuit)

        # Llamar UNA SOLA VEZ con todos los archivos
        message = f'Iniciando proceso de firma para {total_files} archivos'
        update_progress(session_id, 0, total_files, '', message, 'processing')
        
        # se agrega estas lineas para reportar progreso
        def progress_callback(current, total, filename, message):
            nonlocal archivos_exitosos
            # Contar archivos exitosos cuando se completan
            if 'completado' in message.lower():
                archivos_exitosos = current
            update_progress(session_id, current, total, filename, message, 'processing')
    
        firmador_automation.progress_callback = progress_callback
        
        # Ejecutar proceso de firma
        firmador_automation(cuit, password, code, pin, file_paths, user_data['path_carpetas'])

        # Marcar todos como completados al final
        for file_path in file_paths:
            current_filename = os.path.basename(file_path)
            complete_processed_file(session_id, current_filename, 'completed')

        # Actualización final de progreso
        message = f'Proceso completado exitosamente. {archivos_exitosos} archivos guardados en {user_data["path_carpetas"]}'
        update_progress(session_id, total_files, total_files, '', message, 'completed')
        
        # Log de éxito
        log_activity(session_id, 'SUCCESS', f'Proceso completado: {archivos_exitosos}/{total_files} archivos')

    except ConnectionError as e:
        # Error específico lanzado por update_progress cuando se detecta pérdida de internet
        error_message = str(e)
        
        # Mensaje con contador de exitosos
        if archivos_exitosos > 0:
            final_message = f'Conexión perdida. Se completaron {archivos_exitosos} de {len(file_paths)} archivos. {error_message}'
        else:
            final_message = error_message
        
        update_progress(session_id, archivos_exitosos, len(file_paths), '', final_message, 'error')
        
        # Ya se actualizó progress_data dentro de update_progress, pero nos aseguramos del log
        log_activity(session_id, 'ERROR', f'Conexión perdida en archivo {archivos_exitosos + 1}/{len(file_paths)}. {error_message}')
        
        # Intentar completar la sesión en la BD, aunque pueda fallar si la conexión sigue abajo
        try:
            complete_session(session_id, 'error', final_message)
        except:
            pass
            
    except Exception as e:
        # Error general (código incorrecto, timeout de Selenium, error de ruta, etc.)
        error_message = str(e)
        
        # Determinar cuántos se procesaron exitosamente
        if archivos_exitosos > 0:
            final_message = f'Proceso interrumpido. Se completaron {archivos_exitosos} de {len(file_paths)} archivos. Error: {error_message}'
        else:
            final_message = f'Error al iniciar el proceso: {error_message}'
        
        update_progress(session_id, archivos_exitosos, len(file_paths), '', final_message, 'error')
        log_activity(session_id, 'ERROR', f'Error en archivo {archivos_exitosos + 1}/{len(file_paths)}. {error_message}')
        
        # Intentar completar sesión en BD
        try:
            complete_session(session_id, 'error', final_message)
        except:
            pass
        
    finally:
        # Limpiar el directorio temporal al finalizar, con o sin error.
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.route('/validate-user', methods=['POST'])
def validate_user_endpoint():
    """Endpoint para validar si un usuario puede usar el sistema."""
    if not check_internet_connection():
        return jsonify({
            "valid": False,
            "message": "Sin conexión a internet. Revisa tu red e inténtalo de nuevo."
        }), 503
    
    try:
        data = request.get_json()
        cuil = ''.join(filter(str.isdigit, data.get('cuil', '').strip()))
        
        if not cuil:
            return jsonify({
                "valid": False,
                "message": "CUIL es requerido"
            }), 400

        user_data = validate_user(cuil)
        
        if not user_data:
            return jsonify({
                "valid": False,
                "message": "Usuario no autorizado. Comunícate con el área de sistemas para obtener acceso."
            }), 403

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
    session_id = None
    try:
        session_id = str(uuid.uuid4())
        
        cuit = request.form.get('cuit')
        password = request.form.get('password')
        pin = request.form.get('pin')
        otp_code = request.form.get('otpCode')
        uploaded_files = request.files.getlist('files[]')

        if not all([cuit, password, pin, otp_code, uploaded_files]):
            return jsonify({"message": "Faltan datos o archivos requeridos."}), 400

        user_data = validate_user(cuit)
        if not user_data:
            return jsonify({
                "message": "Usuario no autorizado para utilizar el sistema."
            }), 403

        directory_success, directory_message = create_user_directory(user_data['path_carpetas'])
        if not directory_success:
            return jsonify({
                "message": f"Error preparando directorio del usuario: {directory_message}"
            }), 500

        create_session(session_id, cuit, user_data['responsable'], user_data['path_carpetas'], len(uploaded_files))
        
        progress_data[session_id] = {
            'current': 0,
            'total': len(uploaded_files),
            'status': 'initializing',
            'current_file': '',
            'message': 'Preparando archivos...',
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
        message = f"Error al iniciar el proceso: {str(e)}"
        if session_id and session_id in progress_data:
            update_progress(session_id, 0, 0, '', message, 'error')
        elif session_id:
            try:
                complete_session(session_id, 'error', message)
            except:
                pass
        return jsonify({"message": message}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Endpoint para obtener el progreso actual de una sesión."""
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
    """Endpoint para limpiar los datos de una sesión terminada."""
    if session_id in progress_data:
        del progress_data[session_id]
        return jsonify({"message": "Sesión limpiada"}), 200
    return jsonify({"message": "Sesión no encontrada"}), 404

@app.route('/abrir-carpeta', methods=['POST'])
def abrir_carpeta():
    """Endpoint para abrir la carpeta donde se guardaron los archivos."""
    try:
        data = request.get_json()
        ruta = data.get('ruta')
        
        if not ruta:
            return jsonify({
                "success": False, 
                "error": "No se proporcionó una ruta"
            }), 400
        
        if not os.path.exists(ruta):
            return jsonify({
                "success": False, 
                "error": f"La carpeta no existe: {ruta}"
            }), 400
        
        sistema = platform.system()
        
        if sistema == "Windows":
            subprocess.run(['explorer', ruta], check=True)
        elif sistema == "Darwin":  # macOS
            subprocess.run(['open', ruta], check=True)
        elif sistema == "Linux":
            subprocess.run(['xdg-open', ruta], check=True)
        else:
            return jsonify({
                "success": False, 
                "error": f"Sistema operativo no soportado: {sistema}"
            }), 400
        
        return jsonify({
            "success": True, 
            "message": f"Carpeta abierta exitosamente: {ruta}"
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({
            "success": False, 
            "error": f"Error al ejecutar comando del sistema: {str(e)}"
        }), 500
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"Error inesperado: {str(e)}"
        }), 500

def check_internet_connection(timeout=3):
    """Verifica la conexión a internet intentando conectar a Google."""
    try:
        socket.create_connection(("www.google.com", 80), timeout)
        return True
    except OSError:
        pass
    return False

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)