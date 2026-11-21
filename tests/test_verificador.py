import unittest

from horarios.modelo import instancia_desde_dict
from horarios.verificador import calcular_objetivo, comparar_con_esperada, verificar
from tests.utilidades import ejemplo, estudiante, seccion

# Asignación del documento (Código 2)
X_DOC = [("E0001", "G001"), ("E0001", "G002"), ("E0002", "G001")]


def restricciones(reporte):
    return [v.restriccion for v in reporte.violaciones]


class TestObjetivo(unittest.TestCase):

    def test_valores_del_documento(self):
        """Los valores de la Sección 4.3: f1=12, f2=1, f3=2, f4=0, f5=784.6, f=116.154."""
        o = calcular_objetivo(instancia_desde_dict(ejemplo()), X_DOC)
        self.assertEqual((o.f1, o.f2, o.f3, o.f4), (12, 1, 2, 0))
        self.assertAlmostEqual(o.f5, 784.6)
        self.assertAlmostEqual(o.f, 116.154)

    def test_asignacion_vacia(self):
        o = calcular_objetivo(instancia_desde_dict(ejemplo()), [])
        self.assertEqual(o.f, 0)

    def test_f3_solo_si_comparten_seccion(self):
        inst = instancia_desde_dict(ejemplo())
        # Solo E0001 en G001: su compañero no está, f3 = 0.
        self.assertEqual(calcular_objetivo(inst, [("E0001", "G001")]).f3, 0)

    def test_f3_no_simetrico(self):
        d = ejemplo()
        estudiante(d, "E0002")["companeros"] = []
        o = calcular_objetivo(instancia_desde_dict(d), X_DOC)
        self.assertEqual(o.f3, 1)

    def test_f4_franja_libre_ocupada(self):
        d = ejemplo()
        estudiante(d, "E0001")["libres"] = [["LU", 1], ["LU", 2], ["JU", 1]]
        o = calcular_objetivo(instancia_desde_dict(d), X_DOC)
        self.assertEqual(o.f4, 2)

    def test_f5_solo_clases_seguidas_mismo_dia(self):
        d = ejemplo()
        # G002 pasa al martes: ya no es seguida de G001 (que es lunes y miércoles).
        seccion(d, "G002")["franjas"] = [["MA", 3], ["MA", 4]]
        o = calcular_objetivo(instancia_desde_dict(d), X_DOC)
        self.assertEqual(o.f5, 0)

    def test_f5_mismo_salon_no_suma(self):
        d = ejemplo()
        seccion(d, "G002")["salon"] = "S01"
        o = calcular_objetivo(instancia_desde_dict(d), X_DOC)
        self.assertEqual(o.f5, 0)


class TestRestricciones(unittest.TestCase):

    def test_asignacion_del_documento_es_valida(self):
        r = verificar(instancia_desde_dict(ejemplo()), X_DOC)
        self.assertTrue(r.valida, [v.a_dict() for v in r.violaciones])

    def test_r1_asignatura_no_pedida(self):
        r = verificar(instancia_desde_dict(ejemplo()), [("E0002", "G002")])
        self.assertEqual(restricciones(r), [1])

    def test_r2_misma_asignatura_dos_veces(self):
        d = ejemplo()
        d["secciones"].append({"id": "G003", "asignatura": "A01", "profesor": "P02",
                               "salon": "S02", "franjas": [["JU", 1]], "cupo": 10})
        r = verificar(instancia_desde_dict(d), [("E0001", "G001"), ("E0001", "G003")])
        self.assertEqual(restricciones(r), [2])

    def test_r2_cruce_de_horario(self):
        d = ejemplo()
        seccion(d, "G002")["franjas"] = [["LU", 2], ["LU", 3]]
        r = verificar(instancia_desde_dict(d), [("E0001", "G001"), ("E0001", "G002")])
        self.assertEqual(restricciones(r), [2])
        self.assertIn("('LU', 2)", r.violaciones[0].detalle)

    def test_r3_franja_no_disponible(self):
        d = ejemplo()
        estudiante(d, "E0002")["no_disponibles"] = [["MI", 2]]
        r = verificar(instancia_desde_dict(d), X_DOC)
        self.assertEqual(restricciones(r), [3])

    def test_r4_cupo(self):
        d = ejemplo()
        seccion(d, "G001")["cupo"] = 1
        r = verificar(instancia_desde_dict(d), X_DOC)
        self.assertEqual(restricciones(r), [4])
        self.assertEqual(r.violaciones[0].detalle, "2 inscritos, cupo 1")

    def test_formato(self):
        inst = instancia_desde_dict(ejemplo())
        r = verificar(inst, [("E0001", "G001"), ("E0001", "G001"), ("E9", "G001"), ("E0002", "G9")])
        self.assertEqual(restricciones(r), ["formato"] * 3)
        # El par repetido no cuenta doble en f.
        self.assertEqual(r.objetivo.f1, 5)


class TestComparacion(unittest.TestCase):

    ESPERADA = {"origen": "fuerza_bruta", "optimo": True, "asignacion": None, "f": 116.154}

    def test_correcta(self):
        inst = instancia_desde_dict(ejemplo())
        r = verificar(inst, X_DOC)
        self.assertTrue(comparar_con_esperada(r, X_DOC, self.ESPERADA)["correcta"])

    def test_suboptima(self):
        inst = instancia_desde_dict(ejemplo())
        x = [("E0001", "G001"), ("E0002", "G001")]
        r = verificar(inst, x)
        self.assertFalse(comparar_con_esperada(r, x, self.ESPERADA)["correcta"])

    def test_manual_exige_misma_asignacion(self):
        d = ejemplo()
        # Dos secciones idénticas de A01: misma f con E0002 en cualquiera de las dos.
        d["secciones"].append({"id": "G003", "asignatura": "A01", "profesor": "P01",
                               "salon": "S01", "franjas": [["LU", 1]], "cupo": 5})
        estudiante(d, "E0002")["companeros"] = []
        inst = instancia_desde_dict(d)
        esperada = {"origen": "manual", "optimo": True, "f": 40,
                    "asignacion": [{"estudiante": "E0002", "seccion": "G001"}]}
        x = [("E0002", "G003")]
        r = verificar(inst, x)
        self.assertAlmostEqual(r.objetivo.f, 40)
        self.assertFalse(comparar_con_esperada(r, x, esperada)["correcta"])

    def test_sin_optimo_conocido(self):
        inst = instancia_desde_dict(ejemplo())
        r = verificar(inst, X_DOC)
        res = comparar_con_esperada(r, X_DOC, {"origen": "ninguno", "optimo": False,
                                              "asignacion": None, "f": None})
        self.assertTrue(res["correcta"])


if __name__ == "__main__":
    unittest.main()
