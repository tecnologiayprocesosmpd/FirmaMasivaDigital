import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

# ================================
# CONFIGURACIÓN DE POSTGRESQL
# ================================
DB_CONFIG = {
    'host': '172.24.120.80',        # Ej: '192.168.1.100'
    'port': '5432',
    'database': 'firmadigital',       # Ej: 'firmadigital'
    'user': 'postgres',              # Ej: 'postgres'
    'password': 'defen$a2019'          # Tu contraseña
}

# Zona horaria de Argentina
ARGENTINA_TZ = timezone(timedelta(hours=-3))

def get_argentina_time():
    """Retorna la hora actual de Argentina"""
    return datetime.now(ARGENTINA_TZ)

@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a PostgreSQL"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None):
    """Ejecuta una query y devuelve los resultados"""
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
        return cursor.fetchone()[0] if cursor.description else None

def execute_update(query, params):
    """Ejecuta un UPDATE y devuelve el número de filas afectadas"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount

# ================================
# FUNCIONES ESPECÍFICAS PARA EL PROYECTO
# ADAPTADAS A LAS TABLAS POSTGRESQL
# ================================

def validate_user(cuil):
    """Valida si un usuario está autorizado"""
    # Limpiar el CUIL de guiones, espacios y otros caracteres no numéricos
    cuil_clean = ''.join(filter(str.isdigit, cuil))
    
    query = '''
        SELECT "fUserAutCuil", "fUserAutResponsable", "fUserAutPathCarpetas", "fUserAutActivo"
        FROM public."fUserAut" 
        WHERE "fUserAutCuil" = %s AND "fUserAutActivo" = true
    '''
    result = execute_query(query, (cuil_clean,))
    if result:
        # Convertir nombres PostgreSQL a nombres esperados por app.py
        user_data = dict(result[0])
        return {
            'cuil': user_data['fUserAutCuil'],
            'responsable': user_data['fUserAutResponsable'],
            'path_carpetas': user_data['fUserAutPathCarpetas'],
            'activo': user_data['fUserAutActivo']
        }
    return None

def create_session(session_id, cuil, responsable, path_carpetas, total_files):
    """Crea una nueva sesión de firma"""
    argentina_time = get_argentina_time()
    query = '''
        INSERT INTO public."fSession" 
        ("fSessionSessionId", "fSessionCuil", "fSessionResponsable", "fSessionPathCarpetas", 
         "fSessionTotalFiles", "fSessionStatus", "fSessionCreatedAt")
        VALUES (%s, %s, %s, %s, %s, 'processing', %s)
        RETURNING "fSessionId"
    '''
    result = execute_query(query, (session_id, cuil, responsable, path_carpetas, total_files, argentina_time))
    return result[0]['fSessionId'] if result else None

def update_session_progress(session_id, files_processed):
    """Actualiza el progreso de una sesión"""
    query = '''
        UPDATE public."fSession" 
        SET "fSessionFilesProcessed" = %s
        WHERE "fSessionSessionId" = %s
    '''
    return execute_update(query, (files_processed, session_id))

def complete_session(session_id, status='completed', error_message=None):
    """Marca una sesión como completada o con error"""
    argentina_time = get_argentina_time()
    query = '''
        UPDATE public."fSession" 
        SET "fSessionStatus" = %s, "fSessionCompleteAt" = %s, "fSessionErrorMessage" = %s
        WHERE "fSessionSessionId" = %s
    '''
    return execute_update(query, (status, argentina_time, error_message, session_id))

def get_session(session_id):
    """Obtiene información de una sesión"""
    query = '''
        SELECT "fSessionId", "fSessionSessionId", "fSessionCuil", "fSessionResponsable",
               "fSessionPathCarpetas", "fSessionTotalFiles", "fSessionFilesProcessed",
               "fSessionStatus", "fSessionCreatedAt", "fSessionCompleteAt", "fSessionErrorMessage"
        FROM public."fSession" 
        WHERE "fSessionSessionId" = %s
    '''
    result = execute_query(query, (session_id,))
    if result:
        # Convertir nombres PostgreSQL a nombres esperados por app.py
        session_data = dict(result[0])
        return {
            'id': session_data['fSessionId'],
            'session_id': session_data['fSessionSessionId'],
            'cuil': session_data['fSessionCuil'],
            'responsable': session_data['fSessionResponsable'],
            'path_carpetas': session_data['fSessionPathCarpetas'],
            'total_files': session_data['fSessionTotalFiles'],
            'files_processed': session_data['fSessionFilesProcessed'],
            'status': session_data['fSessionStatus'],
            'created_at': session_data['fSessionCreatedAt'],
            'completed_at': session_data['fSessionCompleteAt'],
            'error_message': session_data['fSessionErrorMessage']
        }
    return None

def log_activity(session_id, level, message):
    """Registra actividad en los logs"""
    argentina_time = get_argentina_time()
    query = '''
        INSERT INTO public."fActvLog" 
        ("fActvLogSessionId", "fActvLogLevel", "fActvLogMessage", "fActvLogTimestamp")
        VALUES (%s, %s, %s, %s)
        RETURNING "fActvLogid"
    '''
    result = execute_query(query, (session_id, level, message, argentina_time))
    return result[0]['fActvLogid'] if result else None

def create_processed_file(session_id, original_filename, file_size=None, cuil=None):
    """Registra un archivo que se está procesando con información real del sistema"""
    import socket
    import getpass
    
    argentina_time = get_argentina_time()
    
    # Obtener datos REALES de auditoría
    hostname = socket.gethostname()
    username = getpass.getuser()
    
    try:
        log_ip = socket.gethostbyname(hostname)
    except:
        log_ip = "127.0.0.1"
    
    query = '''
            INSERT INTO public."fLog" 
            ("fLogSessionId", "fLogOriginalFilename", "fLogFileSize", "fLogStatus", 
            "fLogCreatedAt", "fLogLogip", "fLogLogpc", "fLogLogusuario", "fLogCuil")
            VALUES (%s, %s, %s, 'processing', %s, %s, %s, %s, %s)
            RETURNING "fLogId"
        '''
    result = execute_query(query, (session_id, original_filename, file_size, argentina_time, log_ip, hostname, username, cuil))
    return result[0]['fLogId'] if result else None

def complete_processed_file(session_id, original_filename, signed_filename, processing_time=None, status='completed', error_message=None):
    """Marca un archivo como procesado"""
    argentina_time = get_argentina_time()
    query = '''
        UPDATE public."fLog" 
        SET "fLogSignedFilename" = %s, "fLogProcessingTimeSeconds" = %s, "fLogStatus" = %s, 
            "fLogCompletedAt" = %s, "fLogErrorMessage" = %s
        WHERE "fLogSessionId" = %s AND "fLogOriginalFilename" = %s
    '''
    return execute_update(query, (signed_filename, processing_time, status, argentina_time, error_message, session_id, original_filename))

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"Conexión exitosa a PostgreSQL: {version}")
            return True
    except Exception as e:
        print(f"Error en conexión: {e}")
        return False

# ================================
# FUNCIONES ADICIONALES PARA POSTGRESQL
# ================================

def get_user_sessions(cuil, limit=20):
    """Obtiene el historial de sesiones de un usuario"""
    query = '''
        SELECT "fSessionSessionId", "fSessionTotalFiles", "fSessionFilesProcessed",
               "fSessionStatus", "fSessionCreatedAt", "fSessionCompleteAt"
        FROM public."fSession" 
        WHERE "fSessionCuil" = %s 
        ORDER BY "fSessionCreatedAt" DESC 
        LIMIT %s
    '''
    result = execute_query(query, (cuil, limit))
    return [dict(row) for row in result] if result else []

def cleanup_old_sessions(days=30):
    """Elimina sesiones antiguas"""
    query = '''
        DELETE FROM public."fSession"
        WHERE "fSessionCreatedAt" < CURRENT_TIMESTAMP - INTERVAL '%s days'
    '''
    return execute_update(query, (days,))

def cleanup_old_logs(days=7):
    """Elimina logs antiguos"""
    query = '''
        DELETE FROM public."fActvLog"
        WHERE "fActvLogTimestamp" < CURRENT_TIMESTAMP - INTERVAL '%s days'
    '''
    return execute_update(query, (days,))