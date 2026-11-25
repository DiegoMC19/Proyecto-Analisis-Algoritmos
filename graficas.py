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
COLOR = {"voraz": "#2a78d6", "vc": "#7a5af5", "bt": "#eb6834", "fb": "#1baf7a"}
NOMBRE = {"voraz": "Voraz (prioridad)", "vc": "Voraz (3 criterios)", "bt": "Voraz + backtracking con cota",
          "fb": "Backtracking exacto sin cota"}
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
    for clave, col in (("voraz", "tiempo_voraz"), ("vc", "tiempo_vc")):
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
    for clave, col in (("fb", "tiempo_fb"), ("bt", "tiempo_bt")):
        med = [st.median(max(f[col], 1e-5) for f in g[n]) for n in ns]
        ax.plot(ns, med, marker="o", color=COLOR[clave], label=NOMBRE[clave])
    ax.set_yscale("log")
    ax.set_xticks(ns, [str(int(n)) for n in ns])
    ax.set_xlabel("Número de estudiantes n")
    ax.set_ylabel("Tiempo mediano (s, escala log)")
    ax.set_title("Backtracking exacto: sin cota contra con cota y voraz")
    ax.legend(loc="upper left")
    guardar(fig, "fuerza_bruta_vs_algoritmo")


def grafica_brecha(cal):
    g = por(cal, "n")
    ns = list(g)
    x = np.arange(len(ns))
    ancho = 0.26
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for i, (clave, col) in enumerate((("voraz", "brecha_voraz"), ("vc", "brecha_vc"), ("bt", "brecha_bt"))):
        medias = [st.mean(f[col] for f in g[n]) for n in ns]
        barras = ax.bar(x + (i - 1) * (ancho + 0.02), medias, ancho, color=COLOR[clave], label=NOMBRE[clave])
        for b, v in zip(barras, medias):
            ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=7.5, color=TINTA_2)
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
    ax.plot(hs, [f["pct_prioridad5_bt"] for f in comp], marker="o", color=COLOR["bt"],
            label="Solicitudes de prioridad 5")
    ax.plot(hs, [f["pct_inscritas_bt"] for f in comp], marker="o", color=COLOR["voraz"],
            label="Todas las solicitudes")
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
                    "| n | instancias | espacio (mediana) | nodos sin cota | tiempo sin cota | nodos con cota "
                    "| tiempo voraz+BT | óptimas voraz | óptimas 3 criterios | óptimas voraz+BT "
                    "| brecha voraz | brecha 3 criterios | brecha voraz+BT |",
                    "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for n, fs in por(cal, "n").items():
            opt = lambda c: sum(f[c] < 1e-6 for f in fs)  # noqa: E731
            m = lambda c: st.mean(f[c] for f in fs)  # noqa: E731
            resumen.append(
                f"| {int(n)} | {len(fs)} | {st.median(f['espacio'] for f in fs):,.0f} "
                f"| {st.median(f['nodos'] for f in fs):,.0f} | {st.median(f['tiempo_fb'] for f in fs):.3f} s "
                f"| {st.median(f['nodos_bt'] for f in fs):,.0f} | {st.median(f['tiempo_bt'] for f in fs):.4f} s "
                f"| {opt('brecha_voraz')} | {opt('brecha_vc')} | {opt('brecha_bt')} "
                f"| {m('brecha_voraz'):.2f} % | {m('brecha_vc'):.2f} % | {m('brecha_bt'):.2f} % |")
        tot = lambda c: sum(f[c] < 1e-6 for f in cal)  # noqa: E731
        resumen.append(f"\nTotal: óptimo en {tot('brecha_voraz')}/{len(cal)} (voraz), {tot('brecha_vc')}/{len(cal)} "
                       f"(3 criterios), {tot('brecha_bt')}/{len(cal)} (voraz+BT); brecha máxima voraz "
                       f"{max(f['brecha_voraz'] for f in cal):.2f} %, 3 criterios {max(f['brecha_vc'] for f in cal):.2f} %; "
                       f"backtracking completo en {sum(f['completo_bt'] == 'True' for f in cal)}/{len(cal)}.")
    if esc:
        resumen += ["", "## Escalabilidad (promedio de las semillas)", "",
                    "| n | asignaturas | secciones | solicitudes | tiempo voraz | tiempo 3 criterios "
                    "| inscritas | mejora por 3 criterios | mejora por backtracking | criterio ganador |",
                    "|---|---|---|---|---|---|---|---|---|---|"]
        for n, fs in por(esc, "n").items():
            m = lambda c: st.mean(f[c] for f in fs)  # noqa: E731
            ganadores = ", ".join(sorted({f["criterio"] for f in fs}))
            resumen.append(
                f"| {int(n)} | {m('asignaturas'):.0f} | {m('secciones'):.0f} | {m('solicitudes'):.0f} "
                f"| {m('tiempo_voraz'):.3f} s | {m('tiempo_vc'):.3f} s "
                f"| {100 * m('inscritas_bt') / m('solicitudes'):.1f} % "
                f"| +{m('mejora_vc_pct'):.2f} % | +{m('mejora_bt_pct'):.3f} % | {ganadores} |")
    if comp:
        resumen += ["", "## Competencia por cupos", "",
                    "| holgura | inscritas 3 criterios | inscritas voraz+BT | prioridad 5 inscritas |",
                    "|---|---|---|---|"]
        for f in comp:
            resumen.append(f"| {f['holgura']} | {f['pct_inscritas_vc']} % | {f['pct_inscritas_bt']} % "
                           f"| {f['pct_prioridad5_bt']} % |")


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
