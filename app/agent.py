import argo
from argo import Message
from argo.skills import chat
import requests
from config import TOKEN, API_URL
import streamlit as st
from schemas.carreras import Carreras, DataCarreras, Carrera
from schemas.grupos import Grupos, GrupoData
from typing import List
from api_helper import fetch_carreras, fetch_grupos

@st.cache_resource
def initialize_agent():
    if not TOKEN:
        st.error("TOKEN environment variable not set. Please create a .env file.")
        return None

    llm = argo.LLM(
        model="google/gemini-2.5-flash",
        api_key=TOKEN,
        base_url="https://openrouter.ai/api/v1",
        verbose=True,
    )

    agent = argo.ChatAgent(
        name="Dr. Matrícula",
        description="Asistente que actúa como vendedor de carreras de la UBE.",
        llm=llm,
        skills=[chat],
    )

    agent.system_prompt = """
        Eres un vendedor de la Universidad Bolivariana del Ecuador (UBE). Responde de manera cordial y precisa a
        preguntas sobre carreras. Si te preguntan por grupos o mallas, identifica el nombre de la carrera en el mensaje
        del usuario para buscar la información.
        Ejemplo:
        Pregunta: "¿Grupos de la carrera de Derecho?". Respuesta esperada: invocar la herramienta con 'nombre_carrera'='Derecho'.
        Si no tienes la informacion necesario. indica que visiten la pagina web para mas informacion: https://sga.ube.edu.ec/
    """

    carreras_instance = fetch_carreras()
    agent.carreras = carreras_instance

    @agent.tool
    async def list_carreras():
        carreras = agent.carreras.data
        if not carreras:
            return "No conozco esa carrera"

        grado = "Las carreras de grado son: \n"
        grado += "\n".join(
            f"- ID de la carrera: {carrera.id}, Nombre de la carrera: {carrera.nombre}."
            for carrera in carreras.grado
        )

        postgrado = "Las carreras de postgrado son: "
        postgrado += "\n".join(
            f"- {carrera.nombre}."
            for carrera in carreras.postgrado
        )

        response = f"{grado}\n{postgrado}\nLos IDS usalos para apuntar a otro endpont de ser necesario, no los muestres en la conversacion con el usuario."
        # print(response)
        return response
    
    # @agent.tool
    # async def fetch_grupos(id_carrera: int):
    #     # res = requests.get(f"{API_URL}grupos/")
    #     response = requests.get(f"https://sga.ube.edu.ec/api/ventas/grupos/{id_carrera}")
    #     response.raise_for_status()
    #     grupos_data = response.json()
    #     print(grupos_data)
    #     print("\n")
    #     grupos_instance = Grupos(**grupos_data)
        # agent.grupos = grupos_instance


    @agent.tool
    async def listar_grupos(id_carrera: int):
        """
        Herramienta que lista los grupos de una carrera específica.
        Requiere el 'id_carrera' de la carrera como un número entero.
        Este ID se debe obtener primero con otra skill.
        """
        print(f"ID RECIBE LISTAR_GRUPOS: {id_carrera}")
        grupos_instance = await fetch_grupos(id_carrera)
        agent.grupos = grupos_instance
        grupos = agent.grupos.data

        if not grupos:
            return "No hay grupos disponibles que inicien clase proximamente."

        response = f"Los grupos disponibles son:"
        response = "\n".join(
            f"- Paralelo: {grupo.nombre}, Fecha de inicio de clases aproximado: {grupo.fecha_inicio}, Sesion: {grupo.sesion}, Modalidad: {grupo.modalidad}"
            for grupo in grupos
        )
        print(response)
        return response
            
    # @agent.skill
    # async def responder_usuario(ctx: argo.Context):
    #     tool = await ctx.equip(tools=[list_carreras])
    #     result = await ctx.invoke(tool)
    #     ctx.add(Message.system(result))
    #     await ctx.reply()

    @agent.skill
    async def skill_listar_carreras(ctx: argo.Context):
        """
            Esta skill es para cuando el usuario quiere una visión general de la oferta académica.
            "¿Qué carreras tienen?"
            "Quiero ver la lista de carreras."
            "Háblame de las carreras de la UBE."
            "¿Qué opciones de estudio ofrecen?"
        """
        tool = await ctx.equip(tools=[list_carreras])
        result = await ctx.invoke(tool)
        ctx.add(Message.system(result))
        await ctx.reply()


    @agent.skill
    async def skill_listar_grupos(ctx: argo.Context, nombre_carrera: str = "ELECTRICIDAD"):
        """
        Activa esta skill SOLO si el usuario pregunta por los grupos de una carrera específica.
        El agente DEBE identificar el nombre de la carrera en el mensaje del usuario (ej. 'Derecho', 'Contabilidad')
        y pasar ese valor directamente al argumento 'nombre_carrera'.
        """

        ultimo_mensaje = ctx.messages[-1] 
        print(f"El usuario dijo: {ultimo_mensaje.content}")

        if not nombre_carrera:
            print("SIN NOMBRE")
            await ctx.reply(f"Claro, ¿de qué carrera te gustaría saber los grupos? Si quieres, puedo listarte todas las carreras disponibles.")
            return

        id_carrera = find_carrera_id_by_name(nombre_carrera)
        print(f"ID RETORNA: {id_carrera}")

        if id_carrera is None:
            await ctx.reply(f"Lo siento, no encontré la carrera de '{nombre_carrera}'. ¿Podrías verificar si está bien escrita?")
            return

        print("POSI")
        # tool = await ctx.equip(tools=[listar_grupos])
        # result = await ctx.invoke(tool, id_carrera=id_carrera)

        grupos_instance = await fetch_grupos(id_carrera)
        grupos = grupos_instance.data

        if not grupos:
            return "No hay grupos disponibles que inicien clase proximamente."

        result = f"Los grupos disponibles son:"
        result = "\n".join(
            f"- Paralelo: {grupo.nombre}, Fecha de inicio de clases aproximado: {grupo.fecha_inicio}, Sesion: {grupo.sesion}, Modalidad: {grupo.modalidad}"
            for grupo in grupos
        )

        ctx.add(Message.system(result))
        await ctx.reply()

   
    def find_carrera_id_by_name(carrera_name: str):
        print("BUSCANDO ID DE CARRERA")
        carreras_grado: List[DataCarreras] = agent.carreras.data.grado
        carreras_postgrado = agent.carreras.data.postgrado

        for carrera in carreras_grado:
            print(f"GRADO: {carrera.id} - {carrera.nombre}")
            if carrera.nombre.lower() == carrera_name.lower():
                print(f"GRADO SELECT: {carrera.id} - {carrera.nombre}")
                return carrera.id
            
        for carrera in carreras_postgrado:
            print(f"POSTGRADO: {carrera.id} - {carrera.nombre}")
            if carrera.nombre.lower() == carrera_name.lower():
                print(f"POSTGRADO SELECT: {carrera.id} - {carrera.nombre}")
                return carrera.id
        return None


    return agent
