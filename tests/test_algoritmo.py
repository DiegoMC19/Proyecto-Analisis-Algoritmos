import unittest

from horarios.algoritmo import CRITERIOS, backtracking, ordenar, resolver, voraz
from horarios.casos import casos
from horarios.fuerza_bruta import fuerza_bruta
from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.verificador import calcular_objetivo, verificar

PEQUENA = dict(asignaturas=5, solicitudes_por_estudiante=(2, 3), secciones_por_asignatura=(1, 3), holgura=0.7)


def instancia(n, semilla, **kw):
    return instancia_desde_dict(generar(Parametros(estudiantes=n, semilla=semilla, **kw)))


class TestAlgoritmo(unittest.TestCase):

    def test_casos_hechos_a_mano(self):
        for caso in casos():
            with self.subTest(caso=caso["numero"]):
                r = resolver(instancia_desde_dict(caso["instancia"]))
                self.assertEqual(sorted(r.asignacion), sorted(caso["esperada"]))
                self.assertTrue(r.backtracking.completo)

    def test_criterios_ordenan_todas_las_solicitudes(self):
        inst = instancia(40, 1)
        total = sum(len(e.solicitudes) for e in inst.estudiantes.values())
        for c in CRITERIOS:
            with self.subTest(criterio=c):
                orden = ordenar(inst, c)
                self.assertEqual(len(orden), total)
                self.assertEqual(len(set(orden)), total)

    def test_siempre_valida(self):
        for n, semilla in [(30, 1), (80, 2), (200, 3)]:
            for holgura in (0.5, 1.0):
                with self.subTest(n=n, holgura=holgura):
                    inst = instancia(n, semilla, holgura=holgura)
                    for c in CRITERIOS:
                        estado = voraz(inst, c)
                        self.assertTrue(verificar(inst, estado.asignacion()).valida)
                        self.assertAlmostEqual(estado.f, calcular_objetivo(inst, estado.asignacion()).f, places=6)
                    r = resolver(inst, tiempo_max=0.5)
                    reporte = verificar(inst, r.asignacion)
                    self.assertTrue(reporte.valida, [v.a_dict() for v in reporte.violaciones[:3]])
                    self.assertAlmostEqual(r.objetivo.f, reporte.objetivo.f, places=6)

    def test_el_mejor_criterio_y_el_backtracking_no_empeoran(self):
        for semilla in range(4):
            inst = instancia(150, semilla, holgura=0.7)
            r = resolver(inst, tiempo_max=0.5)
            self.assertAlmostEqual(r.f_voraz, max(r.f_criterios.values()), places=6)
            self.assertGreaterEqual(r.objetivo.f, r.f_voraz - 1e-6)

    def test_backtracking_completo_da_el_optimo(self):
        """Si recorre todo el árbol, el backtracking con cota llega al mismo f que
        el backtracking exacto sin cota (fuerza_bruta)."""
        for semilla in range(1, 16):
            with self.subTest(semilla=semilla):
                inst = instancia(4, semilla, **PEQUENA)
                optimo = fuerza_bruta(inst).objetivo.f
                r = resolver(inst, tiempo_max=30)
                self.assertTrue(r.backtracking.completo)
                self.assertAlmostEqual(r.objetivo.f, optimo, places=6)
                self.assertLessEqual(r.f_voraz, optimo + 1e-6)

    def test_backtracking_sin_punto_de_partida(self):
        inst = instancia(4, 3, **PEQUENA)
        optimo = fuerza_bruta(inst).objetivo.f
        bt = backtracking(inst, None, 30)
        self.assertTrue(bt.completo)
        self.assertAlmostEqual(bt.f, optimo, places=6)

    def test_tiempo_limite(self):
        inst = instancia(300, 1)
        r = resolver(inst, tiempo_max=0.2)
        self.assertFalse(r.backtracking.completo)
        self.assertLess(r.tiempo_backtracking, 2.0)


if __name__ == "__main__":
    unittest.main()
