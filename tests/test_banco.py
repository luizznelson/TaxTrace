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
        self.assertEqual(busca.pesquisar(self.conn, "cesta basica", metodo="v1")["resultados"], [])

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

    def test_v3_citacoes_versao_e_consulta_sem_evidencia(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        r = busca.pesquisar(self.conn, "crédito presumido", coleta_id=cid, metodo="v3")
        self.assertEqual(r["coleta"]["id"], cid)
        self.assertEqual(r["resultados"][0]["citacao"]["artigo"], "138")
        self.assertEqual(r["resultados"][0]["posicoes"], {"v1": 1, "v2": 1})
        for consulta in ("zzzinexistente", "zzzinexistente'; DROP TABLE coletas; --"):
            self.assertEqual(busca.pesquisar(self.conn, consulta, metodo="v3")["resultados"], [])
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 1)

    def test_v4_preserva_ranking_original_e_completa_vagas(self):
        cid = banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        original = busca.pesquisar(self.conn, "crédito presumido", coleta_id=cid, metodo="v1")
        conservadora = busca.pesquisar(self.conn, "crédito presumido", coleta_id=cid, metodo="v4")
        self.assertEqual(
            [x["artigo_numero"] for x in original["resultados"]],
            [x["artigo_numero"] for x in conservadora["resultados"]],
        )
        ampliada = busca.pesquisar(self.conn, "credito presumido zzzterm", metodo="v4")
        self.assertEqual(ampliada["resultados"][0]["origem"], "v2")
        self.assertTrue(ampliada["resultados"][0]["correspondencia_parcial"])

    def test_padrao_v4_nao_consulta_v2_quando_nao_ha_vagas(self):
        from unittest.mock import patch

        banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        with patch(
            "taxtrace.busca.buscar_v2", side_effect=AssertionError("consulta desnecessária")
        ):
            r = busca.pesquisar(self.conn, "crédito presumido", limite=1)
        self.assertEqual(r["metodo"], "busca_textual_portugues_v4")
        self.assertEqual(r["resultados"][0]["origem"], "v1")

    def preparar_indice_sintetico(self):
        # Vetores artificiais servem apenas ao teste de persistência, não à qualidade do modelo.
        from taxtrace.vetores import gravar_indice

        cid = banco.carregar_pasta(self.conn, self.pasta)
        manifesto = self.conn.execute(
            "SELECT manifesto_sha256 FROM coletas WHERE id=%s", (cid,)
        ).fetchone()[0]
        artigos = self.conn.execute(
            "SELECT artigo_numero,texto_ativo FROM documentos_busca "
            "WHERE coleta_id=%s ORDER BY artigo_numero",
            (cid,),
        ).fetchall()
        fragmentos = []
        for n, (numero, texto) in enumerate(artigos):
            corte = len(texto) // 2
            for ordem, (inicio, fim) in enumerate(((0, corte), (max(0, corte - 3), len(texto)))):
                fragmentos.append(
                    {
                        "artigo": numero,
                        "ordem": ordem,
                        "inicio": inicio,
                        "fim": fim,
                        "texto": texto[inicio:fim],
                        "vetor": [0] * n + [1] + [0] * (383 - n),
                    }
                )
        indice = gravar_indice(self.conn, cid, manifesto, artigos, fragmentos)
        return cid, manifesto, artigos, fragmentos, indice

    def test_vetores_exatos_deduplicam_artigo_e_leitor_nao_escreve(self):
        import psycopg
        from psycopg.rows import dict_row

        from taxtrace.vetores import buscar_semantica

        cid, _, _, _, indice = self.preparar_indice_sintetico()
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        with self.conn.cursor(row_factory=dict_row) as cur:
            resultados, meta = buscar_semantica(cur, [1] + [0] * 383, cid, 5)
        self.assertEqual(meta["id"], str(indice))
        self.assertEqual([x["artigo_numero"] for x in resultados], ["1", "138"])
        self.assertAlmostEqual(resultados[0]["pontuacao"], 1)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.conn.transaction():
                self.conn.execute("DELETE FROM indices_semanticos")

    def test_indice_duplicado_nao_deixa_fragmentos_parciais(self):
        import psycopg

        from taxtrace.vetores import gravar_indice

        cid, manifesto, artigos, fragmentos, _ = self.preparar_indice_sintetico()
        with self.assertRaises(psycopg.errors.UniqueViolation):
            gravar_indice(self.conn, cid, manifesto, artigos, fragmentos)
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM indices_semanticos").fetchone()[0], 1
        )
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM fragmentos_semanticos").fetchone()[0], 4
        )

    def test_indice_ausente_e_alteracao_de_coleta_nao_viram_busca_vazia(self):
        from psycopg.rows import dict_row

        from taxtrace.vetores import buscar_semantica, gravar_indice

        cid = banco.carregar_pasta(self.conn, self.pasta)
        with self.conn.cursor(row_factory=dict_row) as cur:
            with self.assertRaisesRegex(ValueError, "indice_semantico_ausente"):
                buscar_semantica(cur, [1] + [0] * 383, cid, 5)
        # Um corpus diferente do banco deve ser recusado antes de publicar o índice.
        with self.assertRaisesRegex(ValueError, "coleta_alterada"):
            gravar_indice(
                self.conn,
                cid,
                "hash_incorreto",
                [("1", "abc")],
                [
                    {
                        "artigo": "1",
                        "ordem": 0,
                        "inicio": 0,
                        "fim": 3,
                        "texto": "abc",
                        "vetor": [1] + [0] * 383,
                    }
                ],
            )
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM indices_semanticos").fetchone()[0], 0
        )

    def test_falha_na_gravacao_de_fragmentos_reverte_indice_inteiro(self):
        import psycopg

        self.conn.execute("""CREATE FUNCTION falhar_fragmento_teste() RETURNS trigger
           LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'falha simulada'; END $$""")
        self.conn.execute("""CREATE TRIGGER falha_simulada BEFORE INSERT ON fragmentos_semanticos
           FOR EACH ROW EXECUTE FUNCTION falhar_fragmento_teste()""")
        with self.assertRaises(psycopg.errors.RaiseException):
            self.preparar_indice_sintetico()
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM indices_semanticos").fetchone()[0], 0
        )
        self.assertEqual(
            self.conn.execute("SELECT count(*) FROM fragmentos_semanticos").fetchone()[0], 0
        )
        self.assertEqual(self.conn.execute("SELECT count(*) FROM coletas").fetchone()[0], 1)

    def test_hibrida_combina_e_preserva_citacao_com_encoder_sintetico(self):
        from unittest.mock import MagicMock, patch

        self.preparar_indice_sintetico()
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        encoder = MagicMock()
        encoder.gerar.return_value = [[1] + [0] * 383]
        with patch("taxtrace.busca.encoder_local", return_value=encoder):
            r = busca.pesquisar(self.conn, "crédito presumido", metodo="hibrida")
        self.assertEqual(r["status"], "candidatos_para_revisao")
        self.assertEqual(len({x["artigo_numero"] for x in r["resultados"]}), 2)
        item = next(x for x in r["resultados"] if x["artigo_numero"] == "138")
        self.assertEqual(set(item["posicoes"]), {"textual", "semantica"})
        self.assertEqual(item["citacao"]["artigo"], "138")
        self.assertEqual(item["pontuacao_tipo"], "rrf")

    def test_hibrida_com_indice_ausente_nao_oculta_falha_com_resposta_textual(self):
        from unittest.mock import MagicMock, patch

        banco.carregar_pasta(self.conn, self.pasta)
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        encoder = MagicMock()
        encoder.gerar.return_value = [[1] + [0] * 383]
        with patch("taxtrace.busca.encoder_local", return_value=encoder):
            with self.assertRaisesRegex(ValueError, "indice_semantico_ausente"):
                busca.pesquisar(self.conn, "crédito presumido", metodo="hibrida")
