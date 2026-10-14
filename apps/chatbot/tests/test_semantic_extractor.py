import pytest
from services.semantic_extractor import semantic_extractor, SemanticExtractor, SemanticExtractionResult


CONSORCIOS_MOCK = [
    "Consorcio Callao 2334",
    "Consorcio Av. Corrientes 1240",
    "Edificio Pueyrredon 850",
]


class TestSemanticExtractorRulesFallback:
    """Verifica el extractor en modo contingencia (cero dependencias de hardware)."""

    def setup_method(self):
        self.extractor = SemanticExtractor(model_path="non_existent_model.gguf")

    def test_fallback_unit_extraction(self):
        res = self.extractor.extract("Soy del 4B y tengo una filtracion", CONSORCIOS_MOCK)
        assert res.unidad_funcional == "4B"
        assert res.categoria == "PLOMERIA"
        assert res.metodo == "FALLBACK_RULES"

    def test_fallback_consorcio_extraction(self):
        res = self.extractor.extract("Aca en Callao se rompio el porton", CONSORCIOS_MOCK)
        assert res.consorcio_mencionado == "Consorcio Callao 2334"
        assert res.categoria == "PORTON_ACCESO"

    def test_fallback_emergency_detection(self):
        res = self.extractor.extract("Urgente nos quedamos atrapados en el ascensor", CONSORCIOS_MOCK)
        assert res.es_emergencia is True
        assert res.categoria == "ASCENSORES"

    def test_fallback_payment_request(self):
        res = self.extractor.extract("Buenas, me pasan el cbu para pagar?", CONSORCIOS_MOCK)
        assert res.intencion == "SOLICITUD_DATOS_PAGO"

    def test_fallback_payment_confirmation(self):
        res = self.extractor.extract("Aviso que ya pague las expensas", CONSORCIOS_MOCK)
        assert res.intencion == "CONFIRMACION_PAGO"


class TestSemanticExtractorModelQwen3B:
    """Batería exhaustiva de pruebas con el modelo Qwen 2.5 3B."""

    @pytest.fixture(autouse=True)
    def ensure_model_available(self):
        if not semantic_extractor._has_model:
            pytest.skip("Modelo Qwen 2.5 3B GGUF no disponible en el entorno")

    def test_whisper_spoken_numbers_normalization(self):
        """Caso 1: Audio de Whisper transcribiendo números en palabras."""
        res = semantic_extractor.extract(
            "Hola te hablo del cuarto be de callao, se me revento un caño y se inunda todo",
            CONSORCIOS_MOCK,
        )
        assert res.unidad_funcional in ("4° B", "4B", "4°B")
        assert res.consorcio_mencionado == "Consorcio Callao 2334"
        assert res.categoria == "PLOMERIA"
        assert res.es_emergencia is True
        assert res.metodo == "QWEN_3B"

    def test_whisper_ground_floor(self):
        """Caso 2: Planta baja en palabras."""
        res = semantic_extractor.extract(
            "Buenas tardes, soy de planta baja a en pueyrredon, no anda el portero",
            CONSORCIOS_MOCK,
        )
        assert res.unidad_funcional in ("PB A", "PB", "Planta Baja A")
        assert res.consorcio_mencionado == "Edificio Pueyrredon 850"
        assert res.categoria in ("PORTON_ACCESO", "ELECTRICIDAD", "ADMINISTRACION_CONSULTA", "OTRO")
        assert res.es_emergencia is False

    def test_argentinian_slang_payments(self):
        """Caso 3: Modismos argentinos de pago (garpé, alias, cbu)."""
        res_cbu = semantic_extractor.extract(
            "Hola Ivana, me pasas el cbu o alias para transferir lo de este mes?",
            CONSORCIOS_MOCK,
        )
        assert res_cbu.intencion in ("SOLICITUD_DATOS_PAGO", "CONSULTA_GENERAL")
        assert res_cbu.es_emergencia is False

        res_pago = semantic_extractor.extract(
            "Ya garpe las expensas, ahi te mande el comprobante",
            CONSORCIOS_MOCK,
        )
        assert res_pago.intencion in ("CONFIRMACION_PAGO", "CONSULTA_GENERAL")
        assert res_pago.es_emergencia is False

    def test_critical_emergencies_without_explicit_keywords(self):
        """Caso 4: Emergencia crítica sin usar la palabra 'emergencia'."""
        # 4.1 Ascensor trabado
        res_asc = semantic_extractor.extract(
            "Aca en corrientes al mil doscientos nos quedamos trabados en la cabina entre el 3 y el 4",
            CONSORCIOS_MOCK,
        )
        assert res_asc.consorcio_mencionado == "Consorcio Av. Corrientes 1240"
        assert res_asc.categoria == "ASCENSORES"
        assert res_asc.es_emergencia is True

        # 4.2 Desborde cloacal / Inundación grave
        res_cloaca = semantic_extractor.extract(
            "Se desbordo la cloaca y esta entrando agua sucia a borbotones a la cocina",
            CONSORCIOS_MOCK,
        )
        assert res_cloaca.categoria == "PLOMERIA"
        assert res_cloaca.es_emergencia is True

        # 4.3 Cortocircuito / Fuego
        res_fuego = semantic_extractor.extract(
            "Hay chispazos y olor a plastico quemado en los cables del pasillo",
            CONSORCIOS_MOCK,
        )
        assert res_fuego.categoria == "ELECTRICIDAD"
        assert res_fuego.es_emergencia is True

    def test_non_emergency_routine_incident(self):
        """Caso 5: Reclamos normales que NO deben marcarse como emergencia."""
        res_luz = semantic_extractor.extract(
            "Se quemo la lamparita del palier del piso 3, cuando puedan cambienla",
            CONSORCIOS_MOCK,
        )
        assert res_luz.categoria in ("ELECTRICIDAD", "LIMPIEZA_AREAS_COMUNES", "OTRO")
        assert res_luz.es_emergencia is False
