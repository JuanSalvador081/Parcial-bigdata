import boto3
import csv
import datetime
from bs4 import BeautifulSoup
import io

# Buckets
S3_BUCKET_INPUT = "landing-casas-juan-salvador"
S3_BUCKET_OUTPUT = "zappa-vws52tb6p"

s3 = boto3.client("s3")


def process_html(event, context):
    print("🚀 Lambda de Procesamiento Iniciada")

    # Extraer información del evento S3
    record = event["Records"][0]
    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]
    print(f"Procesando archivo: {key} del bucket: {bucket}")

    # Descargar el archivo HTML
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        html_content = response["Body"].read().decode("utf-8")
    except Exception as e:
        print(f"❌ Error al descargar el archivo: {str(e)}")
        return {"message": "Error en la descarga"}

    # Parsear el HTML con BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Seleccionar cada "casa" mediante el selector de ambas clases
    listings = soup.select("a.listing.listing-card")
    data = []
    fecha_descarga = key.replace(".html", "")

    for listing in listings:
        # Extraer la ubicación y separar ciudad y barrio
        location_elem = listing.find("div", class_="listing-card__location__geo")
        if location_elem:
            location_text = location_elem.get_text(
                strip=True
            )  # Ejemplo: "Bogotá, Cedritos"
            parts = [part.strip() for part in location_text.split(",")]
            # Impresión de diagnóstico para verificar el split de la ubicación
            print("DEBUG: Ubicación extraída:", location_text, "-> Partes:", parts)
            barrio = parts[1] if len(parts) > 1 else "N/A"
        else:
            barrio = "N/A"

        # Extraer valor
        price_elem = listing.find("span", {"data-test": "price__actual"})
        valor = price_elem.get_text(strip=True) if price_elem else "N/A"

        # Extraer número de habitaciones
        bedrooms_elem = listing.find("p", {"data-test": "bedrooms"})
        num_habitaciones = (
            bedrooms_elem["content"]
            if bedrooms_elem and "content" in bedrooms_elem.attrs
            else "N/A"
        )

        # Extraer número de baños
        bathrooms_elem = listing.find("p", {"data-test": "bathrooms"})
        num_banos = (
            bathrooms_elem["content"]
            if bathrooms_elem and "content" in bathrooms_elem.attrs
            else "N/A"
        )

        # Extraer metros cuadrados
        floor_area_elem = listing.find("p", {"data-test": "floor-area"})
        mts2 = (
            floor_area_elem["content"]
            if floor_area_elem and "content" in floor_area_elem.attrs
            else "N/A"
        )

        data.append([fecha_descarga, barrio, valor, num_habitaciones, num_banos, mts2])

    # Generar CSV en memoria
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(
        ["FechaDescarga", "Barrio", "Valor", "NumHabitaciones", "NumBanos", "mts2"]
    )
    writer.writerows(data)

    # Guardar CSV en el bucket de salida
    csv_key = key.replace(".html", ".csv")
    try:
        s3.put_object(Bucket=S3_BUCKET_OUTPUT, Key=csv_key, Body=csv_buffer.getvalue())
        print(f"✅ CSV guardado en S3: {csv_key}")
    except Exception as e:
        print(f"❌ Error al subir el CSV: {str(e)}")

    return {"message": "Procesamiento completado"}
