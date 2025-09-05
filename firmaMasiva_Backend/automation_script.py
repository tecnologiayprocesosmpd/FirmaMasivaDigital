import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import shutil # Importa shutil para eliminar el directorio temporal

def wait_for_download_and_rename(download_dir, new_filename):
    """
    Espera a que un nuevo archivo se descargue y lo renombra.
    """
    timeout = 60
    start_time = time.time()
    
    initial_files = set(os.listdir(download_dir))
    
    while time.time() - start_time < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = list(current_files - initial_files)
        
        newly_downloaded_files = [f for f in new_files if not f.endswith(('.crdownload', '.tmp'))]
        
        if newly_downloaded_files:
            downloaded_file = os.path.join(download_dir, newly_downloaded_files[0])
            os.rename(downloaded_file, os.path.join(download_dir, new_filename))
            print(f"Descarga completa. Archivo renombrado a {new_filename}.")
            return
            
        time.sleep(0.5)
        
    raise TimeoutException("El archivo no se descargó a tiempo.")

def firmador_automation(cuit, password, otp_code, pin, files_to_upload):
    """
    Automatiza el proceso de login y firma en la página firmar.gob.ar.
    """
    download_dir = 'C:\\firmado'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    options = webdriver.ChromeOptions()
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
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "inputCUIL")))
        cuit_input = browser.find_element(By.ID, "inputCUIL")
        cuit_input.send_keys(cuit)
        
        password_input = browser.find_element(By.ID, "inputPass")
        password_input.send_keys(password)
        
        acceder_button_stage1 = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acceder')]")))
        acceder_button_stage1.click()
        print("Botón 'Acceder' de la etapa 1 presionado.")
        
        # --- ETAPA 2: Ingresar Código OTP ---
        WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.ID, "inputOtp")))
        print("Campos de la etapa 2 encontrados.")
        
        otp_input = browser.find_element(By.ID, "inputOtp")
        otp_input.send_keys(otp_code)
        
        acceder_button_stage2 = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Acceder')]")))
        acceder_button_stage2.click()
        print("Botón 'Acceder' de la etapa 2 presionado. Login completado.")
        
        # --- ETAPA 3: Bucle para cada archivo ---
        if files_to_upload:
            for i, file_path in enumerate(files_to_upload):
                print(f"\nProcesando archivo: {file_path}")
                
                file_uploader = WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
                file_uploader.send_keys(file_path)
                print("Archivo adjuntado.")

                pin_input = WebDriverWait(browser, 15).until(EC.presence_of_element_located((By.ID, "inputPin")))
                pin_input.send_keys(pin)
                print("PIN ingresado.")
                
                firmar_button = WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Firmar')]")))
                firmar_button.click()
                print("Botón 'Firmar' presionado.")
                time.sleep(2)
                
                descargar_button = WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Descargar documento')]"))) 
                
                original_filename = os.path.basename(file_path)
                base_name, file_extension = os.path.splitext(original_filename)
                new_filename = f"{base_name}_firmado{file_extension}"
                
                print("Iniciando la descarga...")
                descargar_button.click()

                wait_for_download_and_rename(download_dir, new_filename)
                
                print(f"Archivo {original_filename} renombrado a {new_filename} y guardado en {download_dir}")
                
                browser.back()
                time.sleep(2)
                WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        else:
            print("No se seleccionaron archivos para adjuntar. Proceso de firma omitido.")
        
    except TimeoutException:
        print("Error: No se encontraron los elementos de la página a tiempo.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if browser:
            browser.quit()
        
if __name__ == "__main__":
    # Esta sección es solo para pruebas locales del script de automatización
    # Cuando lo uses con Flask, este código no se ejecutará
    print("Este script está diseñado para ser importado y ejecutado por un servidor Flask.")
    print("Para probarlo, llama a 'firmador_automation' con los parámetros correctos.")