import itertools
import math
import random
import unittest

from horarios.casos import casos
from horarios.estado import Estado
from horarios.fuerza_bruta import InstanciaMuyGrande, fuerza_bruta, solicitudes_de
from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.verificador import calcular_objetivo, verificar
from tests.utilidades import ejemplo


def pequena(semilla, n=3):
    p = Parametros(estudiantes=n, semilla=semilla, asignaturas=4,
                   solicitudes_por_estudiante=(1, 3), secciones_por_asignatura=(1, 3), holgura=0.7)
    return instancia_desde_dict(generar(p))


def optimo_ingenuo(inst):
    """Prueba literalmente las (t+1)^(n*q) combinaciones y se queda con la mejor válida."""
    sol = solicitudes_de(inst)
    opciones = [[None] + inst.secciones_por_asignatura[a] for _, a in sol]
    mejor = -math.inf
    for eleccion in itertools.product(*opciones):
        x = [(e, g) for (e, _), g in zip(sol, eleccion) if g is not None]
        r = verificar(inst, x)
        if r.valida:
            mejor = max(mejor, r.objetivo.f)
    return mejor


class TestEstado(unittest.TestCase):

    def test_incremental_igual_a_recalcular(self):
        """Inscribir y retirar al azar: f del Estado siempre igual a calcular_objetivo."""
        for semilla in range(5):
            inst = instancia_desde_dict(generar(Parametros(estudiantes=60, semilla=semilla)))
            estado = Estado(inst)
            rng = random.Random(semilla)
            pares = [(e, g) for e in inst.estudiantes for a in inst.estudiantes[e].solicitudes
                     for g in inst.secciones_por_asignatura[a]]
            for _ in range(1500):
                e, g = rng.choice(pares)
                if g in estado.secciones_de[e]:
                    estado.retirar(e, g)
                elif estado.puede_inscribir(e, g):
                    estado.inscribir(e, g)
            x = estado.asignacion()
            self.assertTrue(verificar(inst, x).valida)
            self.assertAlmostEqual(estado.f, calcular_objetivo(inst, x).f, places=6)

    def test_ejemplo(self):
        inst = instancia_desde_dict(ejemplo())
        estado = Estado(inst)
        for e, g in [("E0001", "G001"), ("E0001", "G002"), ("E0002", "G001")]:
            self.assertTrue(estado.puede_inscribir(e, g))
            estado.inscribir(e, g)
        self.assertAlmostEqual(estado.f, 116.154)


class TestFuerzaBruta(unittest.TestCase):

    def test_casos_hechos_a_mano(self):
        for caso in casos():
            with self.subTest(caso=caso["numero"]):
                r = fuerza_bruta(instancia_desde_dict(caso["instancia"]))
                self.assertEqual(sorted(r.asignacion), sorted(caso["esperada"]))

    def test_igual_al_recorrido_ingenuo(self):
        for semilla in range(8):
            with self.subTest(semilla=semilla):
                inst = pequena(semilla)
                r = fuerza_bruta(inst)
                self.assertTrue(verificar(inst, r.asignacion).valida)
                self.assertAlmostEqual(r.objetivo.f, optimo_ingenuo(inst), places=6)
                self.assertLessEqual(r.hojas, r.espacio)

    def test_limite(self):
        with self.assertRaises(InstanciaMuyGrande):
            fuerza_bruta(pequena(0, n=3), limite=1)


if __name__ == "__main__":
    unittest.main()
