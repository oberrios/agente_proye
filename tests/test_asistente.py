"""Pruebas sin modelo real ni internet: uv run pytest

Un modelo falso (FunctionModel) pide la tool que queremos, y comprobamos lo que hace el código.
"""

import os
from types import SimpleNamespace

os.environ.setdefault("GEMINI_API_KEY_LOCAL", "clave-de-prueba")  # para importar sin .env (no se llama a Gemini)

import pytest  # noqa: E402
from pydantic_ai import ModelResponse, TextPart, ToolCallPart, ToolReturnPart  # noqa: E402
from pydantic_ai.models.function import FunctionModel  # noqa: E402

import asistente  # noqa: E402
import bot  # noqa: E402
import capacidades  # noqa: E402
from config import settings  # noqa: E402


def pide(tool: str, args: dict) -> FunctionModel:
    """Un modelo falso: la 1.ª vez pide la tool; cuando recibe su resultado, responde texto."""

    def responder(mensajes, info):
        ultimo = mensajes[-1].parts[-1]
        if isinstance(ultimo, ToolReturnPart):
            return ModelResponse(parts=[TextPart(f"Resultado: {ultimo.content}")])
        return ModelResponse(parts=[ToolCallPart(tool, args)])

    return FunctionModel(responder)


def test_evaluar_mora_asfi_semaforos():
    # Consumo: <= 5 días es Verde
    verde = capacidades.evaluar_mora_asfi("consumo", 3)
    assert verde["semaforo"] == "Verde"
    assert "Categoría A" in verde["categoria_asfi"]

    # Consumo: 15 días es Amarillo (Categoría B)
    amarillo = capacidades.evaluar_mora_asfi("consumo", 15)
    assert amarillo["semaforo"] == "Amarillo"
    assert "Categoría B" in amarillo["categoria_asfi"]

    # Vivienda: 100 días es Rojo (Categoría C)
    rojo = capacidades.evaluar_mora_asfi("vivienda", 100)
    assert rojo["semaforo"] == "Rojo"
    assert "Categoría C" in rojo["categoria_asfi"]

    # Empresarial: 20 días es Verde (Categoría A)
    emp = capacidades.evaluar_mora_asfi("empresarial", 20)
    assert emp["semaforo"] == "Verde"
    assert "Categoría A" in emp["categoria_asfi"]


def test_evaluar_mora_asfi_dias_negativos():
    error = capacidades.evaluar_mora_asfi("empresarial", -5)
    assert "error" in error


def test_consultar_derechos_prestatario_asfi():
    cobranza = capacidades.consultar_derechos_prestatario_asfi("cobranza")
    assert "ASFI" in cobranza["derechos"]
    assert "Punto de Reclamo" in cobranza["accion"]

    reprog = capacidades.consultar_derechos_prestatario_asfi("reprogramacion")
    assert "reprogramación" in reprog["derechos"]


async def test_asistente_evaluar_mora_con_modelo_falso():
    with asistente.asistente.override(model=pide("evaluar_mora_asfi", {
        "tipo_credito": "consumo", "dias_mora": 10,
    })):
        respuesta = await asistente.responder("Tengo un crédito de consumo con 10 días de mora.")
    assert "Resultado:" in respuesta


async def test_bot_inicio_envia_mensaje_bienvenida(monkeypatch):
    monkeypatch.setattr(settings, "telegram_permitidos", "123")
    respuestas = []

    async def reply_text(texto):
        respuestas.append(texto)

    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=123), message=SimpleNamespace(reply_text=reply_text)
    )
    await bot.inicio(update, None)
    assert len(respuestas) == 1
    assert "ASFI" in respuestas[0]
    assert "Tipo de Crédito" in respuestas[0]
    assert "Días de Mora" in respuestas[0]


async def test_chat_ajeno_se_rechaza_sin_llamar_al_modelo(monkeypatch):
    monkeypatch.setattr(settings, "telegram_permitidos", "123")
    respuestas = []

    async def reply_text(texto):
        respuestas.append(texto)

    def modelo_prohibido(mensajes, info):
        raise AssertionError("no debía llamarse al modelo")

    update = SimpleNamespace(
        effective_chat=SimpleNamespace(id=999), message=SimpleNamespace(text="hola", reply_text=reply_text)
    )
    with asistente.asistente.override(model=FunctionModel(modelo_prohibido)):
        await bot.mensaje(update, None)
    assert "No autorizado" in respuestas[0] and "999" in respuestas[0]


def test_permitidos(monkeypatch):
    monkeypatch.setattr(settings, "telegram_permitidos", " 123, 456 ,")
    assert settings.permitidos == {"123", "456"}
    monkeypatch.setattr(settings, "telegram_permitidos", "")
    assert settings.permitidos == set()  # vacío = nadie
