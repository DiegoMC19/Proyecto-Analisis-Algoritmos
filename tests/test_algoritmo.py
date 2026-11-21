import random
import unittest

from horarios.algoritmo import delta_intercambio, resolver, voraz
from horarios.casos import casos
from horarios.fuerza_bruta import fuerza_bruta
from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.verificador import calcular_objetivo, verificar


def instancia(n, semilla, **kw):
    return instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=semilla, **kw)))


class TestAlgoritmo(unittest.TestCase):

    def test_casos_hechos_a_mano(self):
        for caso in casos():
            with self.subTest(caso=caso["numero"]):
                r = resolver(instancia_desde_dict(caso["instancia"]))
                self.assertEqual(sorted(r.asignacion), sorted(caso["esperada"]))

    def test_siempre_valida(self):
        for n, semilla in [(30, 1), (80, 2), (200, 3)]:
            for holgura in (0.5, 1.0):
                with self.subTest(n=n, holgura=holgura):
                    inst = instancia(n, semilla, holgura=holgura)
                    for con_busqueda in (False, True):
                        r = resolver(inst, con_busqueda=con_busqueda)
                        reporte = verificar(inst, r.asignacion)
                        self.assertTrue(reporte.valida, [v.a_dict() for v in reporte.violaciones[:3]])
                        self.assertAlmostEqual(r.objetivo.f, reporte.objetivo.f, places=6)

    def test_busqueda_local_no_empeora(self):
        for semilla in range(4):
            inst = instancia(150, semilla, holgura=0.7)
            r = resolver(inst)
            self.assertGreaterEqual(r.objetivo.f, r.f_voraz - 1e-6)
            self.assertTrue(r.busqueda.optimo_local)

    def test_nunca_supera_el_optimo(self):
        kw = dict(asignaturas=5, solicitudes_por_estudiante=(2, 3), secciones_por_asignatura=(1, 3), holgura=0.7)
        for semilla in range(10):
            with self.subTest(semilla=semilla):
                inst = instancia(4, semilla, **kw)
                optimo = fuerza_bruta(inst).objetivo.f
                f = resolver(inst).objetivo.f
                self.assertLessEqual(f, optimo + 1e-6)

    def test_delta_intercambio_exacto(self):
        """El Δf calculado sin tocar la asignación es igual a hacer el intercambio de verdad."""
        inst = instancia(300, 5, holgura=0.6, max_companeros=8)
        estado = voraz(inst)
        rng = random.Random(0)
        probados = 0
        for a, secs in inst.secciones_por_asignatura.items():
            if len(secs) < 2:
                continue
            g1, g2 = secs[0], secs[1]
            for e1 in list(estado.inscritos[g1]):
                for e2 in list(estado.inscritos[g2]):
                    F1, F2 = inst.secciones[g1].franjas, inst.secciones[g2].franjas
                    if (F2 & (estado.ocupadas[e1] - F1)) or (F1 & (estado.ocupadas[e2] - F2)):
                        continue
                    if F2 & inst.estudiantes[e1].no_disponibles or F1 & inst.estudiantes[e2].no_disponibles:
                        continue
                    delta = delta_intercambio(estado, e1, g1, e2, g2)
                    antes = estado.f
                    estado.retirar(e1, g1); estado.retirar(e2, g2)
                    estado.inscribir(e1, g2); estado.inscribir(e2, g1)
                    self.assertAlmostEqual(estado.f - antes, delta, places=6)
                    estado.retirar(e1, g2); estado.retirar(e2, g1)
                    estado.inscribir(e1, g1); estado.inscribir(e2, g2)
                    probados += 1
                    if rng.random() < 0.3:
                        break
        self.assertGreater(probados, 50)
        x = estado.asignacion()
        self.assertAlmostEqual(estado.f, calcular_objetivo(inst, x).f, places=6)


if __name__ == "__main__":
    unittest.main()
