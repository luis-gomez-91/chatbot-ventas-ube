import requests
from schemas.carreras import Carreras, DataCarreras
from schemas.grupos import Grupos
from config import API_URL


def fetch_carreras():
    response = requests.get(f"{API_URL}carreras")
    response.raise_for_status()
    carreras_data = response.json()
    carreras_instance = Carreras(
        status=carreras_data["status"],
        data=DataCarreras(**carreras_data["data"])
    )
    return carreras_instance


async def fetch_grupos(id_carrera: int):
    response = requests.get(f"{API_URL}grupos/{id_carrera}")
    response.raise_for_status()
    grupos_data = response.json()
    print(grupos_data)
    print("\n")
    grupos_instance = Grupos(**grupos_data)
    return grupos_instance