import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from time import sleep
import threading
import os
import glob
import time

# Variable global para los archivos seleccionados
selected_files = []

def select_files():
    """Abre un diálogo para que el usuario seleccione archivos PDF y los muestra en la consola."""
    global selected_files
    filetypes = [("PDF files", "*.pdf")]
    file_paths = filedialog.askopenfilenames(title="Seleccionar archivos PDF", filetypes=filetypes)
    
    if file_paths:
        selected_files = list(file_paths)
        messagebox.showinfo("Archivos Seleccionados", f"Se han seleccionado {len(selected_files)} archivo(s).")
        
        print("Archivos seleccionados:")
        for file in selected_files:
            print(f"- {file}")
    else:
        selected_files = []
        print("No se seleccionaron archivos.")

def create_login_window():
    """
    Crea y muestra la ventana de login con cuatro campos de entrada.
    """
    window = tk.Tk()
    window.title("Login Firmador")
    window.geometry("500x400")
    window.eval('tk::PlaceWindow . center')

    style = ttk.Style(window)
    style.theme_use('vista') 
    style.configure("TLabel", font=("Arial", 10))
    style.configure("TButton", font=("Arial", 10, "bold"))

    main_frame = ttk.Frame(window, padding="20")
    main_frame.pack(expand=True, fill="both")

    ttk.Label(main_frame, text="CUIT").pack(pady=(0, 5))
    cuit_entry = ttk.Entry(main_frame)
    cuit_entry.pack(fill="x", pady=(0, 10))
    
    ttk.Label(main_frame, text="Contraseña").pack(pady=(0, 5))
    password_entry = ttk.Entry(main_frame, show="*")
    password_entry.pack(fill="x", pady=(0, 10))
    
    ttk.Label(main_frame, text="Código").pack(pady=(0, 5))
    code_entry = ttk.Entry(main_frame, show="*")
    code_entry.pack(fill="x", pady=(0, 10))
    
    ttk.Label(main_frame, text="PIN").pack(pady=(0, 5))
    pin_entry = ttk.Entry(main_frame, show="*")
    pin_entry.pack(fill="x", pady=(0, 10))

    select_button = ttk.Button(main_frame, text="Seleccionar Archivos PDF", command=select_files)
    select_button.pack(pady=(10, 5), fill="x")

    def on_submit():
        cuit = cuit_entry.get()
        password = password_entry.get()
        code = code_entry.get()
        pin = pin_entry.get()

        if not all([cuit, password, code, pin]):
            messagebox.showerror("Error", "Todos los campos deben ser completados.")
            return
        
        window.destroy()

        automation_thread = threading.Thread(
            target=firmador_automation,
            args=(cuit, password, code, pin, selected_files)
        )
        automation_thread.start()

    submit_button = ttk.Button(main_frame, text="Acceder", command=on_submit)
    submit_button.pack(pady=20, fill="x")

    window.mainloop()

# La función auxiliar se ha corregido para buscar el archivo más reciente y eliminar el código duplicado
def wait_for_download_and_rename(download_dir, new_filename):
    """
    Espera a que un nuevo archivo se descargue en el directorio y luego lo renombra.
    """
    timeout = 60
    start_time = time.time()
    
    # Obtener el listado inicial de archivos en el directorio
    initial_files = set(os.listdir(download_dir))
    
    # Esperar hasta que un nuevo archivo aparezca en la carpeta
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = list(current_files - initial_files)
        
        # Filtrar archivos temporales de descarga
        newly_downloaded_files = [f for f in new_files if not f.endswith('.crdownload')]
        
        if newly_downloaded_files:
            downloaded_file = os.path.join(download_dir, newly_downloaded_files[0])
            
            # Renombrar el archivo encontrado
            os.rename(downloaded_file, os.path.join(download_dir, new_filename))
            print(f"Descarga completa. Archivo renombrado a {new_filename}.")
            return
            
        sleep(0.5)
        
    raise TimeoutException("El archivo no se descargó a tiempo.")
    
def firmador_automation(cuit, password, code, pin, files_to_upload, user_path):
    """
    Automatiza el proceso de login y firma en la página firmar.gob.ar.
    """
    # **Mover la configuración del navegador aquí dentro de la función**
    download_dir = user_path 
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options = webdriver.ChromeOptions()

     # AGREGO ESTAS LÍNEAS PARA MODO FANTASMA EN EL NAVEGADOR "HEADLESS":
    options.add_argument('--headless')  # Ejecutar sin ventana visible
    options.add_argument('--no-sandbox')  # Mejorar compatibilidad
    options.add_argument('--disable-dev-shm-usage')  # Evitar problemas de memoria

    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    service = Service(ChromeDriverManager().install())
    browser = None
    try:
        browser = webdriver.Chrome(service=service, options=options)
        browser.get("https://firmar.gob.ar/firmador/#/")
        
        # --- ETAPA 1: Login con CUIT y Contraseña ---
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "inputCUIL"))
        )
        cuit_input = browser.find_element(By.ID, "inputCUIL")
        cuit_input.send_keys(cuit)
        
        password_input = browser.find_element(By.ID, "inputPass")
        password_input.send_keys(password)
        
        acceder_button_stage1 = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acceder')]"))
        )
        acceder_button_stage1.click()
        print("Botón 'Acceder' de la etapa 1 presionado.")
        
        # --- ETAPA 2: Ingresar Código ---
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "inputOtp"))
        )
        print("Campos de la etapa 2 encontrados.")
        
        code_input = browser.find_element(By.ID, "inputOtp")
        code_input.send_keys(code)
        
        acceder_button_stage2 = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acceder')]"))
        )
        acceder_button_stage2.click()
        print("Botón 'Acceder' de la etapa 2 presionado. Login completado.")
        
        # --- ETAPA 3: Bucle para cada archivo ---
        if files_to_upload:
            for i, file_path in enumerate(files_to_upload):
                print(f"\nProcesando archivo: {file_path}")

                # AGREGAR ESTAS 3 LÍNEAS para reportar progreso:
                if hasattr(firmador_automation, 'progress_callback'):
                    filename = os.path.basename(file_path)
                    firmador_automation.progress_callback(i, len(files_to_upload), filename, f'Procesando {filename}...')
                
                # Esperar a que el input de tipo file sea visible
                file_uploader = WebDriverWait(browser, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                
                file_uploader.send_keys(file_path)
                print("Archivo adjuntado.")

                # Esperar a que el campo del PIN aparezca
                pin_input = WebDriverWait(browser, 15).until(
                    EC.presence_of_element_located((By.ID, "inputPin"))
                )
                
                pin_input.send_keys(pin)
                print("PIN ingresado.")
                
                # Esperar a que el botón "Firmar" sea clicable
                firmar_button = WebDriverWait(browser, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Firmar')]"))
                )
                firmar_button.click()
                print("Botón 'Firmar' presionado.")
                sleep(2)
                # Esperar a que el botón "Descargar" aparezca
                descargar_button = WebDriverWait(browser, 30).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Descargar documento')]"))
                ) 
                
                # OBTENER EL NOMBRE DEL ARCHIVO ORIGINAL
                original_filename = os.path.basename(file_path)
                base_name, file_extension = os.path.splitext(original_filename)
                new_filename = f"{base_name}_firmado{file_extension}"
                
                print("Iniciando la descarga...")
                descargar_button.click()

                # **LLAMADA CORREGIDA**
                wait_for_download_and_rename(download_dir, new_filename)
                
                print(f"Archivo {original_filename} renombrado a {new_filename} y guardado en {download_dir}")
                # AGREGAR ESTAS 2 LÍNEAS AQUÍ:
                if hasattr(firmador_automation, 'progress_callback'):
                    firmador_automation.progress_callback(i + 1, len(files_to_upload), original_filename, f'{original_filename} completado')

                
                # Regresar a la pantalla de carga para el siguiente archivo
                browser.back()
                # **Añadir una espera para permitir que la página se cargue de nuevo**
                sleep(2)
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )

        else:
            print("No se seleccionaron archivos para adjuntar. Proceso de firma omitido.")
        
        # while True:
          #  try:
           #     browser.title
            #    sleep(2)
           # except WebDriverException:
           #     print("El navegador ha sido cerrado. Deteniendo el programa.")
            #    break
            # Opcional: mantener el navegador abierto por unos segundos para ver el resultado
        print("Proceso completado. Cerrando navegador en 3 segundos...")
        sleep(3)    
    except TimeoutException:
        print("Error: No se encontraron los elementos de la página a tiempo.")
        messagebox.showerror("Error", "No se pudo cargar la página o los elementos.")
    except IndexError:
        print("Error: No se seleccionaron archivos. No se puede proceder con la firma.")
        messagebox.showerror("Error", "No se seleccionaron archivos.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        messagebox.showerror("Error", f"Ocurrió un error durante la automatización: {e}")
    finally:
        if browser:
            browser.quit()

if __name__ == "__main__":
    create_login_window()