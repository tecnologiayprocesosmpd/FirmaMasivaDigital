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
import requests
import psycopg2 
import getpass
from threading import Thread, Event 

# Importar desde tus archivos
from firma import firmador_automation
from conexionPosgre import validate_user, create_session, update_session_progress, complete_session, log_activity, create_processed_file, complete_processed_file

# Define tu excepción para la pérdida de conexión
class NoInternetConnectionError(Exception):
    """Excepción personalizada para indicar la pérdida de conexión a internet."""
    pass

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
        print(f"Error actualizando BD: {e}")

def create_user_directory(path):
    """Crea el directorio del usuario si no existe."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            return True, f"Directorio creado: {path}"
        return True, f"Directorio ya existe: {path}"
    except Exception as e:
        return False, f"Error creando directorio: {str(e)}"

def check_internet_connection(timeout=3, raise_exception=False):
    """Verifica la conexión a internet intentando conectar a Google."""
    try:
        # Usamos requests.head para una solicitud más rápida.
        # Intentamos un HEAD request al sitio de firma, que es el recurso clave
        requests.head("https://firmar.gob.ar", timeout=5) # Reducimos el timeout a 5 segundos
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False
    except Exception: # Captura otros posibles errores de red/socket
        return False


def check_connection_status():
    """Verifica el estado de la conexión a internet y la BD (si se puede)."""
    if not check_internet_connection():
        raise NoInternetConnectionError("Se perdió la conexión a Internet durante el proceso.")
    # Puedes agregar aquí un chequeo simple a la BD si es necesario
    # try:
    #     some_db_check_function()
    # except Exception:
    #     raise Exception("Se perdió la conexión con la base de datos.")

class ConnectionMonitor(Thread):
    def __init__(self, session_id, interval=5):
        super().__init__()
        self.session_id = session_id
        self.interval = interval
        self.stop_event = Event()
        self.connection_lost = False

    def run(self):
        # Monitorear después de un pequeño retraso para asegurar que Selenium arrancó
        time.sleep(self.interval) 
        
        while not self.stop_event.is_set():
            if not check_internet_connection():
                self.connection_lost = True
                # Notificar el error en el progreso
                update_progress(
                    self.session_id, 
                    progress_data[self.session_id]['current'], 
                    progress_data[self.session_id]['total'], 
                    progress_data[self.session_id]['current_file'], 
                    'CONEXIÓN PERDIDA - Detectado por monitor. Intentando detener proceso.', 
                    'error'
                )
                self.stop_event.set() # Detiene el propio monitor
                break
            
            # Espera activa: si el evento se detiene (proceso terminó), salimos.
            self.stop_event.wait(self.interval) 

    def stop(self):
        self.stop_event.set()

def firmador_automation_wrapper(cuit, password, code, pin, file_paths, session_id, user_data):
    """
    Wrapper que ejecuta la función de firma y maneja las actualizaciones de progreso.
    """
    # Capturar información del sistema
    hostname = socket.gethostname()
    username = getpass.getuser() 
    # Log con información real del sistema
    log_activity(session_id, 'INFO', f'Proceso iniciado por {username} desde {hostname}')

    temp_dir = os.path.dirname(file_paths[0]) if file_paths else None

    monitor = ConnectionMonitor(session_id)
    monitor.start()
    
    try:
        total_files = len(file_paths)
        update_progress(session_id, 0, total_files, '', 'Iniciando proceso de firma...', 'initializing')
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
            create_processed_file(session_id, filename, file_size)

       # Llamar UNA SOLA VEZ con todos los archivos
        message = f'Iniciando proceso de firma para {total_files} archivos'
        update_progress(session_id, 0, total_files, '', message, 'processing')
     # se agrega estas lineas para reportar progreso
        def progress_callback(current, total, filename, message):
            update_progress(session_id, current, total, filename, message, 'processing')
    
        firmador_automation.progress_callback = progress_callback
        
        firmador_automation(cuit, password, code, pin, file_paths, user_data['path_carpetas'], monitor)

        # Marcar todos como completados al final
        for file_path in file_paths:
            current_filename = os.path.basename(file_path)
            complete_processed_file(session_id, current_filename, 'completed')

        # Actualización final de progreso
        message = f'Proceso completado exitosamente. Archivos guardados en {user_data["path_carpetas"]}'
        update_progress(session_id, total_files, total_files, '', message, 'completed')

    except NoInternetConnectionError: 
        error_message = '¡CONEXIÓN PERDIDA! Se interrumpió la conexión a Internet o al sitio de firma.'
        
        update_progress(session_id, 0, len(file_paths), '', error_message, 'error')
        try:
            log_activity(session_id, 'FATAL', error_message)
        except:
            print("Fallo al registrar actividad de conexión en BD, continuando...")
    
    except Exception as e:
        # ... (manejo de errores existente) ...
        
        # 💥 CLAVE: Si el monitor detectó el error, lo sobreescribimos.
        if monitor.connection_lost:
            error_message = '¡CONEXIÓN PERDIDA! El monitor de red detuvo el proceso.'
            update_progress(session_id, 0, len(file_paths), '', error_message, 'error')
            # ... (manejo de log y BD) ...
        
    finally:
        # --- Nuevo: Detener y limpiar el monitor ---
        monitor.stop()
        monitor.join() 
        # ... (limpieza de directorio temporal) ...
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
        
        if not check_internet_connection():
            return jsonify({
                "message": "Sin conexión a internet. Revisa tu red e inténtalo de nuevo."
            }), 503

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
            original_filename = file.filename
            
            try:
                # Decodificar el nombre de archivo (comúnmente Latin-1 en Windows)
                if isinstance(original_filename, bytes):
                    filename = original_filename.decode('latin-1')
                else:
                    filename = original_filename
            except Exception:
                # Si falla, forzar un nombre ASCII seguro
                filename = original_filename.encode('ascii', 'ignore').decode('ascii')
            
            # Reemplazar caracteres no permitidos en el path
            safe_filename = filename.replace(':', '_').replace('/', '_').replace('\\', '_')
            
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
        # Aquí capturas el error de codificación si ocurre después de la verificación.
        # Es mejor asegurar que el mensaje de error sea seguro (solo ASCII).
        
        # Manejo más seguro del error
        raw_message = str(e)
        
        # Intentamos decodificar el mensaje de error de forma segura antes de incluirlo en el JSON
        try:
            # Intentar decodificar el error de forma segura (ignora los bytes malos)
            safe_message = raw_message.encode('latin-1', 'replace').decode('utf-8', 'ignore')
            message = f"Error al iniciar el proceso: {safe_message}"
        except:
            # En caso de que falle la decodificación de seguridad, usar un mensaje simple
            message = "Error al iniciar el proceso: Falla de codificación interna (revisa el log)."

        # Si se pudo obtener una ID, actualizamos el estado en la BD
        if session_id:
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

# Mantenemos tu excepción personalizada
class NoInternetConnectionError(Exception):
    """Excepción personalizada para indicar la pérdida de conexión a internet."""
    pass

if __name__ == '__main__':
    print("Iniciando servidor Flask...")
    app.run(port=5000, debug=True)