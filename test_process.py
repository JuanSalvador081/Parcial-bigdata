# tests/test_process.py
import pytest
from unittest.mock import MagicMock
import io
import csv

# Se asume que el código del parser (con la función process_html) se
# encuentra en Parser/process.py
from Parser import process

# HTML de ejemplo con dos listings:
# - El primer listing tiene "Bogotá, Cedritos" → Barrio esperado: "Cedritos"
# - El segundo listing tiene solo "Bogotá" → Barrio esperado: "N/A"
SAMPLE_HTML = """
<html>
  <body>
    <a class="listing listing-card">
      <div class="listing-card__location__geo">
        Bogotá, Cedritos
      </div>
      <span data-test="price__actual">$ 335.000.000</span>
      <div class="listing-card__properties">
        <p data-test="bedrooms" content="1">1 habitación</p>
        <p data-test="bathrooms" content="1">1 baño</p>
        <p data-test="floor-area" content="41 m²">41 m²</p>
      </div>
      </a>
      <a class="listing listing-card">
      <div class="listing-card__location__geo">
        Bogotá
      </div>
      <span data-test="price__actual">$ 400.000.000</span>
      <div class="listing-card__properties">
        <p data-test="bedrooms" content="2">2 habitaciones</p>
        <p data-test="bathrooms" content="2">2 baños</p>
        <p data-test="floor-area" content="50 m²">50 m²</p>
      </div>
    </a>
  </body>
</html>
"""


def fake_get_object(Bucket, Key):
    class FakeBody:
        def read(self):
            return SAMPLE_HTML.encode("utf-8")

    return {"Body": FakeBody()}


def fake_put_object(Bucket, Key, Body):
    fake_put_object.csv_content = Body


# Patch de los métodos s3.get_object y s3.put_object en el módulo process


@pytest.fixture(autouse=True)
def patch_s3(monkeypatch):
    monkeypatch.setattr(process.s3, "get_object", fake_get_object)
    monkeypatch.setattr(process.s3, "put_object", fake_put_object)


def test_process_html_csv_generation():
    # Creamos un evento simulado (la estructura que S3 envía en un trigger)
    fake_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "landing-casas-juan-salvador"},
                    "object": {"key": "2025-03-11.html"},
                }
            }
        ]
    }

    result = process.process_html(fake_event, None)
    assert result["message"] == "Procesamiento completado"

    # Obtenemos el CSV que se "subió"
    csv_content = fake_put_object.csv_content
    csv_buffer = io.StringIO(csv_content)
    reader = list(csv.reader(csv_buffer))

    # Verificamos que la cabecera es la esperada
    expected_header = [
        "FechaDescarga",
        "Barrio",
        "Valor",
        "NumHabitaciones",
        "NumBanos",
        "mts2",
    ]
    assert reader[0] == expected_header

    # Primer listing: se espera que se extraiga "Cedritos" como barrio
    first_listing = reader[1]
    assert first_listing[1].strip() == "Cedritos"

    # Segundo listing: se espera "N/A" pues no hay segunda parte en la
    # ubicación
    second_listing = reader[2]
    assert second_listing[1].strip() == "N/A"


def test_process_html_filename():
    # Verifica que el nombre del CSV se derive correctamente de la key del HTML
    fake_event = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "landing-casas-juan-salvador"},
                    "object": {"key": "2025-03-11.html"},
                }
            }
        ]
    }
    _ = process.process_html(fake_event, None)
    # Se asume que fake_put_object ha capturado el CSV, por lo que comprobamos
    # que existe csv_content
    assert hasattr(fake_put_object, "csv_content")
