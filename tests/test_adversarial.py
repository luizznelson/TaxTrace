import json
import unittest
from pathlib import Path

from taxtrace.avaliar_adversarial import avaliar


class AdversarialTest(unittest.TestCase):
    def test_bloqueios_e_limites_semanticos_sao_pontuados_separadamente(self):
        path = Path(__file__).resolve().parent.parent / "evals/rag.adversarial.v2.json"
        r = avaliar(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(r["chamadas_de_modelo"], 0)
        self.assertEqual(r["resumo"]["bloqueios_esperados"], 10)
        self.assertEqual(r["resumo"]["bloqueios_corretos"], 10)
        self.assertEqual(r["resumo"]["controles_semanticos_nao_cobertos"], 2)
        self.assertTrue(all(c["comportamento_estrutural_esperado"] for c in r["casos"]))
