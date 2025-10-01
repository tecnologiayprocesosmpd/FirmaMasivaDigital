import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import threading
import os
import glob
import time
import requests

# Variable global for selected files
selected_files = []


def select_files():
    """Opens a dialog for the user to select PDF files and shows them in the console."""
    global selected_files
    filetypes = [("PDF files", "*.pdf")]
    file_paths = filedialog.askopenfilenames(title="Select PDF files", filetypes=filetypes)
    
    if file_paths:
        selected_files = list(file_paths)
        messagebox.showinfo("Selected Files", f"You have selected {len(selected_files)} file(s).")
        
        print("Selected files:")
        for file in selected_files:
            print(f"- {file}")
    else:
        selected_files = []
        print("No files were selected.")

def create_login_window():
    """
    Creates and shows the login window with four input fields.
    """
    window = tk.Tk()
    window.title("Login Signer")
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
    
    ttk.Label(main_frame, text="Password").pack(pady=(0, 5))
    password_entry = ttk.Entry(main_frame, show="*")
    password_entry.pack(fill="x", pady=(0, 10))
    
    ttk.Label(main_frame, text="Code").pack(pady=(0, 5))
    code_entry = ttk.Entry(main_frame, show="*")
    code_entry.pack(fill="x", pady=(0, 10))
    
    ttk.Label(main_frame, text="PIN").pack(pady=(0, 5))
    pin_entry = ttk.Entry(main_frame, show="*")
    pin_entry.pack(fill="x", pady=(0, 10))

    select_button = ttk.Button(main_frame, text="Select PDF Files", command=select_files)
    select_button.pack(pady=(10, 5), fill="x")

    def on_submit():
        cuit = cuit_entry.get()
        password = password_entry.get()
        code = code_entry.get()
        pin = pin_entry.get()
        
        # Define the download path for the user
        user_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        if not all([cuit, password, code, pin]):
            messagebox.showerror("Error", "All fields must be filled.")
            return
        
        window.destroy()

        automation_thread = threading.Thread(
            target=firmador_automation,
            args=(cuit, password, code, pin, selected_files, user_path)
        )
        automation_thread.start()

    submit_button = ttk.Button(main_frame, text="Access", command=on_submit)
    submit_button.pack(pady=20, fill="x")

    window.mainloop()

# --- Utility Functions ---

def get_next_filename(download_dir, filename_without_ext, extension):
    """
    Generates a unique filename with a counter to prevent overwrites.
    Example: 'documento_firmado.pdf' -> 'documento_firmado_01.pdf'
    """
    counter = 1
    new_filename = f"{filename_without_ext}_firmado{extension}"
    while os.path.exists(os.path.join(download_dir, new_filename)):
        new_filename = f"{filename_without_ext}_firmado_{counter:02d}{extension}"
        counter += 1
    return new_filename

def wait_for_download_and_rename(download_dir, new_filename):
    """
    Waits for a new file to download in the directory and then renames it.
    """
    timeout = 60
    start_time = time.time()
    
    initial_files = set(os.listdir(download_dir))
    
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = list(current_files - initial_files)
        
        newly_downloaded_files = [f for f in new_files if not f.endswith('.crdownload')]
        
        if newly_downloaded_files:
            downloaded_file = os.path.join(download_dir, newly_downloaded_files[0])
            
            os.rename(downloaded_file, os.path.join(download_dir, new_filename))
            print(f"Download complete. File renamed to {new_filename}.")
            return
            
        time.sleep(0.2)
        
    raise TimeoutException("The file did not download in time.")

def firmador_automation(cuit, password, code, pin, files_to_upload, user_path):
    """
    Automates the login and signing process on the firmar.gob.ar page.
    """
    download_dir = user_path 
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options = webdriver.ChromeOptions()
    # modo fantasma
    #options.add_argument('--headless')
    #options.add_argument('--no-sandbox')
    #options.add_argument('--disable-dev-shm-usage')

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
        
        # --- STAGE 1: Login with CUIT and Password ---
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
        print("Button 'Access' from stage 1 pressed.")
        
     # Validar Stage 1
        time.sleep(3)
        error_password = browser.find_elements(By.XPATH, 
            "//div[contains(text(), 'intentos fallidos')]"
            " | //span[contains(text(), 'incorrectos')]"
        )

        print(f"DEBUG: Encontrados {len(error_password)} elementos de error")  # ← AGREGAR
        if error_password and len(error_password) > 0:
            print("DEBUG: Contraseña incorrecta detectada, lanzando excepción")  # ← AGREGAR
            raise Exception("Usuario o contraseña incorrectos. Verifique sus credenciales.")        
        
        print("Contraseña validada correctamente, continuando...")

        # --- STAGE 2: Ingresar codigo OTP ---
        WebDriverWait(browser, 20).until(
            EC.presence_of_element_located((By.ID, "inputOtp"))
        )
        print("Fields from stage 2 found.")
        
        code_input = browser.find_element(By.ID, "inputOtp")
        code_input.send_keys(code)
        
        acceder_button_stage2 = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acceder')]"))
        )
        acceder_button_stage2.click()
        print("Button 'Access' from stage 2 (OTP) pressed.")
        
        # VALIDAR STAGE 2: OTP correcto?
        time.sleep(3)
        error_otp = browser.find_elements(By.XPATH, 
            "//div[contains(text(), 'OTP ingresado no es válido')]"
            " | //div[contains(text(), 'El OTP ingresado no es válido')]"
            " | //div[contains(text(), 'intentos fallidos')]"
            " | //div[contains(text(), 'código incorrecto')]"
        )
        
        if error_otp and len(error_otp) > 0:
            raise Exception("Código OTP inválido. Verifique el código de 6 dígitos en su aplicación autenticadora.")
        
        print("OTP validado correctamente, continuando...")

        # --- STAGE 3: Loop for each file ---
        if files_to_upload:
            for i, file_path in enumerate(files_to_upload):
                
                original_filename = os.path.basename(file_path)

                # Reportar inicio del archivo
                if hasattr(firmador_automation, 'progress_callback'):
                    firmador_automation.progress_callback(i, len(files_to_upload), original_filename, 
                                                        f'Procesando {original_filename}...')
                
                print(f"\nProcessing file: {file_path}")

                try:
                    file_uploader = WebDriverWait(browser, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    
                    file_uploader.send_keys(file_path)
                    print("File attached.")

                    pin_input = WebDriverWait(browser, 15).until(
                        EC.presence_of_element_located((By.ID, "inputPin"))
                    )
                    
                    pin_input.send_keys(pin)
                    print("PIN entered.")
                    
                    firmar_button = WebDriverWait(browser, 20).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Firmar')]"))
                    )
                    firmar_button.click()
                    print("Button 'Sign' pressed.")
                    time.sleep(1)

                    descargar_button = WebDriverWait(browser, 30).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Descargar documento')]"))
                    ) 
                    
                    # New filename with potential counter
                    base_name, file_extension = os.path.splitext(original_filename)
                    new_filename = get_next_filename(download_dir, base_name, file_extension)
                    
                    print("Starting download...")
                    descargar_button.click()

                    wait_for_download_and_rename(download_dir, new_filename)
                    
                    print(f"File {original_filename} renamed to {new_filename} and saved in {download_dir}")

                    if hasattr(firmador_automation, 'progress_callback'):
                        firmador_automation.progress_callback(i + 1, len(files_to_upload), original_filename, 
                                                        f'{original_filename} completado')
                    
                    # Return to the upload screen for the next file
                    browser.back()
                    time.sleep(1)
                    WebDriverWait(browser, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                    )
                    
                except TimeoutException:
                    # Verificar si es por pérdida de conexión
                    if not check_internet_connection():
                        print(f"CONEXIÓN PERDIDA en archivo {i+1}")
                        messagebox.showerror("Conexión Perdida", 
                                        f"Se perdió la conexión en el archivo {i+1} de {len(files_to_upload)}.\n"
                                        f"Reinicie la aplicación y vuelva a cargar los PDFs.")
                        return
                    
                    print(f"Timeout error while processing {original_filename}. Continuing with the next one.")
                    continue     
                
                except Exception as e:
                    print(f"An unexpected error occurred while processing {original_filename}: {e}")
                    continue
            
            print("Process completed. Closing browser in 3 seconds...")
            time.sleep(1)
        else:
            print("No files were selected to attach. Signing process skipped.")
        
    except Exception as e:
        print(f"An unexpected general error occurred: {e}")
        raise e
        
    finally:
        if browser:
            browser.quit()

def check_internet_connection():
    """Verifica si hay conexión a internet y al sitio de firma"""
    try:
        response = requests.get("https://firmar.gob.ar", timeout=10)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):return False

if __name__ == "__main__":
    create_login_window()