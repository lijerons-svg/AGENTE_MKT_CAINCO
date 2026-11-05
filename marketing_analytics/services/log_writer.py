"""Genera Log_Ejecucion.txt a partir de una ejecución ya registrada en SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from marketing_analytics.services.orchestrator import ResumenEjecucion


def escribir_log_ejecucion(
    conn: sqlite3.Connection, resumen: ResumenEjecucion, ruta_salida: str | Path
) -> Path:
    fila = conn.execute(
        "SELECT * FROM ejecuciones WHERE id = ?", (resumen.ejecucion_id,)
    ).fetchone()

    lineas = [
        "=== Log de ejecución — Marketing Analytics ===",
        f"Ejecución ID: {resumen.ejecucion_id}",
        f"Hora inicio: {fila['hora_inicio']}",
        f"Hora final: {fila['hora_fin']}",
        f"Tiempo de ejecución (seg): {fila['tiempo_ejecucion_seg']:.2f}",
        f"Estado: {fila['estado']}",
        "",
        "--- Totales ---",
        f"Registros descargados: {fila['registros_descargados']}",
        f"Registros nuevos: {fila['registros_nuevos']}",
        f"Registros actualizados: {fila['registros_actualizados']}",
        f"Registros descartados (sin cambios): {fila['registros_descartados']}",
        "",
        "--- Por conector ---",
    ]

    for item in resumen.por_conector:
        if item.error:
            lineas.append(f"[ERROR] {item.nombre}: {item.error}")
        else:
            r = item.resultado
            lineas.append(
                f"[OK] {item.nombre}: nuevos={r.nuevos} actualizados={r.actualizados} "
                f"descartados={r.descartados}"
            )

    if resumen.errores:
        lineas += ["", "--- Errores ---", *resumen.errores]

    ruta_salida = Path(ruta_salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    ruta_salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return ruta_salida
