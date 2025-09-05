from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os
import tempfile # Importa el módulo para manejar archivos temporales
from automation_script import firmador_automation

app = Flask(__name__)
CORS(app)

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

        # Crea un directorio temporal para guardar los archivos
        temp_dir = tempfile.mkdtemp()
        file_paths = []
        for file in uploaded_files:
            file_path = os.path.join(temp_dir, file.filename)
            file.save(file_path)
            file_paths.append(file_path)

        # Inicia la automatización en un hilo separado
        thread = threading.Thread(
            target=firmador_automation,
            args=(cuit, password, otp_code, pin, file_paths)
        )
        thread.start()
        
        return jsonify({"message": "Proceso de firma iniciado."}), 202
        
    except Exception as e:
        return jsonify({"message": f"Error al iniciar el proceso: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)