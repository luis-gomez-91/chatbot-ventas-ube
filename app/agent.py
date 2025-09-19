import argo
from argo import Message
from argo.skills import chat
from config import TOKEN
import streamlit as st
from api_helper import fetch_carreras, fetch_grupos, fetch_malla
from utils import get_id_by_name, formatear_texto_carreras

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
        
        SIEMPRE mantente dentro de tu rol y contexto. Si el usuario te pregunta algo fuera de lo relacionado a las carreras
        de la UBE, responde educadamente que tu única función es proveer información sobre la oferta académica de la UBE.
    """

    carreras_instance = fetch_carreras()
    agent.carreras = carreras_instance

    @agent.tool
    async def list_carreras():
        carreras = agent.carreras.data
        if not carreras:
            return "No conozco esa carrera"

        grado = formatear_texto_carreras(carreras.grado, "grado")
        postgrado = formatear_texto_carreras(carreras.postgrado, "postgrado")
        response = f"{grado}\n{postgrado}\nLos IDS usalos para apuntar a otro endpont de ser necesario, no los muestres en la conversacion con el usuario."
        # print(response)
        return response


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
    async def skill_listar_grupos(ctx: argo.Context):
        """
        Esta skill se activa cuando el usuario pregunta por los grupos o cupos disponibles de una carrera específica.
        El agente debe identificar el nombre de la carrera en el mensaje del usuario
        y pasarlo directamente al argumento 'nombre_carrera'.

        Ejemplo de uso:
        - Mensaje del usuario: "¿Qué grupos hay para la carrera de Fisioterapia?"
        - Acción esperada del agente: Invocar skill_listar_grupos con nombre_carrera='Fisioterapia'.
        """

        ultimo_mensaje = ctx.messages[-1] 
        print(f"El usuario dijo: {ultimo_mensaje.content}")

        id_carrera = get_id_by_name(agent.carreras.data, ultimo_mensaje.content)
        print(f"ID RETORNA: {id_carrera}")

        if id_carrera == 0:
            await ctx.reply(f"Lo siento, no encontré la carrera. ¿Podrías verificar si está bien escrita?")
            return

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


    @agent.skill
    async def skill_listar_malla(ctx: argo.Context, nombre_carrera: str = None):
        """
        Esta skill se activa cuando el usuario pregunta por la malla curricular de una carrera.
        El agente debe identificar el nombre de la carrera en el mensaje del usuario
        y pasarlo al argumento 'nombre_carrera'.

        Ejemplo de uso:
        - Mensaje del usuario: "¿Cuál es la malla de la carrera de Derecho?"
        - Acción esperada del agente: Invocar skill_listar_malla con nombre_carrera='Derecho'.
        """

        ultimo_mensaje = ctx.messages[-1] 
        id_carrera = get_id_by_name(agent.carreras.data, ultimo_mensaje.content)

        if not id_carrera:
            await ctx.reply(f"Lo siento, no encontré esa carrera en nuestra base de datos. ¿Podrías verificar si está bien escrita o puedo listarte todas las carreras disponibles?")
            return

        malla_instance = await fetch_malla(id_carrera)
        malla = malla_instance.data

        if not malla:
            return "No hay malla disponible para esta carrera."

        result = f"La Malla curricular de la carrera es la siguiente:\n"
        
        for nivel in malla:
            result += f"\n### Período: {nivel.nivel_malla}"
            result += f"\nLas asignaturas de este período son:"

            for asig in nivel.asignaturas:
                result += f"\n- Asignatura: {asig.asignatura}"
                result += f"\n  - Horas: {asig.horas}"
                if asig.creditos is not None:
                    result += f"\n  - Créditos: {asig.creditos}"
        result += "\n"
            
        ctx.add(Message.system(result))
        await ctx.reply()


    return agent
