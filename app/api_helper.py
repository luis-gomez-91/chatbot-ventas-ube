import requests
from schemas.carreras import Carreras, DataCarreras
from schemas.grupos import Grupos
from schemas.malla import Malla
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
    data = response.json()
    grupos_instance = Grupos(**data)
    return grupos_instance

async def fetch_malla(id_carrera: int):
    response = requests.get(f"{API_URL}malla/{id_carrera}")
    response.raise_for_status()
    data = response.json()
    # print(data)
    malla_instance = Malla(**data)
    return malla_instance