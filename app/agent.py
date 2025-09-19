import argo
from argo import Message
from argo.skills import chat
import requests
from config import TOKEN, API_URL
import streamlit as st
from schemas.carreras import Carreras, DataCarreras
from schemas.grupos import Grupos, GrupoData

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
        Eres un vendedor de la Universidad Bolivariana del Ecuador (UBE).
        Responde de manera cordial y precisa a preguntas sobre:
        1. Información general de las carreras.
        2. Información de la malla de una carrera específica.
        3. Información de los grupos disponibles de una carrera específica.
        Dependiendo de lo que pregunte el usuario, llama a la API correspondiente.
    """

    try:
        # res = requests.get(f"{API_URL}carreras")
        response = requests.get(f"https://sga.ube.edu.ec/api/ventas/carreras")
        response.raise_for_status()
        carreras_data = response.json()
        print(carreras_data)
        carreras_instance = Carreras(
            status=carreras_data["status"],
            data=DataCarreras(**carreras_data["data"])
        )
        agent.carreras = carreras_instance
    except requests.RequestException as e:
        return f"Error al obtener las carreras: {e}"

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
    
    @agent.tool
    async def fetch_grupos(id_carrera: int):
        # res = requests.get(f"{API_URL}grupos/")
        response = requests.get(f"https://sga.ube.edu.ec/api/ventas/grupos/{id_carrera}")
        response.raise_for_status()
        grupos_data = response.json()
        
        print(grupos_data)

        grupos_instance = Grupos(
            status=grupos_data["status"],
            data=GrupoData(**grupos_data["data"])
        )
        agent.grupos = grupos_instance

    @agent.tool
    async def listar_grupos():
        grupos = agent.grupos.data
        if not grupos:
            return "No conozco ese grupo"

        if not grupos:
            return "No hay grupos disponibles que inicien clase proximamente."

        response = f"Los grupos de la carrera {grupos[0].carrera} disponibles son:"
        response = "\n".join(
            f"- Paralelo: {grupo.nombre}, Fecha de inicio de clases aproximado: {grupo.fecha_inicio}, Sesion: {grupo.sesion}, Modalidad: {grupo.modalidad}"
            for grupo in grupos
        )
        print(response)
        return response
    
    async def list_grupos_de_carrera(id_carrera: int):
        # Primero obtenemos los grupos de la API
        response = requests.get(f"https://sga.ube.edu.ec/api/ventas/grupos/{id_carrera}")
        response.raise_for_status()
        grupos_data = response.json()
        grupos_instance = Grupos(
            status=grupos_data["status"],
            data=GrupoData(**grupos_data["data"])
        )

        grupos = grupos_instance.data.grupos  # Ajusta según tu schema
        if not grupos:
            return "No hay grupos disponibles para esta carrera."

        response_text = f"Los grupos de la carrera {grupos[0].carrera} disponibles son:\n"
        response_text += "\n".join(
            f"- Paralelo: {grupo.nombre}, Fecha de inicio: {grupo.fecha_inicio}, Sesión: {grupo.sesion}, Modalidad: {grupo.modalidad}"
            for grupo in grupos
        )
        return response_text
            
    # @agent.skill
    # async def responder_usuario(ctx: argo.Context):
    #     tool = await ctx.equip(tools=[list_carreras])
    #     result = await ctx.invoke(tool)
    #     ctx.add(Message.system(result))
    #     await ctx.reply()

    @agent.skill
    async def responder_usuario(ctx: argo.Context):
        user_input = ctx.messages[-1].content.lower() 

        if "carrera" in user_input and "grupo" not in user_input:
            tool = await ctx.equip(tools=[list_carreras])
            result = await ctx.invoke(tool)
        elif "grupo" in user_input:
            import re
            match = re.search(r"carrera (\d+)", user_input)
            if match:
                id_carrera = int(match.group(1))
                await fetch_grupos(id_carrera)
                tool = await ctx.equip(tools=[list_grupos_de_carrera])
                result = await ctx.invoke(tool, id_carrera=id_carrera)
            else:
                result = "No entendí el ID de la carrera. Por favor proporciona un número de carrera."
        else:
            result = "No entendí tu consulta. Pregunta sobre carreras o grupos."

        ctx.add(Message.system(result))
        await ctx.reply()



   

    return agent
