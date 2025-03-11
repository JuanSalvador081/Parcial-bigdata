import requests
import boto3
import datetime
import time

# Configuración
S3_BUCKET = "landing-casas-juan-salvador2"  # Asegúrate de que este sea el bucket correcto
BASE_URL = "https://casas.mitula.com.co/find"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

# Parámetros fijos de búsqueda para la venta de apartaestudios en Bogotá
PARAMS = {
    "operationType": "sell",
    "propertyType": "mitula_studio_apartment",
    "geoId": "mitula-CO-poblacion-0000014156",
    "text": "Bogotá, (Cundinamarca)"
}

s3 = boto3.client("s3")

def scrape_and_upload(event, context):
    print("🚀 Lambda Function Iniciada")
    
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    combined_html = ""  # Variable para acumular el contenido de las 10 páginas

    for page in range(1, 11):
        PARAMS["page"] = page  # Actualiza el número de página
        print(f"🔎 Intentando descargar página {page}")

        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=PARAMS)
            print(f"🌍 Código HTTP: {response.status_code}")

            if response.status_code == 200:
                # Se agrega un separador para identificar el contenido de cada página
                combined_html += f"\n<!-- Página {page} -->\n" + response.text
                print(f"✅ Página {page} procesada correctamente")
            else:
                print(f"⚠️ Error descargando página {page} - Código {response.status_code}")
                print("📜 Respuesta del servidor:", response.text[:500])  # Muestra los primeros 500 caracteres

        except requests.exceptions.RequestException as e:
            print(f"❌ Excepción al hacer la solicitud: {str(e)}")
        except Exception as e:
            print(f"🚨 Error inesperado: {str(e)}")

        time.sleep(2)  # Pausa para evitar bloqueos por muchas solicitudes consecutivas

    # Nombre del archivo unificado: yyyy-mm-dd.html
    file_name = f"{today}.html"
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=file_name, Body=combined_html)
        print(f"✅ Archivo combinado guardado en S3: {file_name}")
    except Exception as e:
        print(f"❌ Error subiendo el archivo combinado a S3: {str(e)}")

    print("✅ Scraping finalizado")
    return {"message": "Scraping completado"}
