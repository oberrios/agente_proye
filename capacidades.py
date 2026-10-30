"""Capability especializada en la normativa de la ASFI (Bolivia).

Utiliza esquemas de Pydantic para validar los datos de entrada (tipo_credito y dias_mora)
y estructurar el cálculo de la categoría de riesgo y semáforo de alerta de la ASFI.
"""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai.capabilities import Capability

TipoCredito = Literal["vivienda", "consumo", "empresarial"]


class EntradaEvaluacionMora(BaseModel):
    """Esquema Pydantic para validar los datos de entrada de la consulta crediticia."""

    tipo_credito: TipoCredito = Field(
        description="Tipo de crédito: 'vivienda', 'consumo' o 'empresarial'"
    )
    dias_mora: int = Field(
        ge=0,
        description="Días de retraso acumulados en el pago de la cuota (debe ser mayor o igual a 0)"
    )


class ResultadoEvaluacionASFI(BaseModel):
    """Esquema Pydantic de salida con la evaluación de riesgo crediticio según la ASFI."""

    tipo_credito: str
    dias_mora: int
    semaforo: Literal["Verde", "Amarillo", "Rojo"]
    categoria_asfi: str
    recordatorio_dia_limite: str
    guia_accion_inmediata: str
    alternativas_solucion: str
    impacto_cic: str
    fuente: str


asfi = Capability(
    id="normativa_asfi",
    description="Evaluación crediticia y cálculo de semáforo de mora según normativa ASFI de Bolivia",
    instructions=(
        "Usa evaluar_mora_asfi cuando el usuario consulte por su mora o situación crediticia. "
        "Solicita amablemente el Tipo de Crédito ('vivienda', 'consumo' o 'empresarial') y los Días de Mora "
        "si el usuario no los proporcionó. Basa tu respuesta en los 4 pasos estructurados: "
        "1. Semáforo de Alerta, 2. Recordatorio del Día Límite, 3. Guía de Acción Inmediata, "
        "y 4. Alternativas de Solución Automatizadas, citando la fuente oficial de ASFI."
    ),
)


@asfi.tool_plain
def evaluar_mora_asfi(tipo_credito: TipoCredito, dias_mora: int) -> dict:
    """Evalúa la situación crediticia bajo normativa de la ASFI validando con Pydantic.

    Args:
        tipo_credito: Tipo de crédito ('vivienda', 'consumo' o 'empresarial')
        dias_mora: Días de retraso acumulados en el pago de la cuota (0 si está al día)
    """
    try:
        entrada = EntradaEvaluacionMora(tipo_credito=tipo_credito, dias_mora=dias_mora)
    except Exception as error:
        return {"error": f"Validación de datos fallida: {error}"}

    credito = entrada.tipo_credito
    mora = entrada.dias_mora

    # Umbrales oficiales ASFI (RNSF Libro 3, Título II, Calificación de Cartera de Créditos)
    if credito == "consumo":
        if mora <= 5:
            semaforo = "Verde"
            categoria = "Categoría A (Normal / Vigente)"
            limite = f"Tienes {6 - mora} días de margen antes de entrar a Categoría B (día 6 de mora)."
            accion = "Paga tu cuota habitual antes de la fecha límite para mantener tu score crediticio perfecto."
            soluciones = "Pago automático mensual o transferencia QR desde tu banca móvil."
            impacto = "Calificación A en la Central de Información Crediticia (CIC) de la ASFI."
        elif mora <= 30:
            semaforo = "Amarillo"
            categoria = "Categoría B (Problemas Potenciales)"
            limite = f"Quedan {31 - mora} días antes de pasar a Categoría C (Deficiente) al día 31."
            accion = "Paga la cuota adeudada hoy o antes de fin de mes para evitar el reporte formal con mora en la CIC."
            soluciones = "Acuerdo de regularización inmediata con tu oficial o plan de cuotas sobre saldo devengado."
            impacto = "Anotación de alerta temprana en la CIC. Puede suspender temporalmente el uso de tarjetas de crédito."
        elif mora <= 60:
            semaforo = "Rojo"
            categoria = "Categoría C (Deficiente)"
            limite = f"Faltan {61 - mora} días para caer en Categoría D (Dudoso) al día 61."
            accion = "Comunícate urgentemente con tu entidad financiera; el crédito está en etapa prejudicial."
            soluciones = "Solicitud formal de Reprogramación de deuda acreditando reducción justificada de ingresos."
            impacto = "Reporte negativo severo en la CIC. Bloqueo para acceder a nuevos créditos en cualquier banco."
        elif mora <= 90:
            semaforo = "Rojo"
            categoria = "Categoría D (Dudoso)"
            limite = f"Faltan {91 - mora} días para pasar a Categoría E (Pérdida / Cobro Coactivo)."
            accion = "Preséntate en el departamento de cobranzas para evitar la ejecución judicial de tus garantías."
            soluciones = "Refinanciamiento integral con reestructuración de garantías personales o reales."
            impacto = "Calificación de alto riesgo crediticio con máxima exigencia de previsión bancaria."
        else:
            semaforo = "Rojo"
            categoria = "Categoría E/F (Pérdida / Ejecución Judicial o Castigo)"
            limite = "Plazo de tolerancia agotado (>90 días). Proceso judicial o prejudicial activo."
            accion = "Buscar asesoría jurídica y solicitar audiencia de conciliación ante el Punto de Reclamo ASFI."
            soluciones = "Plan extraordinario de liquidación o amortización extraordinaria para detener remates o embargos."
            impacto = "Historial crediticio gravemente dañado con impedimento legal para contratar en el sistema financiero."

    elif credito == "vivienda":
        if mora <= 30:
            semaforo = "Verde"
            categoria = "Categoría A (Normal / Vigente)"
            limite = f"Tienes {31 - mora} días de margen antes del cambio de categoría regulatoria."
            accion = "Efectuar el pago regular de la cuota mensual de vivienda."
            soluciones = "Débito automático bancario para evitar olvidos involuntarios."
            impacto = "Calificación óptima A en la CIC de ASFI."
        elif mora <= 90:
            semaforo = "Amarillo"
            categoria = "Categoría B (Problemas Potenciales)"
            limite = f"Tienes {91 - mora} días antes del día 91 para evitar entrar en Categoría C."
            accion = "Contactar a tu oficial hipotecario para regularizar las cuotas atrasadas antes del cierre contable."
            soluciones = "Solicitar periodo de gracia temporal o prórroga justificando afectación económica temporal."
            impacto = "Observación preventiva en la CIC sin inicio de cobranza judicial."
        elif mora <= 120:
            semaforo = "Rojo"
            categoria = "Categoría C (Deficiente)"
            limite = f"Faltan {121 - mora} días para entrar en Categoría D (día 121)."
            accion = "Negociar urgentemente con el banco para evitar que el inmueble entre a proceso de ejecución coactiva."
            soluciones = "Reprogramación del crédito de vivienda ampliando el plazo total hasta 25 o 30 años."
            impacto = "Reporte negativo por mora en vivienda; riesgo directo sobre la garantía hipotecaria."
        elif mora <= 180:
            semaforo = "Rojo"
            categoria = "Categoría D (Dudoso)"
            limite = f"Faltan {181 - mora} días para llegar a Categoría E (Pérdida al superar 180 días)."
            accion = "Coordinar con la gerencia de créditos la firma de una adenda contractual de salvaguarda."
            soluciones = "Dación en pago parcial o inclusión de co-deudores para viabilizar reestructuración."
            impacto = "Alerta crítica en el sistema financiero y gravamen en Derechos Reales."
        else:
            semaforo = "Rojo"
            categoria = "Categoría E/F (Pérdida / Proceso Coactivo Hipotecario)"
            limite = "Plazo superado (>180 días). El inmueble está sujeto a remate judicial."
            accion = "Acudir a la Defensoría del Consumidor Financiero de la ASFI para solicitar mediación."
            soluciones = "Cancelación total negociada con condonación de intereses penales o rescate de la vivienda."
            impacto = "Registro coactivo permanente en la CIC de ASFI."

    else:  # empresarial
        if mora <= 30:
            semaforo = "Verde"
            categoria = "Categoría A (Normal / Vigente)"
            limite = f"Cuentas con {31 - mora} días de holgura antes de entrar a Categoría B."
            accion = "Alinear el flujo de caja del negocio con las fechas de pago del banco."
            soluciones = "Pago ágil por plataforma empresarial o factoring sobre cuentas por cobrar."
            impacto = "Perfil comercial categoría A en la CIC de ASFI."
        elif mora <= 60:
            semaforo = "Amarillo"
            categoria = "Categoría B (Problemas Potenciales)"
            limite = f"Faltan {61 - mora} días para pasar a Categoría C (Deficiente al día 61)."
            accion = "Presentar estados financieros actualizados al banco para transparentar la liquidez de la empresa."
            soluciones = "Readecuación de cuotas según la estacionalidad de ventas del negocio."
            impacto = "Alerta crediticia comercial en la CIC; restricción en líneas de sobregiro."
        elif mora <= 90:
            semaforo = "Rojo"
            categoria = "Categoría C (Deficiente)"
            limite = f"Faltan {91 - mora} días para pasar a Categoría D al día 91."
            accion = "Solicitar reunión formal con la comisión de créditos del banco para exponer plan de contingencia."
            soluciones = "Reprogramación operativa con ajuste de amortizaciones a capital."
            impacto = "Calificación desfavorable que inhabilita licitaciones y garantías bancarias."
        elif mora <= 120:
            semaforo = "Rojo"
            categoria = "Categoría D (Dudoso)"
            limite = f"Faltan {121 - mora} días para Categoría E al día 121."
            accion = "Intervenir la cartera de cobranzas de la empresa para inyectar liquidez inmediata al crédito."
            soluciones = "Reestructuración integral de pasivos con acreedores bancarios."
            impacto = "Riesgo crediticio severo y congelamiento de créditos en el sistema financiero."
        else:
            semaforo = "Rojo"
            categoria = "Categoría E/F (Pérdida / Demanda Ejecutiva Mercantil)"
            limite = "Superados los 120 días de mora. Cobro judicial de pagarés y garantías prendarias/hipotecarias."
            accion = "Activar defensa legal corporativa y buscar mediación ante la Cámara de Comercio o ASFI."
            soluciones = "Plan de liquidación concertada o venta de activos no estratégicos."
            impacto = "Inhabilitación mercantil y reporte de pérdida irrevocable en la CIC."

    resultado = ResultadoEvaluacionASFI(
        tipo_credito=credito,
        dias_mora=mora,
        semaforo=semaforo,
        categoria_asfi=categoria,
        recordatorio_dia_limite=limite,
        guia_accion_inmediata=accion,
        alternativas_solucion=soluciones,
        impacto_cic=impacto,
        fuente="Normativa ASFI - Recopilación de Normas para Servicios Financieros (RNSF, Libro 3, Título II)",
    )
    return resultado.model_dump()


@asfi.tool_plain
def consultar_derechos_prestatario_asfi(tema: Literal["cobranza", "reprogramacion", "reclamos"]) -> dict:
    """Consulta los derechos del prestatario y normativas de protección al consumidor financiero de ASFI.

    Args:
        tema: Área de consulta ('cobranza' para normas de cobranza extrajudicial, 'reprogramacion' para condiciones de renegociación, 'reclamos' para procedimiento de reclamo formal)
    """
    if tema == "cobranza":
        return {
            "tema": "Cobranza Extrajudicial Justa",
            "derechos": (
                "La ASFI prohíbe terminantemente prácticas de cobranza intimidatorias, ofensivas o humillantes. "
                "Los bancos no pueden contactar a terceros que no sean garantes, ni realizar llamadas fuera del "
                "horario comercial permitido (7:00 a 20:00 de lunes a viernes y 8:00 a 13:00 los sábados)."
            ),
            "accion": "Si sufres acoso o cobro indebido, presenta un reclamo en el Punto de Reclamo del banco o ante la ASFI.",
            "fuente": "Reglamento de Protección del Consumidor Financiero - ASFI",
        }
    elif tema == "reprogramacion":
        return {
            "tema": "Reprogramación y Refinanciamiento",
            "derechos": (
                "Todo prestatario que enfrente dificultades justificadas en su capacidad de pago tiene derecho a "
                "solicitar la reprogramación de su crédito, lo cual puede incluir extensión del plazo original, "
                "reducción de cuota mensual o periodos de gracia sin que se le exijan cobros extorsivos."
            ),
            "accion": "Presenta una carta formal a tu oficial de crédito adjuntando respaldo de la disminución de ingresos.",
            "fuente": "Normas de Evaluación y Calificación de Cartera de Créditos - ASFI",
        }
    else:  # reclamos
        return {
            "tema": "Procedimiento de Reclamación Formal",
            "derechos": (
                "Primera Instancia: Todo banco cuenta con un Punto de Reclamo (PR) obligatorio con plazo de respuesta de 5 días hábiles. "
                "Segunda Instancia: Si la respuesta no es satisfactoria, puedes elevar el reclamo ante la Defensoría del Consumidor Financiero de la ASFI."
            ),
            "accion": "Solicita tu número de formulario de reclamo en el Punto de Reclamo de tu entidad bancaria.",
            "fuente": "Sistema de Atención de Reclamos - ASFI",
        }
