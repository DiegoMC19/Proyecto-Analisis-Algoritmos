import unittest
from collections import defaultdict

from horarios.generador import Parametros, generar
from horarios.modelo import instancia_desde_dict
from horarios.validador import validar_datos


class TestGenerador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p = Parametros(estudiantes=300, semilla=7)
        cls.datos = generar(cls.p)

    def test_es_valida(self):
        self.assertEqual(validar_datos(self.datos), [])

    def test_valida_con_varias_semillas_y_tamanos(self):
        for n, semilla in [(1, 1), (10, 2), (50, 3), (120, 4)]:
            with self.subTest(n=n, semilla=semilla):
                self.assertEqual(validar_datos(generar(Parametros(estudiantes=n, semilla=semilla))), [])

    def test_misma_semilla_misma_instancia(self):
        self.assertEqual(generar(Parametros(estudiantes=300, semilla=7)), self.datos)

    def test_otra_semilla_otra_instancia(self):
        self.assertNotEqual(generar(Parametros(estudiantes=300, semilla=8)), self.datos)

    def test_meta_guarda_parametros_y_semilla(self):
        meta = self.datos["meta"]
        self.assertEqual(meta["semilla"], 7)
        self.assertEqual(meta["parametros"]["estudiantes"], 300)
        self.assertEqual(meta["parametros"]["asignaturas"], len(self.datos["asignaturas"]))

    def test_rangos(self):
        lo, hi = self.p.solicitudes_por_estudiante
        for e in self.datos["estudiantes"]:
            self.assertTrue(lo <= len(e["solicitudes"]) <= hi)
        por_asig = defaultdict(int)
        for g in self.datos["secciones"]:
            por_asig[g["asignatura"]] += 1
        lo, hi = self.p.secciones_por_asignatura
        for a in self.datos["asignaturas"]:
            self.assertTrue(lo <= por_asig[a["id"]] <= hi)

    def test_horario_de_dos_sesiones_de_dos_bloques(self):
        for g in self.datos["secciones"]:
            dias = defaultdict(list)
            for d, b in g["franjas"]:
                dias[d].append(b)
            self.assertEqual(len(dias), 2)
            for bloques in dias.values():
                self.assertEqual(sorted(bloques)[1] - sorted(bloques)[0], 1)

    def test_salon_y_profesor_sin_dos_clases_a_la_vez(self):
        for campo in ("salon", "profesor"):
            ocupado = defaultdict(set)
            for g in self.datos["secciones"]:
                franjas = {tuple(f) for f in g["franjas"]}
                self.assertFalse(ocupado[g[campo]] & franjas, f"{campo} {g[campo]} con cruce")
                ocupado[g[campo]] |= franjas

    def test_companeros_simetricos(self):
        comp = {e["id"]: set(e["companeros"]) for e in self.datos["estudiantes"]}
        for e, cs in comp.items():
            for c in cs:
                self.assertIn(e, comp[c])

    def test_holgura_controla_la_competencia(self):
        def cupos_sobre_demanda(holgura):
            d = generar(Parametros(estudiantes=300, semilla=7, holgura=holgura))
            demanda = sum(len(e["solicitudes"]) for e in d["estudiantes"])
            return sum(g["cupo"] for g in d["secciones"]) / demanda
        self.assertLess(cupos_sobre_demanda(0.5), 0.6)
        self.assertGreater(cupos_sobre_demanda(1.5), 1.3)

    def test_se_puede_cargar_en_el_modelo(self):
        inst = instancia_desde_dict(self.datos)
        self.assertEqual(len(inst.estudiantes), 300)
        s1, s2 = inst.salones[0], inst.salones[1]
        self.assertEqual(inst.distancia(s1, s2), inst.distancia(s2, s1))


if __name__ == "__main__":
    unittest.main()
