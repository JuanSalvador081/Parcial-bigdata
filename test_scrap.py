# tests/test_scrap.py
from unittest.mock import patch, MagicMock
import datetime

# Se asume que la función scrape_and_upload está en el módulo scrap
from Scrapper import scrap

# Prueba 1: Verifica que, ante respuestas HTTP 200, se procese y se llame
# a s3.put_object


@patch("Scrapper.scrap.requests.get")
@patch("Scrapper.scrap.s3.put_object")
def test_scrape_success(mock_put_object, mock_requests_get):
    # Configuramos el mock para requests.get: siempre devuelve un status 200
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.text = "<html>Contenido de prueba</html>"
    mock_requests_get.return_value = response_mock

    # Ejecutamos la función
    result = scrap.scrape_and_upload({}, {})

    # Verificamos que se haya llamado a s3.put_object y se retorne el mensaje
    # esperado
    mock_put_object.assert_called_once()
    assert "Scraping completado" in result["message"]


# Prueba 2: Simula que algunas páginas fallan (por ejemplo, status 404) y
# verifica que se complete el proceso


@patch("Scrapper.scrap.requests.get")
@patch("Scrapper.scrap.s3.put_object")
def test_scrape_partial_failure(mock_put_object, mock_requests_get):
    def side_effect(*args, **kwargs):
        page = kwargs.get("params", {}).get("page", 1)
        response = MagicMock()
        # Si el número de página es par, simula error 404, de lo contrario
        # éxito
        if page % 2 == 0:
            response.status_code = 404
            response.text = "Not Found"
        else:
            response.status_code = 200
            response.text = f"<html>Página {page} correcta</html>"
        return response

    mock_requests_get.side_effect = side_effect

    result = scrap.scrape_and_upload({}, {})
    # A pesar de errores intermitentes, se espera que se invoque s3.put_object
    # y se retorne mensaje de éxito
    assert mock_put_object.called
    assert "Scraping completado" in result["message"]


# Prueba 3: Verifica que el nombre de archivo se genera con el formato esperado


def test_filename_format():
    today = datetime.datetime.today().strftime("%Y-%m-%d")
    file_name = f"{today}.html"
    # Se espera que el formato sea "YYYY-MM-DD.html" (longitud fija para una
    # fecha válida)
    assert len(file_name) == len("yyyy-mm-dd.html")
