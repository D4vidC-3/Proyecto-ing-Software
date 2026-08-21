import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

# Cargar las variables de entorno (API key)
load_dotenv()

# Definir la estructura del Estado
# Esto define que datos viajan por el grafo.
class AgentState(TypedDict):
    input_text: str
    ai_response: str

# Inicialización modelo de IA
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# Crear el Nodo (La función que hará el trabajo)
def profile_agent_node(state: AgentState):
    print("--- El Agente de Perfil está procesando ---")
    user_input = state["input_text"]
    
    # Llamamos a la IA pasándole el texto del usuario
    response = llm.invoke(f"Eres un asistente de empleo. Responde brevemente a esto: {user_input}")
    
    # Actualizamos el estado con la respuesta
    return {"ai_response": response.content}

# Construir el Grafo (El flujo de ejecución)
workflow = StateGraph(AgentState)

# Añadir el nodo al grafo
workflow.add_node("profile_agent", profile_agent_node)

# Definir el camino: START -> profile_agent -> END
workflow.add_edge(START, "profile_agent")
workflow.add_edge("profile_agent", END)

# Compilar el grafo en una aplicación ejecutable
app = workflow.compile()

# Ejecutar la Prueba de Concepto (Entrada, Proceso, Salida)
if __name__ == "__main__":
    print("Iniciando Prueba de Concepto...\n")
    
    # ENTRADA
    initial_state = {"input_text": "Hola, soy desarrollador pero no sé cómo poner mi aspiración salarial en mi perfil."}
    
    # PROCESO
    result = app.invoke(initial_state)
    
    # SALIDA
    print("\nRespuesta del Sistema:")
    print(result["ai_response"])