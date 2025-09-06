import os
import fitz   
import time 
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# --- Selección de PDF ---
pdf_path = filedialog.askopenfilename(title="Selecciona el PDF", filetypes=[("PDF files", "*.pdf")])
if not pdf_path:
    print("No se seleccionó PDF.")
    exit()

# --- Firma fija ---
signature_path = r"C:\Users\user\Downloads\sign.png"  # ruta fija a la firma
if not os.path.isfile(signature_path):
    print(f"No se encontró la firma en: {signature_path}")
    exit()

# --- Abrir PDF ---
doc = fitz.open(pdf_path)
page = doc[0]

# Mostrar imagen de la página para seleccionar posición firma
zoom = 2
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
img_path = "temp_page.png"
pix.save(img_path)

sig_width = 100
sig_height = 50
sig_width_px = sig_width * zoom
sig_height_px = sig_height * zoom

# Interfaz para seleccionar posición firma
root = tk.Tk()
root.title("Haz clic donde colocar la firma (rectángulo muestra tamaño)")

img = Image.open(img_path)
tk_img = ImageTk.PhotoImage(img)

canvas = tk.Canvas(root, width=img.width, height=img.height)
canvas.pack()
canvas.create_image(0, 0, anchor="nw", image=tk_img)

rect_id = None
click = {}

def on_click(event):
    global rect_id
    if rect_id:
        canvas.delete(rect_id)
    rect_id = canvas.create_rectangle(
        event.x, event.y,
        event.x + sig_width_px, event.y + sig_height_px,
        outline='red', width=2
    )
    click["x"] = event.x
    click["y"] = event.y

canvas.bind("<Button-1>", on_click)

def on_key(event):
    if event.keysym == 'Return' and "x" in click and "y" in click:
        root.destroy()

root.bind("<Key>", on_key)

root.mainloop()
os.remove(img_path)

if not click:
    print("No se hizo clic.")
    exit()

x_pdf = click["x"] / zoom
y_pdf = click["y"] / zoom
sig_rect = fitz.Rect(x_pdf, y_pdf, x_pdf + sig_width, y_pdf + sig_height)

# Insertar firma
page.insert_image(sig_rect, filename=signature_path)

# Guardar PDF firmado (sobrescribiendo)
doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
doc.close()

print("Firma insertada y PDF guardado.")

# --- Ahora seleccionar la imagen para añadir como página ---
image_path = filedialog.askpenfilename(title="Selecciona una imagen para añadir como página", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
if not image_path:
    print("No se seleccionó imagen adicional.")
    exit()

# Reabrir PDF para añadir página
doc = fitz.open(pdf_path)

# Convertir imagen a PDF toemporal
img = Image.open(image_path).convert("RGB")
temp_pdf_path = "temp_image.pdf"
img.save(temp_pdf_path)

# Abrir PDF temporal e insertar páginas
img_pdf = fitz.open(temp_pdf_path)
doc.insert_pdf(img_pdf)
img_pdf.close()

# Guardar PDF final
doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
doc.close()

os.remove(temp_pdf_path)

print(f"Imagen añadida como página extra y PDF guardado en:\n{pdf_path}")

#Seleccionar archivo XML
print("SCRIPT DE LLENADO DE FORMULARIO JIRA")
print("=" * 50)
print("Abriendo diálogo para seleccionar XML...")

# Crear ventana root de tkinter (oculta)
root = tk.Tk()
root.withdraw()

# Abrir diálogo de selección de archivo XML
xml_file_path = filedialog.askopenfilename(
    title="Selecciona el XML", 
    filetypes=[("XML files", "*.xml")]
)

root.destroy()

# Validar que se seleccionó un archivo
if not xml_file_path or not os.path.exists(xml_file_path):
    print("No se seleccionó archivo o no existe. Cerrando script.")
    input("Presiona Enter para salir...")
    exit()

print(f"Archivo seleccionado: {os.path.basename(xml_file_path)}")

def extract_xml_data(xml_file_path):
    """
    Extrae subtotal, total, taxes y folio fiscal de un archivo XML de factura
    """
    try:
        # Parsear el archivo XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        print(f"Root tag: {root.tag}")
        print(f"Root attributes: {root.attrib}")
        
        # Inicializar variables
        subtotal = ""
        total = ""
        taxes = ""
        folio_fiscal = ""
        
        # Método 1: Buscar directamente en el elemento root
        subtotal = root.get('SubTotal', '')
        total = root.get('Total', '')
        
        print(f"Subtotal encontrado: {subtotal}")
        print(f"Total encontrado: {total}")
        
        # Método 2: Buscar impuestos iterando por todos los elementos
        for elem in root.iter():
            # Buscar impuestos - buscar "Importe" como solicitaste
            if 'Impuesto' in elem.tag or 'Traslado' in elem.tag:
                importe = elem.get('Importe', '')
                if importe and not taxes:  # Tomar el primer Importe encontrado
                    taxes = importe
                    print(f"Importe (Taxes) encontrado: {taxes}")
        
        # También buscar en elementos con tag que contenga "Impuestos"
        for elem in root.iter():
            if 'Impuestos' in elem.tag:
                # Buscar TotalImpuestosTrasladados como alternativa
                total_impuestos = elem.get('TotalImpuestosTrasladados', '')
                if total_impuestos and not taxes:
                    taxes = total_impuestos
                    print(f"TotalImpuestosTrasladados (Taxes) encontrado: {taxes}")
        
        # Método 3: Buscar TimbreFiscalDigital
        for elem in root.iter():
            if 'TimbreFiscalDigital' in elem.tag:
                folio_fiscal = elem.get('UUID', '')
                if folio_fiscal:
                    print(f"Folio Fiscal encontrado: {folio_fiscal}")
                    break
        
        # Si no encuentra valores, mostrar todos los elementos para debug
        if not subtotal and not total:
            print("Elementos encontrados en el XML:")
            for i, elem in enumerate(root.iter()):
                if i < 10:  # Solo mostrar los primeros 10 para no saturar
                    print(f"   {elem.tag}: {elem.attrib}")
        
        return {
            'subtotal': subtotal,
            'total': total,
            'taxes': taxes,
            'folio_fiscal': folio_fiscal
        }
        
    except Exception as e:
        print(f"Error al procesar XML: {e}")
        print("Intentando método alternativo...")
        
        # Método alternativo: leer como texto y buscar patrones
        try:
            with open(xml_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            import re
            
            # Buscar patrones con regex
            subtotal_match = re.search(r'SubTotal="([^"]*)"', content)
            total_match = re.search(r'Total="([^"]*)"', content)
            taxes_match = re.search(r'Importe="([^"]*)"', content)  # Buscar Importe
            uuid_match = re.search(r'UUID="([^"]*)"', content)
            
            return {
                'subtotal': subtotal_match.group(1) if subtotal_match else '',
                'total': total_match.group(1) if total_match else '',
                'taxes': taxes_match.group(1) if taxes_match else '',
                'folio_fiscal': uuid_match.group(1) if uuid_match else ''
            }
            
        except Exception as e2:
            print(f"Error en método alternativo: {e2}")
            return None

# Extraer datos del XML
print("Procesando archivo XML...")
xml_data = extract_xml_data(xml_file_path)

if not xml_data:
    print("No se pudieron extraer los datos del XML. Cerrando script.")
    input("Presiona Enter para salir...")
    exit()

print("\nDatos extraídos del XML:")
print(f"   Subtotal: {xml_data['subtotal']}")
print(f"   Total: {xml_data['total']}")
print(f"   Taxes: {xml_data['taxes']}")
print(f"   Folio Fiscal: {xml_data['folio_fiscal']}")

driver = webdriver.Chrome()
driver.get("**URL FORM**")

# Llenar campo por ID
time.sleep(3)  # Espera a que cargue la página

driver.find_element(By.ID, "email-field").send_keys("user@gmmm.com")
driver.find_element(By.ID, "customfield_10310-field").send_keys("GT550-FR",Keys.ENTER)
driver.find_element(By.ID, "customfield_10319-field").send_keys("UU",Keys.ENTER)      #
driver.find_element(By.ID, "customfield_10430-field").send_keys("0",Keys.ENTER)       #

driver.find_element(By.ID, "summary-field").send_keys("viaticos user")
driver.find_element(By.ID, "ak-editor-textarea").send_keys("5434") 
driver.find_element(By.ID, "customfield_10309-field").send_keys("UADD.VIATICOS") 

driver.find_element(By.ID, "customfield_10402-field").send_keys({xml_data['folio_fiscal']},Keys.ENTER)
driver.find_element(By.ID, "customfield_10401-field").send_keys({xml_data['subtotal'],Keys.ENTER})   #

driver.find_element(By.ID, "customfield_10399-field").send_keys({xml_data['taxes']})           #
driver.find_element(By.ID, "customfield_10400-field").send_keys({xml_data['total']})           #

driver.find_element(By.ID, "customfield_10317-field").send_keys("MXN",Keys.ENTER)
#driver.find_element(By.ID, "customfield_10404-field").send_keys(" ")

time.sleep(100000) 
# Mantener navegador abierto
input("Presiona Enter para cerrar...")
