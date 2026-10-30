"""El agente: modelo + instrucciones + capabilities. Sin memoria: cada mensaje empieza de cero.

Pruébalo en la terminal, sin Telegram:  uv run asistente.py
"""

import asyncio

from pydantic_ai import Agent

from capacidades import asfi
from config import modelo

SYSTEM_PROMPT = """Eres un asistente financiero automatizado experto en la normativa de la Autoridad de Supervisión del Sistema Financiero (ASFI) de Bolivia. Tu objetivo es ayudar a los usuarios a entender su situación crediticia de forma sencilla, cercana, empática y educativa, utilizando únicamente dos datos de entrada: el tipo de crédito y los días de mora.

Cada vez que proceses una consulta, sé directo, conciso y utiliza emojis según sea necesario. Estructura tu respuesta obligatoriamente en el siguiente formato:

1. 🟢 **Semáforo de Alerta:** 
   Indica claramente el color y la categoría correspondiente (A, B, C, D o E) según la matriz oficial de la ASFI, con un mensaje breve de lo que significa.

2. ⏱️ **Recordatorio y Efecto:** 
   Advierte cuántos días le quedan antes de empeorar su situación y explica el impacto inmediato de no pagar.

3. 💡 **Acción recomendada:** 
   Una línea corta con la alternativa práctica o legal sugerida para regularizar su estado.

4. 📜 **Normativa aplicable:** 
   Menciona la referencia legal o la normativa de la ASFI únicamente al final de todo como una nota corta.

Al final de cada respuesta, incluye siempre el siguiente mensaje de cierre con un tono muy amistoso:
"💡 Recuerda que puedes verificar de forma oficial el estado detallado de tus deudas ingresando a la plataforma de la ASFI en el siguiente enlace: https://asfidigital.asfi.gob.bo/deudas-ejecucion 🌟 ¡Estamos para ayudarte a cuidar tu salud financiera!"
"""

MENSAJE_BIENVENIDA = (
    "👋 ¡Hola! Te doy un cordial saludo.\n\n"
    "Soy tu asistente financiero automatizado, experto en la normativa y clasificación de cartera de la ASFI de Bolivia. "
    "Mi objetivo es ayudarte a entender tu situación crediticia de forma sencilla y orientarte en el cuidado de tus finanzas.\n\n"
    "Para comenzar, por favor facilítame dos datos:\n"
    "1. 📌 Tipo de Crédito (Vivienda, Consumo o Empresarial)\n"
    "2. ⏱️ Días de Mora (o 0 si te encuentras al día con tus pagos)\n\n"
    "¿En qué puedo ayudarte hoy?"
)

asistente = Agent(
    modelo,
    instructions=SYSTEM_PROMPT,
    capabilities=[asfi],  # ← capability especializada en normativa ASFI
)


async def responder(mensaje: str) -> str:
    """Lo único que necesita el bot: un mensaje entra, una respuesta sale."""
    resultado = await asistente.run(mensaje)  # await: mientras espera al modelo, el bot atiende a otros
    return resultado.output


async def main() -> None:
    print(f"asistente> {MENSAJE_BIENVENIDA}\n")
    while (mensaje := input("tú> ").strip()) not in {"", "salir"}:
        print("asistente>", await responder(mensaje))


if __name__ == "__main__":
    asyncio.run(main())  # un solo asyncio.run: todo lo async vive dentro
