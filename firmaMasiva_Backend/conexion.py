import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
# Ruta de la base de datos
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'firmadigital.db')

# Zona horaria de Argentina
ARGENTINA_TZ = timezone(timedelta(hours=-3))

def get_argentina_time():
    """Retorna la hora actual de Argentina"""
    return datetime.now(ARGENTINA_TZ)

@contextmanager

def get_db_connection():
    """Context manager para manejar conexiones a SQLite"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None):
    """Ejecuta una query y devuelve los resultados"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        return cursor.fetchall()

def execute_insert(query, params):
    """Ejecuta un INSERT y devuelve el ID del registro insertado"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid

def execute_update(query, params):
    """Ejecuta un UPDATE y devuelve el número de filas afectadas"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount

# ================================
# FUNCIONES ESPECÍFICAS PARA EL PROYECTO
# ================================

def validate_user(cuil):
    """Valida si un usuario está autorizado"""
    # Limpiar el CUIL de guiones, espacios y otros caracteres no numéricos
    cuil_clean = ''.join(filter(str.isdigit, cuil))
    
    query = '''
        SELECT cuil, responsable, path_carpetas, activo
        FROM usuarios_autorizados 
        WHERE cuil = ? AND activo = 1
    '''
    result = execute_query(query, (cuil_clean,))
    if result:
        return dict(result[0])
    return None

#def create_session(session_id, cuil, responsable, path_carpetas, total_files):
#    """Crea una nueva sesión de firma"""
#    query = '''
#        INSERT INTO firma_sessions (session_id, cuil, responsable, path_carpetas, total_files, status)
#        VALUES (?, ?, ?, ?, ?, 'processing')
#    '''
#    return execute_insert(query, (session_id, cuil, responsable, path_carpetas, total_files))

 # Modifica tus queries que usan CURRENT_TIMESTAMP:
def create_session(session_id, cuil, responsable, path_carpetas, total_files):
    """Crea una nueva sesión de firma"""
    argentina_time = get_argentina_time().strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        INSERT INTO firma_sessions (session_id, cuil, responsable, path_carpetas, total_files, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'processing', ?)
    '''
    return execute_insert(query, (session_id, cuil, responsable, path_carpetas, total_files, argentina_time))

def update_session_progress(session_id, files_processed):
    """Actualiza el progreso de una sesión"""
    query = '''
        UPDATE firma_sessions 
        SET files_processed = ?
        WHERE session_id = ?
    '''
    return execute_update(query, (files_processed, session_id))

def complete_session(session_id, status='completed', error_message=None):
    """Marca una sesión como completada o con error"""
    argentina_time = get_argentina_time().strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        UPDATE firma_sessions 
        SET status = ?, completed_at = ?, error_message = ?
        WHERE session_id = ?
    '''
    return execute_update(query, (status, argentina_time, error_message, session_id))

def get_session(session_id):
    """Obtiene información de una sesión"""
    query = '''
        SELECT * FROM firma_sessions WHERE session_id = ?
    '''
    result = execute_query(query, (session_id,))
    return dict(result[0]) if result else None

#def log_activity(session_id, level, message):
 #   """Registra actividad en los logs"""
 #   query = '''
 #       INSERT INTO activity_logs (session_id, level, message)
 #       VALUES (?, ?, ?)
 #   '''
 #   return execute_insert(query, (session_id, level, message))

def log_activity(session_id, level, message):
    """Registra actividad en los logs"""
    argentina_time = get_argentina_time().strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        INSERT INTO activity_logs (session_id, level, message, timestamp)
        VALUES (?, ?, ?, ?)
    '''
    return execute_insert(query, (session_id, level, message, argentina_time))

def create_processed_file(session_id, original_filename, file_size=None):
    """Registra un archivo que se está procesando"""
    argentina_time = get_argentina_time().strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        INSERT INTO processed_files (session_id, original_filename, file_size, status, created_at)
        VALUES (?, ?, ?, 'processing', ?)
    '''
    return execute_insert(query, (session_id, original_filename, file_size, argentina_time))

def complete_processed_file(session_id, original_filename, signed_filename, processing_time=None, status='completed', error_message=None):
    """Marca un archivo como procesado"""
    argentina_time = get_argentina_time().strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        UPDATE processed_files 
        SET signed_filename = ?, processing_time_seconds = ?, status = ?, 
            completed_at = ?, error_message = ?
        WHERE session_id = ? AND original_filename = ?
    '''
    return execute_update(query, (signed_filename, processing_time, status, argentina_time, error_message, session_id, original_filename))

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            print(f"Conexión exitosa a SQLite: {version}")
            return True
    except Exception as e:
        print(f"Error en conexión: {e}")
        return False