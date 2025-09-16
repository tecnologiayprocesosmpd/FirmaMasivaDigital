import pyodbc

# Configura tu cadena de conexión aquí. Asegúrate de que el 'DRIVER' sea el correcto para tu sistema.
CONNECTION_STRING = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DESKTOP-4PV1O46\\SQLEXPRESS;'
    'DATABASE=Firmas;'
    'Trusted_Connection=yes;'
)

def get_user_data_by_cuit(cuil):
    """
    Obtiene la ruta y el responsable para un CUIT dado.
    """
    conn = None
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Consulta las columnas 'path' y 'responsable' de la tabla 'bo.signature'
        cursor.execute("SELECT responsable, path FROM dbo.signature WHERE cuil = ?", (cuil,))
        
        result = cursor.fetchone()
        
        if result:
            # Devuelve un diccionario con los datos
            return {
                'responsable': result.responsable,
                'path': result.path
            }
        
        return None  # Retorna None si no se encuentra el CUIT
        
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Error de base de datos: {sqlstate}")
        return None
    finally:
        if conn:
            conn.close()