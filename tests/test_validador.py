import unittest

from horarios.validador import validar_datos
from tests.utilidades import ejemplo, estudiante, seccion


class TestValidador(unittest.TestCase):

    def assertUnError(self, datos, texto):
        errores = validar_datos(datos)
        self.assertTrue(any(texto in e for e in errores),
                        f"se esperaba un error con '{texto}', se obtuvo {errores}")

    def test_ejemplo_es_valido(self):
        self.assertEqual(validar_datos(ejemplo()), [])

    def test_falta_campo(self):
        d = ejemplo()
        del d["secciones"]
        self.assertUnError(d, "falta el campo 'secciones'")

    # Regla 1: ids y referencias
    def test_id_repetido(self):
        d = ejemplo()
        d["asignaturas"].append({"id": "A01"})
        self.assertUnError(d, "id repetido 'A01'")

    def test_referencia_inexistente(self):
        d = ejemplo()
        seccion(d, "G001")["profesor"] = "P99"
        estudiante(d, "E0001")["companeros"] = ["E9999"]
        estudiante(d, "E0002")["afinidad"] = {"P77": 1}
        self.assertUnError(d, "profesor 'P99' no existe")
        self.assertUnError(d, "compañero 'E9999' no existe")
        self.assertUnError(d, "profesor 'P77' de la afinidad no existe")

    # Regla 2: distancias
    def test_distancias_no_simetricas(self):
        d = ejemplo()
        d["distancias"][0][1] = 10.0
        self.assertUnError(d, "no es simétrica")

    def test_distancias_dimension(self):
        d = ejemplo()
        d["distancias"] = [[0.0]]
        self.assertUnError(d, "matriz de 2 x 2")

    def test_distancia_negativa_y_diagonal(self):
        d = ejemplo()
        d["distancias"][1][1] = 5.0
        self.assertUnError(d, "distancias[1][1] debe ser 0")
        d["distancias"][0][1] = -1
        self.assertUnError(d, "debe ser un número >= 0")

    # Regla 3: franjas
    def test_franja_fuera_de_rango(self):
        d = ejemplo()
        seccion(d, "G001")["franjas"].append(["SA", 1])
        seccion(d, "G002")["franjas"].append(["LU", 8])
        self.assertUnError(d, "franja inválida ['SA', 1]")
        self.assertUnError(d, "franja inválida ['LU', 8]")

    # Regla 4: secciones
    def test_seccion_sin_franjas_y_cupo(self):
        d = ejemplo()
        seccion(d, "G001")["franjas"] = []
        seccion(d, "G002")["cupo"] = 0
        self.assertUnError(d, "al menos una franja")
        self.assertUnError(d, "cupo debe ser un entero >= 1")

    def test_franja_repetida_en_seccion(self):
        d = ejemplo()
        seccion(d, "G001")["franjas"].append(["LU", 1])
        self.assertUnError(d, "franja repetida")

    # Regla 5: solicitudes
    def test_solicitudes(self):
        d = ejemplo()
        e = estudiante(d, "E0001")
        e["solicitudes"].append({"asignatura": "A01", "prioridad": 2})
        e["solicitudes"][1]["prioridad"] = 6
        self.assertUnError(d, "pide dos veces la asignatura 'A01'")
        self.assertUnError(d, "debe ser un entero entre 1 y 5")

    # Regla 6: L_e ∩ N_e y e ∉ C_e
    def test_libres_y_no_disponibles(self):
        d = ejemplo()
        estudiante(d, "E0001")["libres"].append(["VI", 1])
        self.assertUnError(d, "libres y no_disponibles a la vez")

    def test_companero_de_si_mismo(self):
        d = ejemplo()
        estudiante(d, "E0001")["companeros"].append("E0001")
        self.assertUnError(d, "compañero de sí mismo")

    # Regla 7: afinidad y pesos
    def test_afinidad_y_pesos(self):
        d = ejemplo()
        estudiante(d, "E0001")["afinidad"]["P01"] = 3
        d["pesos"]["w3"] = -1
        self.assertUnError(d, "entre -2 y 2")
        self.assertUnError(d, "pesos.w3")


if __name__ == "__main__":
    unittest.main()
