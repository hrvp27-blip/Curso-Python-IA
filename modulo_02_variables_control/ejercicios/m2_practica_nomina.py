"""Módulo 2 - Práctica 2, parte B: calculadora de nómina."""

SEGURIDAD_SOCIAL = 6.35
PAGAS = 12
PAGAS_ADMITIDAS = (12, 14)

# Escala de IRPF: (límite superior del tramo, porcentaje). El último no tiene límite.
TRAMOS_IRPF = (
    (12450, 19),
    (20200, 24),
    (35200, 30),
    (60000, 37),
    (float("inf"), 45),
)

ANCHO_ETIQUETA = 20
ANCHO_IMPORTE = 12


def calcular_irpf(bruto_anual: float) -> float:
    """Calcula la retención anual de IRPF con una escala progresiva.

    Cada tramo se aplica solo a la parte del salario que cae dentro de él.

    >>> calcular_irpf(30000)
    7165.5
    """
    retencion = 0.0
    limite_inferior = 0
    for limite_superior, porcentaje in TRAMOS_IRPF:
        if bruto_anual <= limite_inferior:
            break
        importe_gravado = min(bruto_anual, limite_superior) - limite_inferior
        retencion += importe_gravado * porcentaje / 100
        limite_inferior = limite_superior
    return round(retencion, 2)


def calcular_seguridad_social(bruto_anual: float) -> float:
    """Calcula la cotización anual del trabajador a la Seguridad Social.

    >>> calcular_seguridad_social(30000)
    1905.0
    """
    return round(bruto_anual * SEGURIDAD_SOCIAL / 100, 2)


def calcular_neto_anual(bruto_anual: float) -> float:
    """Devuelve el salario neto anual: bruto menos IRPF y Seguridad Social.

    >>> calcular_neto_anual(30000)
    20929.5
    """
    irpf = calcular_irpf(bruto_anual)
    seguridad_social = calcular_seguridad_social(bruto_anual)
    return round(bruto_anual - irpf - seguridad_social, 2)


def tipo_efectivo(bruto_anual: float) -> float:
    """Devuelve el porcentaje de IRPF sobre el bruto, con dos decimales.

    Si el bruto es cero o negativo devuelve 0.0.

    >>> tipo_efectivo(30000)
    23.89
    """
    if bruto_anual <= 0:
        return 0.0
    return round(calcular_irpf(bruto_anual) / bruto_anual * 100, 2)


def linea_nomina(etiqueta: str, importe: float) -> str:
    """Devuelve una línea del resumen con la etiqueta y el importe alineados.

    >>> linea_nomina("Bruto anual", 30000)
    'Bruto anual            30,000.00'
    """
    return f"{etiqueta:<{ANCHO_ETIQUETA}}{importe:>{ANCHO_IMPORTE},.2f}"


def formatear_nomina(bruto_anual: float, pagas: int = PAGAS) -> str:
    """Devuelve el resumen de la nómina en cinco líneas alineadas.

    Con un número de pagas distinto de PAGAS, la última línea muestra el neto
    de cada paga.

    >>> print(formatear_nomina(30000))
    Bruto anual            30,000.00
    IRPF (23.89 %)         -7,165.50
    Seguridad Social       -1,905.00
    Neto anual             20,929.50
    Neto mensual            1,744.12
    >>> print(formatear_nomina(30000, pagas=14).splitlines()[-1])
    Neto por paga (14)      1,494.96
    """
    neto_anual = calcular_neto_anual(bruto_anual)
    etiqueta_irpf = f"IRPF ({tipo_efectivo(bruto_anual):.2f} %)"
    etiqueta_neto = "Neto mensual" if pagas == PAGAS else f"Neto por paga ({pagas})"
    lineas = [
        linea_nomina("Bruto anual", bruto_anual),
        linea_nomina(etiqueta_irpf, -calcular_irpf(bruto_anual)),
        linea_nomina("Seguridad Social", -calcular_seguridad_social(bruto_anual)),
        linea_nomina("Neto anual", neto_anual),
        linea_nomina(etiqueta_neto, neto_anual / pagas),
    ]
    return "\n".join(lineas)


def a_importe(texto: str) -> float | None:
    """Convierte ``texto`` en un importe. Devuelve None si no es un número.

    Admite espacios alrededor y un punto decimal; no admite signo.

    >>> a_importe(" 30000.50 "), a_importe("abc"), a_importe("-100")
    (30000.5, None, None)
    """
    limpio = texto.strip()
    if limpio.replace(".", "", 1).isdigit() and limpio.isascii():
        return float(limpio)
    return None


def a_pagas(texto: str) -> int | None:
    """Convierte la respuesta en número de pagas. Si está vacía, vale PAGAS.

    Devuelve None si no es uno de los valores de PAGAS_ADMITIDAS.

    >>> a_pagas(""), a_pagas(" 14 "), a_pagas("13"), a_pagas("doce")
    (12, 14, None, None)
    """
    limpio = texto.strip()
    if not limpio:
        return PAGAS
    if limpio.isdigit() and int(limpio) in PAGAS_ADMITIDAS:
        return int(limpio)
    return None


def main(preguntar_pagas: bool = False) -> None:
    """Pide el salario bruto anual y muestra la nómina.

    Con ``preguntar_pagas=True`` pide también el número de pagas (12 o 14).
    """
    bruto_anual = a_importe(input("Salario bruto anual: "))
    if bruto_anual is None or bruto_anual <= 0:
        print("Importe no válido")
        return

    pagas = PAGAS
    if preguntar_pagas:
        pagas = a_pagas(input(f"Número de pagas {PAGAS_ADMITIDAS} [{PAGAS}]: "))
        if pagas is None:
            print("Número de pagas no válido")
            return
    print(formatear_nomina(bruto_anual, pagas))


if __name__ == "__main__":
    main(preguntar_pagas=True)
