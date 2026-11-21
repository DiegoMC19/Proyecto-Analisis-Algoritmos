"""Genera las gráficas y las tablas de resumen a partir de resultados/experimentos/*.csv.

Uso:
    python graficas.py

Cada gráfica se guarda en PNG (para ver) y PDF (vectorial, para el LaTeX).
También escribe resultados/experimentos/resumen.md con las tablas.
"""

import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402

CARPETA = Path("resultados/experimentos")

# Paleta (modo claro): un color fijo por algoritmo, siempre el mismo en todas las gráficas.
COLOR = {"voraz": "#2a78d6", "bl": "#eb6834", "fb": "#1baf7a"}
NOMBRE = {"voraz": "Voraz", "bl": "Voraz + búsqueda local", "fb": "Fuerza bruta"}
TINTA, TINTA_2, REJILLA = "#0b0b0b", "#52514e", "#e5e4e0"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "text.color": TINTA, "axes.labelcolor": TINTA_2, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
    "axes.edgecolor": REJILLA, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": REJILLA, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False, "lines.linewidth": 2, "lines.markersize": 6,
})


def leer(nombre: str) -> list[dict]:
    ruta = CARPETA / nombre
    if not ruta.exists():
        return []
    def valor(v):
        try:
            return float(v)
        except ValueError:
            return v

    with open(ruta, encoding="utf-8") as f:
        return [{k: valor(v) for k, v in fila.items()} for fila in csv.DictReader(f)]


def por(filas, clave):
    grupos = defaultdict(list)
    for f in filas:
        grupos[f[clave]].append(f)
    return dict(sorted(grupos.items()))


def guardar(fig, nombre: str) -> None:
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(CARPETA / f"{nombre}.{ext}", dpi=200)
    plt.close(fig)
    print(f"  -> {CARPETA / nombre}.png / .pdf")


def pendiente(xs, ys) -> float:
    """Exponente b de y ≈ a·x^b (recta en escala log-log)."""
    return float(np.polyfit(np.log(xs), np.log(ys), 1)[0])


# ----------------------------------------------------------------------------

def grafica_tiempo(esc, resumen):
    g = por(esc, "n")
    ns = list(g)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for clave, col in (("voraz", "tiempo_voraz"), ("bl", "tiempo_bl")):
        med = [st.median(max(f[col], 1e-4) for f in g[n]) for n in ns]
        ax.plot(ns, med, marker="o", color=COLOR[clave], label=NOMBRE[clave])
        b = pendiente(ns, med)
        ax.annotate(f"≈ n$^{{{b:.2f}}}$", (ns[-1], med[-1]), textcoords="offset points", xytext=(8, -4),
                    color=TINTA_2, fontsize=10)
        resumen.append(f"- Crecimiento empírico del tiempo ({NOMBRE[clave]}): ~ n^{b:.2f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Número de estudiantes n (escala log)")
    ax.set_ylabel("Tiempo (s, escala log)")
    ax.set_title("Tiempo de ejecución según el tamaño")
    ax.set_xticks(ns, [str(int(n)) for n in ns])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.legend(loc="upper left")
    ax.margins(x=0.12)
    guardar(fig, "tiempo_vs_n")


def grafica_fuerza_bruta(cal):
    g = por(cal, "n")
    ns = list(g)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for clave, col in (("fb", "tiempo_fb"), ("bl", "tiempo_bl")):
        med = [st.median(max(f[col], 1e-5) for f in g[n]) for n in ns]
        ax.plot(ns, med, marker="o", color=COLOR[clave], label=NOMBRE[clave])
    ax.set_yscale("log")
    ax.set_xticks(ns, [str(int(n)) for n in ns])
    ax.set_xlabel("Número de estudiantes n")
    ax.set_ylabel("Tiempo mediano (s, escala log)")
    ax.set_title("Fuerza bruta contra el algoritmo en instancias pequeñas")
    ax.legend(loc="upper left")
    guardar(fig, "fuerza_bruta_vs_algoritmo")


def grafica_brecha(cal):
    g = por(cal, "n")
    ns = list(g)
    x = np.arange(len(ns))
    ancho = 0.36
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for i, (clave, col) in enumerate((("voraz", "brecha_voraz"), ("bl", "brecha_bl"))):
        medias = [st.mean(f[col] for f in g[n]) for n in ns]
        barras = ax.bar(x + (i - 0.5) * (ancho + 0.02), medias, ancho, color=COLOR[clave], label=NOMBRE[clave])
        for b, v in zip(barras, medias):
            ax.annotate(f"{v:.2f} %", (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=8, color=TINTA_2)
    ax.set_xticks(x, [f"n = {int(n)}\n({len(g[n])} inst.)" for n in ns])
    ax.set_ylabel("Brecha promedio contra el óptimo (%)")
    ax.set_title("Qué tan lejos queda cada algoritmo del óptimo")
    ax.set_ylim(0, ax.get_ylim()[1] * 1.3)
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)
    guardar(fig, "brecha_optimo")


def grafica_competencia(comp):
    hs = [f["holgura"] for f in comp]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for clave in ("voraz", "bl"):
        ax.plot(hs, [f[f"pct_inscritas_{clave}"] for f in comp], marker="o", color=COLOR[clave], label=NOMBRE[clave])
    ax.set_xlabel("Holgura (cupos ofrecidos / solicitudes de cada asignatura)")
    ax.set_ylabel("Solicitudes inscritas (%)")
    ax.set_title(f"Efecto de la competencia por cupos (n = {int(comp[0]['n'])})")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower right")
    guardar(fig, "competencia")


# ----------------------------------------------------------------------------

def tablas(cal, esc, comp, resumen):
    if cal:
        resumen += ["", "## Calidad contra el óptimo", "",
                    "| n | instancias | espacio (mediana) | nodos FB (mediana) | tiempo FB (mediana) "
                    "| óptimas voraz | óptimas voraz+BL | brecha voraz | brecha voraz+BL |",
                    "|---|---|---|---|---|---|---|---|---|"]
        for n, fs in por(cal, "n").items():
            resumen.append(
                f"| {int(n)} | {len(fs)} | {st.median(f['espacio'] for f in fs):,.0f} "
                f"| {st.median(f['nodos'] for f in fs):,.0f} | {st.median(f['tiempo_fb'] for f in fs):.3f} s "
                f"| {sum(f['brecha_voraz'] < 1e-6 for f in fs)} | {sum(f['brecha_bl'] < 1e-6 for f in fs)} "
                f"| {st.mean(f['brecha_voraz'] for f in fs):.2f} % | {st.mean(f['brecha_bl'] for f in fs):.2f} % |")
        resumen.append(f"\nTotal: voraz óptimo en {sum(f['brecha_voraz'] < 1e-6 for f in cal)}/{len(cal)}, "
                       f"voraz+BL en {sum(f['brecha_bl'] < 1e-6 for f in cal)}/{len(cal)}; "
                       f"brecha máxima voraz {max(f['brecha_voraz'] for f in cal):.2f} %, "
                       f"voraz+BL {max(f['brecha_bl'] for f in cal):.2f} %.")
    if esc:
        resumen += ["", "## Escalabilidad (promedio de las semillas)", "",
                    "| n | asignaturas | secciones | solicitudes | tiempo voraz | tiempo voraz+BL "
                    "| inscritas voraz | inscritas voraz+BL | mejora de f por BL |",
                    "|---|---|---|---|---|---|---|---|---|"]
        for n, fs in por(esc, "n").items():
            m = lambda c: st.mean(f[c] for f in fs)  # noqa: E731
            resumen.append(
                f"| {int(n)} | {m('asignaturas'):.0f} | {m('secciones'):.0f} | {m('solicitudes'):.0f} "
                f"| {m('tiempo_voraz'):.3f} s | {m('tiempo_bl'):.2f} s "
                f"| {100 * m('inscritas_voraz') / m('solicitudes'):.1f} % "
                f"| {100 * m('inscritas_bl') / m('solicitudes'):.1f} % | +{m('mejora_bl_pct'):.2f} % |")
    if comp:
        resumen += ["", "## Competencia por cupos", "",
                    "| holgura | inscritas voraz | inscritas voraz+BL | prioridad 5 inscritas (voraz+BL) |",
                    "|---|---|---|---|"]
        for f in comp:
            resumen.append(f"| {f['holgura']} | {f['pct_inscritas_voraz']} % | {f['pct_inscritas_bl']} % "
                           f"| {f['pct_prioridad5_bl']} % |")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    cal, esc, comp = leer("calidad.csv"), leer("escalabilidad.csv"), leer("competencia.csv")
    if not (cal or esc or comp):
        print("No hay resultados; primero ejecute python experimentos.py")
        return 1
    resumen = ["# Resumen de experimentos", ""]
    if esc:
        grafica_tiempo(esc, resumen)
    if cal:
        grafica_fuerza_bruta(cal)
        grafica_brecha(cal)
    if comp:
        grafica_competencia(comp)
    tablas(cal, esc, comp, resumen)
    (CARPETA / "resumen.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print(f"  -> {CARPETA / 'resumen.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
