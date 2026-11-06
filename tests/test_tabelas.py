import hashlib
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from taxtrace import tabelas
from taxtrace.integridade import API


def gravar(pasta: Path, nome: str, dados) -> None:
    (pasta / nome).write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def montar(pasta: Path, erros=None, fundamentos=None):
    gravar(
        pasta,
        "manifesto.json",
        {
            "coletado_em": "2026-11-05T21:00:00+00:00",
            "data_consulta": "2027-01-01",
            "erros": erros or [],
            "arquivos": [],
        },
    )
    gravar(
        pasta,
        "versao.json",
        {
            "versaoApp": "1.6.2",
            "versaoDb": "V0066",
            "descricaoVersaoDb": "teste",
            "dataVersaoDb": "2026-10-28",
            "ambiente": "apr",
        },
    )
    gravar(
        pasta,
        "situacoes_cbs_ibs.json",
        [
            {
                "codigo": "000",
                "descricao": "Tributação integral",
                "classificacoesTributarias": [{"codigo": "000001", "descricao": "Geral"}],
            },
            {
                "codigo": "220",
                "descricao": "Regime especial",
                "classificacoesTributarias": [{"codigo": "220001", "descricao": "Incorporação"}],
            },
        ],
    )
    gravar(
        pasta,
        "classificacoes_cbs_ibs.json",
        [
            {
                "codigo": "000001",
                "descricao": "Geral",
                "descricaoTratamentoTributario": "Tributação integral",
                "tipoAliquota": "Padrão",
                "nomenclatura": "NBS ou NCM",
                "percentualReducaoCbs": 0,
                "percentualReducaoIbsUf": 0,
                "percentualReducaoIbsMun": 0,
                "dataAtualizacao": "2026-10-01",
            },
            {
                "codigo": "200003",
                "descricao": "Redução de 60%",
                "descricaoTratamentoTributario": "Alíquota reduzida",
                "tipoAliquota": "Padrão",
                "nomenclatura": "NCM",
                "percentualReducaoCbs": 60.5,
                "percentualReducaoIbsUf": 60,
                "percentualReducaoIbsMun": 60,
                "dataAtualizacao": "2026-10-01",
            },
        ],
    )
    gravar(
        pasta,
        "fundamentacoes_legais.json",
        fundamentos
        if fundamentos is not None
        else [
            {
                "codigoClassificacaoTributaria": "000001",
                "textoCurto": "LC 214/2025",
                "referenciaNormativa": "LIVRO I \\n\\nDO IBS \\n\\nTÍTULO I",
            },
            {
                "codigoClassificacaoTributaria": "200003",
                "textoCurto": " Art. 138, § 2º ",
                "referenciaNormativa": "LIVRO I",
            },
        ],
    )
    gravar(pasta, "ncm_vigentes.json", [{"ncm": "01012100", "descricao": "-- Reprodutores"}])
    atualizar_manifesto(pasta)


def atualizar_manifesto(pasta):
    arquivo = pasta / "manifesto.json"
    manifesto = json.loads(arquivo.read_bytes())
    entradas = []
    for nome, caminho in {**API, "lc214_planalto": "lc214_planalto.html"}.items():
        if (pasta / caminho).exists():
            bruto = (pasta / caminho).read_bytes()
            entradas.append(
                {
                    "nome": nome,
                    "arquivo": caminho,
                    "url": "https://example.invalid/" + caminho,
                    "bytes": len(bruto),
                    "sha256": hashlib.sha256(bruto).hexdigest(),
                }
            )
    manifesto["arquivos"] = entradas
    arquivo.write_text(json.dumps(manifesto), encoding="utf-8")


class TabelasTest(unittest.TestCase):
    def test_carrega_e_aponta_divergencias(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            montar(pasta)
            t = tabelas.carregar(pasta)

            self.assertEqual((t.versao.base, t.versao.data_base), ("V0066", "2026-10-28"))
            self.assertEqual(t.versao.data_consulta, "2027-01-01")
            self.assertEqual(len(t.classificacoes), 2)
            self.assertEqual(t.ncm["01012100"], "-- Reprodutores")
            geral, reduzida = t.classificacoes
            self.assertEqual(geral.cst, "000")
            self.assertEqual(geral.hierarquia_referencia, "LIVRO I > DO IBS > TÍTULO I")
            self.assertEqual(reduzida.texto_curto, "Art. 138, § 2º")
            self.assertEqual(reduzida.percentual_reducao_cbs, Decimal("60.5"))
            self.assertIn("220001: listada em situações, ausente em classificações", t.divergencias)
            self.assertIn("200003: listada em classificações, ausente em situações", t.divergencias)
            self.assertIn("CST 200 ausente da tabela de situações", " ".join(t.divergencias))

    def test_registra_classificacao_sem_fundamento(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            montar(pasta, fundamentos=[])
            t = tabelas.carregar(pasta)
            self.assertIn("000001: sem fundamento legal", t.divergencias)
            self.assertEqual(t.classificacoes[0].texto_curto, "")

    def test_coleta_incompleta_nao_carrega(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            montar(pasta, erros=[{"nome": "lc214_planalto", "erro": "x"}])
            with self.assertRaisesRegex(ValueError, "lc214_planalto"):
                tabelas.carregar(pasta)

    def test_pasta_mais_recente(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            for nome, com in (("2026-11-01", True), ("2026-11-05", True), ("2026-11-09", False)):
                (raiz / nome).mkdir()
                if com:
                    (raiz / nome / "manifesto.json").write_text("{}", encoding="utf-8")
            self.assertEqual(tabelas.pasta_mais_recente(raiz).name, "2026-11-05")
            with self.assertRaises(FileNotFoundError):
                tabelas.pasta_mais_recente(raiz / "nao-existe")


if __name__ == "__main__":
    unittest.main()
