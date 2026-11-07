import copy
import unittest

from taxtrace.revisao_avaliacao import CRITERIOS, conferir, exportar


def execucao():
    return {
        "casos": [
            {
                "id": "caso-1",
                "pergunta": "Pergunta pública de teste",
                "estado": {"rag": {"status": "respondida", "afirmacoes": []}},
            }
        ]
    }


class PacoteTest(unittest.TestCase):
    def test_exportacao_nao_inventa_revisor_nem_aprovacao(self):
        e = execucao()
        p = exportar(e)
        r = conferir(p, e)
        self.assertIsNone(p["revisor"])
        self.assertEqual(r["casos_completos"], 0)
        self.assertEqual(r["casos_pendentes"], 1)
        self.assertFalse(r["independencia_comprovada"])

    def completo(self):
        e = execucao()
        p = exportar(e)
        p["revisor"] = {
            "nome": "Revisor sintético",
            "qualificacao_declarada": "Fixture automatizada, sem revisão fiscal",
            "origem": "teste_automatizado",
        }
        p["casos"][0]["notas"] = dict.fromkeys(CRITERIOS, "atende")
        return e, p

    def test_preenchimento_sintetico_nunca_comprova_revisao_independente(self):
        e, p = self.completo()
        r = conferir(p, e)
        self.assertEqual(r["casos_completos"], 1)
        self.assertFalse(r["revisao_especializada_comprovada"])
        self.assertFalse(r["publicacao_autorizada_automaticamente"])

    def test_outra_execucao_e_material_trocado_sao_recusados(self):
        e, p = self.completo()
        outro = copy.deepcopy(e)
        outro["casos"][0]["pergunta"] = "Outra pergunta"
        with self.assertRaisesRegex(ValueError, "outra_execucao"):
            conferir(p, outro)
        p["casos"][0]["material"]["pergunta"] = "Pergunta adulterada"
        with self.assertRaisesRegex(ValueError, "material_da_revisao_alterado"):
            conferir(p, e)

    def test_casos_duplicados_nao_podem_substituir_casos_pendentes(self):
        e = execucao()
        e["casos"].append({**copy.deepcopy(e["casos"][0]), "id": "caso-2"})
        p = exportar(e)
        p["casos"][1] = copy.deepcopy(p["casos"][0])
        with self.assertRaisesRegex(ValueError, "duplicado"):
            conferir(p, e)

    def test_reprovacao_exige_justificativa_e_notas_invalidas_falham(self):
        e, p = self.completo()
        p["casos"][0]["notas"][CRITERIOS[0]] = "nao_atende"
        with self.assertRaisesRegex(ValueError, "justificativa"):
            conferir(p, e)
        p["casos"][0]["observacoes"] = "A resposta omite condicionantes."
        self.assertEqual(conferir(p, e)["casos_com_reprovacao"], ["caso-1"])
        p["casos"][0]["notas"][CRITERIOS[0]] = True
        with self.assertRaisesRegex(ValueError, "rubrica"):
            conferir(p, e)

    def test_tudo_nao_aplicavel_nao_e_avaliacao_concluida(self):
        e, p = self.completo()
        p["casos"][0]["notas"] = dict.fromkeys(CRITERIOS, "nao_aplicavel")
        self.assertEqual(conferir(p, e)["casos_completos"], 0)
