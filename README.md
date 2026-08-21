# WorkInt - Prueba de Concepto (PoC)

## Descripción
En esta prueba de concepto, se realiza una demostración del flujo del sistema. Un agente de inteligencia artificial recibe como entrada un prompt predeterminado, donde un desarrollador pide ayuda para poner su aspiración salarial en su perfil.
En la etapa de proceso, un grafo de estados creado con LangGraph recibe y mantiene el contexto que se comparte entre agentes.
En la salida, el agente aconseja al usuario para escoger un rango salarial adecuado.

El fin de esta prueba de concepto es estabilizar un ambiente de desarrollo y familiarizar al equipo con las tecnologías más fundamentales de nuestro proyecto. Principalmente LangGraph, LangChain y el uso de LLMs.


## Dependencias
El proyecto requiere Python 3.10 o superior y las siguientes librerias:
- langgraph
- langchain-groq
- python-dotenv

## Uso

1. Crear y activar el entorno virtual:
   En Windows:
   python -m venv venv
   .\venv\Scripts\activate
   
   En Linux o macOS:
   python -m venv venv
   source venv/bin/activate

2. Instalar dependencias:
   pip install langgraph langchain-groq python-dotenv

3. Configurar variables de entorno:
   Cree un archivo .env en la raiz del proyecto (al mismo nivel que main.py) con su credencial de la API:
   GROQ_API_KEY="insertar_api_key"

4. Ejecutar la prueba:
   python main.py