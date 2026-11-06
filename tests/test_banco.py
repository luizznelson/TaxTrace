import os
import tempfile
import unittest
from pathlib import Path

from test_tabelas import atualizar_manifesto, montar

from taxtrace import banco, busca, conexao, lei, ligacao


class LinhasTest(unittest.TestCase):
    def test_artigos_e_alteracoes(self):
        artigos = lei.ler_artigos(
            "<p>Art. 1º Texto. (Redação dada pela Lei Complementar nº 235, de 2026)</p>".encode()
        )
        self.assertEqual([r[0] for r in banco.linhas_artigos(artigos)], ["1"])
        self.assertEqual(
            banco.linhas_alteracoes(artigos)[0][2:5], ("redacao", "Lei Complementar nº 235", 2026)
        )

    def test_ligacoes_e_divergencias(self):
        ligs = [ligacao.Ligacao("200001", "Arts. 1 e 9", ("1",), ("9",), False)]
        self.assertEqual(banco.linhas_ligacoes(ligs), [("200001", "1")])
        t = type("T", (), {"divergencias": ("x: erro",)})()
        self.assertIn("art. 9", banco.linhas_divergencias(t, ligs)[1][1])


@unittest.skipUnless(os.environ.get("TAXTRACE_TEST_DATABASE") == "1", "PostgreSQL isolado opt-in")
class PostgresTest(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        montar(self.pasta)
        (self.pasta / "lc214_planalto.html").write_text(
            "<p>Art. 1º Tributo sobre operações.</p>"
            "<p>Art. 138. <s>abacaxiantigo</s> Crédito presumido de exemplo.</p>",
            encoding="utf-8",
        )
        atualizar_manifesto(self.pasta)
        self.conn = conexao.conectar(Path.cwd(), teste=True)
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        banco.criar_esquema(self.conn)
        banco.preparar_leitor(self.conn, "isolated-test-only")

    def test_carga_completa_duplicada_e_proveniencia(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        linha = self.conn.execute(
            "SELECT manifesto_sha256,fontes FROM coletas WHERE id=%s", (cid,)
        ).fetchone()
        self.assertEqual(len(linha[0]), 64)
        self.assertEqual(len(linha[1]), 6)
        with self.assertRaises(banco.ColetaJaCarregada):
            banco.carregar_pasta(self.conn, self.pasta)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 1)

    def test_falha_de_integridade_nao_cria_coleta(self):
        with (self.pasta / "lc214_planalto.html").open("ab") as arquivo:
            arquivo.write(b"changed")
        with self.assertRaises(ValueError):
            banco.carregar_pasta(self.conn, self.pasta)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 0)

    def test_erro_no_indice_nao_deixa_carga_parcial(self):
        # Hash correto não basta: falha de processamento deve reverter as inserções.
        (self.pasta / "lc214_planalto.html").write_text(
            "<p>Art. 1º ⟦sem fechamento</p>", encoding="utf-8"
        )
        atualizar_manifesto(self.pasta)
        with self.assertRaises(ValueError):
            banco.carregar_pasta(self.conn, self.pasta)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM artigos").fetchone()[0], 0)

    def test_busca_cita_a_coleta_e_ignora_texto_riscado(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        resultado = busca.pesquisar(self.conn, "crédito presumido", coleta_id=cid)
        self.assertEqual(resultado["status"], "encontrado")
        self.assertEqual(resultado["resultados"][0]["citacao"]["artigo"], "138")
        self.assertEqual(resultado["coleta"]["data_consulta"].isoformat(), "2027-01-01")
        self.assertEqual(
            busca.pesquisar(self.conn, "abacaxiantigo", coleta_id=cid)["status"],
            "sem_evidencia_na_busca_textual",
        )
        self.assertEqual(
            busca.pesquisar(self.conn, "inexistente'; DROP TABLE coletas; --", coleta_id=cid)[
                "resultados"
            ],
            [],
        )
        import psycopg

        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.conn.transaction():
                self.conn.execute("DELETE FROM coletas")

    def test_administrador_nao_e_aceito_pela_busca(self):
        banco.carregar_pasta(self.conn, self.pasta)
        with self.assertRaisesRegex(ValueError, "papel_sem_escrita"):
            busca.pesquisar(self.conn, "tributo")

    def test_v2_acentos_e_texto_decomposto(self):
        with (self.pasta / "lc214_planalto.html").open("a", encoding="utf-8") as arquivo:
            arquivo.write("<p>Art. 139. Cesta básica nacional de alimentos.</p>")
        atualizar_manifesto(self.pasta)
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        for consulta in ("cesta basica", "CESTA BÁSICA", "cesta ba\u0301sica"):
            with self.subTest(consulta=consulta):
                resposta = busca.pesquisar(self.conn, consulta, coleta_id=cid, metodo="v2")
                self.assertEqual(resposta["resultados"][0]["artigo_numero"], "139")
                self.assertEqual(resposta["resultados"][0]["termos_ausentes"], [])
        self.assertEqual(busca.pesquisar(self.conn, "cesta basica")["resultados"], [])

    def test_v2_sinaliza_correspondencia_parcial(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        resposta = busca.pesquisar(
            self.conn, "crédito presumido zzzterm", coleta_id=cid, metodo="v2"
        )
        item = resposta["resultados"][0]
        self.assertTrue(item["correspondencia_parcial"])
        self.assertIn("zzzterm", item["termos_ausentes"])

    def test_v2_sem_termos_e_entrada_parecida_com_sql(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        for consulta in ("Qual artigo?", "zzzinexistente'; DROP TABLE coletas; --"):
            self.assertEqual(
                busca.pesquisar(self.conn, consulta, coleta_id=cid, metodo="v2")["resultados"], []
            )
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 1)

    def test_atualizacao_de_esquema_preserva_carga_e_indice_original(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        antes = self.conn.execute("SELECT numero,texto FROM artigos ORDER BY numero").fetchall()
        banco.criar_esquema(self.conn)
        banco.criar_esquema(self.conn)
        self.assertEqual(
            antes, self.conn.execute("SELECT numero,texto FROM artigos ORDER BY numero").fetchall()
        )
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM documentos_busca WHERE coleta_id=%s "
                "AND termos IS NOT NULL AND termos_v2 IS NOT NULL",
                (cid,),
            ).fetchone()[0],
            2,
        )
