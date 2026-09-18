"""Collaudo su cronologie finte con risultati calcolati a mano.

Si lancia dalla cartella del progetto:  python3 -m unittest discover tests
"""

import io
import json
import os
import shutil
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

os.environ["TZ"] = "UTC"
if hasattr(time, "tzset"):
    time.tzset()

from consumo_claude import calcolo, lettura, listino  # noqa: E402
from consumo_claude.__main__ import main, periodo  # noqa: E402


def utente(sid, ts, testo, cwd="/progetti/alfa"):
    return {"type": "user", "sessionId": sid, "timestamp": ts, "cwd": cwd,
            "message": {"role": "user", "content": testo}}


def risposta(sid, ts, mid, modello, usage, contenuto, cwd="/progetti/alfa"):
    return {"type": "assistant", "sessionId": sid, "timestamp": ts, "cwd": cwd,
            "requestId": "req-" + mid,
            "message": {"id": mid, "model": modello, "usage": usage, "content": contenuto}}


def uso(letti=0, scritti=0, c5m=0, c1h=0, riletti=0, veloce=False):
    return {"input_tokens": letti, "output_tokens": scritti,
            "cache_creation_input_tokens": c5m + c1h,
            "cache_creation": {"ephemeral_5m_input_tokens": c5m, "ephemeral_1h_input_tokens": c1h},
            "cache_read_input_tokens": riletti, "speed": "fast" if veloce else "standard"}


S1, S2 = "sessione-uno", "sessione-due"

# m1 compare due volte: la prima riga ha il conteggio provvisorio (2 token scritti).
M1_PROVVISORIA = risposta(S1, "2026-09-10T10:00:05Z", "m1", "claude-opus-5",
                          uso(letti=10, scritti=2, c5m=1000),
                          [{"type": "text", "text": "Ecco il file"}])
M1_DEFINITIVA = risposta(S1, "2026-09-10T10:00:06Z", "m1", "claude-opus-5",
                         uso(letti=10, scritti=400, c5m=1000),
                         [{"type": "tool_use", "id": "tu1", "name": "Write",
                           "input": {"file_path": "/x/app.py", "content": "a\nb\n\nc"}}])

FILE_PRINCIPALE = [
    utente(S1, "2026-09-10T10:00:00Z", "ciao"),
    M1_PROVVISORIA,
    M1_DEFINITIVA,
    utente(S1, "2026-09-10T10:01:00Z", [{"type": "tool_result", "content": "ok"}]),
    risposta(S1, "2026-09-10T10:02:00Z", "m2", "claude-opus-5",
             uso(letti=5, scritti=100, c1h=2000, riletti=50000, veloce=True),
             [{"type": "tool_use", "id": "tu2", "name": "Read", "input": {"file_path": "/x/a"}}]),
    '{"type":"assistant","sessionId":"sessione-uno","message":{"id":"tronca',
    {"type": "ai-title", "aiTitle": "Prova alfa", "sessionId": S1},
    risposta(S1, "2026-09-10T10:04:00Z", "m4", "claude-futuro-9", uso(letti=100, scritti=100), []),
    risposta(S1, "2026-09-10T10:04:30Z", "err", "<synthetic>", uso(letti=999, scritti=999), []),
]

SOTTO_AGENTE = [
    risposta(S1, "2026-09-10T10:03:00Z", "m3", "claude-sonnet-5", uso(letti=1000, scritti=1000),
             [{"type": "tool_use", "id": "tu3", "name": "Bash", "input": {"command": "ls"}}],
             cwd="/altrove"),
]

# Sessione ripresa: ricopia m1 (va contata una volta sola, nella sessione uno).
RIPRESA = [
    utente(S2, "2026-09-11T09:00:00Z", "riprendo"),
    dict(M1_DEFINITIVA, sessionId=S2),
    risposta(S2, "2026-09-11T09:01:00Z", "m5", "claude-haiku-4-5-20251001", uso(letti=1000000), []),
]


def scrivi(percorso, righe):
    percorso.parent.mkdir(parents=True, exist_ok=True)
    with open(percorso, "w", encoding="utf-8") as f:
        for r in righe:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        os.environ["XDG_CACHE_HOME"] = str(self.tmp / "cache")
        os.environ["XDG_CONFIG_HOME"] = str(self.tmp / "config")
        self.radice = self.tmp / "projects"
        cartella = self.radice / "-progetti-alfa"
        scrivi(cartella / (S1 + ".jsonl"), FILE_PRINCIPALE)
        scrivi(cartella / S1 / "subagents" / "agent-a.jsonl", SOTTO_AGENTE)
        scrivi(cartella / (S2 + ".jsonl"), RIPRESA)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rapporto(self, archivio=False):
        file_letti = lettura.carica(self.radice, usa_archivio=archivio)
        imp = calcolo.carica_json("impostazioni.json")
        prezzi = calcolo.Prezzi(calcolo.carica_json("prezzi.json"))
        return calcolo.calcola(file_letti, self.radice, prezzi, imp), imp

    def per_sessione(self, rapporto, sid):
        return calcolo.riepiloga([c for c in rapporto["celle"] if c[0] == sid], 8)


class Conti(Base):
    def test_token_esatti(self):
        r, _ = self.rapporto()
        v = self.per_sessione(r, S1)["v"]
        self.assertEqual(v[calcolo.LETTI], 10 + 5 + 1000 + 100)
        self.assertEqual(v[calcolo.SCRITTI], 400 + 100 + 1000 + 100)
        self.assertEqual(v[calcolo.CACHE_SCRITTI], 1000 + 2000)
        self.assertEqual(v[calcolo.CACHE_RILETTI], 50000)
        self.assertEqual(v[calcolo.RISPOSTE], 4)

    def test_dollari_esatti(self):
        r, _ = self.rapporto()
        # m1 opus-5: 10*5 + 400*25 + 1000*6.25            = 16.300
        # m2 veloce: 5*10 + 100*50 + 2000*20 + 50000*1   = 95.050
        # m3 sonnet-5 (sotto-agente): 1000*2 + 1000*10    = 12.000
        self.assertAlmostEqual(self.per_sessione(r, S1)["v"][calcolo.COSTO], 0.12335, places=9)
        # m5 haiku: un milione di token letti = 1 dollaro
        self.assertAlmostEqual(self.per_sessione(r, S2)["v"][calcolo.COSTO], 1.0, places=9)

    def test_nessun_doppio_conteggio(self):
        r, _ = self.rapporto()
        tutte = calcolo.riepiloga(r["celle"], 8)["v"]
        self.assertEqual(tutte[calcolo.RISPOSTE], 5)
        self.assertEqual(tutte[calcolo.SCRITTI], 1600)

    def test_sotto_agente_nella_sessione_madre(self):
        r, _ = self.rapporto()
        self.assertEqual(set(r["sessioni"]), {S1, S2})
        self.assertEqual(r["sessioni"][S1]["progetto"], "/progetti/alfa")

    def test_modello_sconosciuto_segnalato(self):
        r, _ = self.rapporto()
        self.assertEqual(r["ignoti"], [[S1, "2026-09-10", "claude-futuro-9", 200]])

    def test_riga_rotta_contata(self):
        r, _ = self.rapporto()
        self.assertEqual(r["illeggibili"], 1)

    def test_titoli_e_progetto(self):
        r, _ = self.rapporto()
        self.assertEqual(r["sessioni"][S1]["titolo"], "Prova alfa")
        # Senza titolo resta vuoto: il testo dei messaggi non entra mai nel rapporto.
        self.assertEqual(r["sessioni"][S2]["titolo"], "")
        self.assertNotIn("riprendo", json.dumps(r))
        self.assertNotIn("ciao", json.dumps(r))
        self.assertEqual(list(r["progetti"].values()), [{"nome": "alfa", "percorso": "/progetti/alfa"}])

    def test_lavoro_umano(self):
        r, _ = self.rapporto()
        s = self.per_sessione(r, S1)
        ore_a = 3 / 500 + 3 / 30                 # testo di 3 parole, file di 3 righe
        ore_b = 15 / 60 + 3 / 60 + 5 / 60        # creare, leggere, comando
        self.assertAlmostEqual(s["ore"], (ore_a + ore_b) / 2, places=6)
        # da 10:00:00 a 10:04:30 (anche il messaggio d'errore e' tempo di sessione)
        self.assertAlmostEqual(s["v"][calcolo.MINUTI], 4.5, places=6)
        self.assertAlmostEqual(calcolo.persone_sessione(s), s["ore"] / (4.5 / 60), places=6)

    def test_mezzanotte_non_crea_giorni_vuoti(self):
        scrivi(self.radice / "-progetti-alfa" / "notte.jsonl", [
            utente("notte", "2026-09-10T23:40:00Z", "domanda"),
            risposta("notte", "2026-09-10T23:51:00Z", "n1", "claude-opus-5", uso(letti=10), []),
            utente("notte", "2026-09-11T00:10:00Z", "altra domanda senza risposta"),
        ])
        r, _ = self.rapporto()
        giorni = [c[1] for c in r["celle"] if c[0] == "notte"]
        self.assertEqual(giorni, ["2026-09-10"])
        self.assertAlmostEqual(self.per_sessione(r, "notte")["v"][calcolo.MINUTI], 30.0, places=6)

    def test_campi_di_tipo_strano(self):
        scrivi(self.radice / "-progetti-alfa" / "strana.jsonl", [
            {"type": "assistant", "sessionId": "strana", "timestamp": 123, "cwd": ["x"],
             "message": {"id": "s1", "model": "claude-opus-5", "content": "testo",
                         "usage": {"input_tokens": "tanti", "cache_creation": []}}},
            risposta("strana", "2026-09-12T10:00:00Z", "s2", "claude-opus-5", uso(letti=7), [5, None]),
        ])
        r, _ = self.rapporto()
        self.assertEqual(self.per_sessione(r, "strana")["v"][calcolo.LETTI], 7)

    def test_cartella_sotto_una_directory_subagents(self):
        nuova = self.tmp / "subagents" / "projects"
        shutil.copytree(self.radice, nuova)
        file_letti = lettura.carica(nuova, usa_archivio=False)
        imp = calcolo.carica_json("impostazioni.json")
        r = calcolo.calcola(file_letti, nuova, calcolo.Prezzi(calcolo.carica_json("prezzi.json")), imp)
        self.assertEqual(r["sessioni"][S1]["progetto"], "/progetti/alfa")

    def test_archivio_si_ripulisce(self):
        self.rapporto(archivio=True)
        (self.radice / "-progetti-alfa" / (S2 + ".jsonl")).unlink()
        self.rapporto(archivio=True)
        archiviati = list((lettura.cartella_archivio() / "file").rglob("*.json"))
        self.assertEqual(len(archiviati), 2)

    def test_archivio_da_lo_stesso_risultato(self):
        senza, _ = self.rapporto(archivio=False)
        self.rapporto(archivio=True)
        con, _ = self.rapporto(archivio=True)
        self.assertEqual(senza["celle"], con["celle"])


class Programma(Base):
    def lancia(self, *argomenti):
        uscita = io.StringIO()
        with redirect_stdout(uscita):
            codice = main(["--cartella", str(self.radice), "--offline", "--non-aprire",
                           "--pagina", str(self.tmp / "p.html")] + list(argomenti))
        return codice, uscita.getvalue()

    def test_terminale_e_pagina(self):
        codice, testo = self.lancia("--lingua", "it")
        self.assertEqual(codice, 0)
        self.assertIn("alfa", testo)
        self.assertIn("claude-futuro-9", testo)
        self.assertIn("Horizon Peak", testo)
        html = (self.tmp / "p.html").read_text(encoding="utf-8")
        self.assertIn("Prova alfa", html)
        self.assertNotIn("__DATI__", html)

    def test_inglese(self):
        codice, testo = self.lancia("--lingua", "en")
        self.assertEqual(codice, 0)
        self.assertIn("Project", testo)

    def test_sessione_per_id(self):
        codice, testo = self.lancia("sessione", "--sessione-id", S2, "--lingua", "it")
        self.assertEqual(codice, 0)
        self.assertIn("(senza titolo)", testo)
        self.assertIn("2026-09-11 09:00", testo)      # non la data della riga ricopiata
        self.assertIn("claude-haiku-4-5", testo)

    def test_sessione_inesistente(self):
        codice, _ = self.lancia("sessione", "--sessione-id", "refuso", "--lingua", "it")
        self.assertEqual(codice, 1)

    def test_json_rispetta_il_periodo(self):
        codice, testo = self.lancia("2026-09-11", "--json")
        dati = json.loads(testo)
        self.assertEqual({c[1] for c in dati["celle"]}, {"2026-09-11"})
        self.assertEqual(dati["campi_celle"][:3], ["sessione", "giorno", "letti"])
        self.assertEqual(list(dati["sessioni"]), [S2])

    def test_pagina_resiste_ai_titoli_strani(self):
        scrivi(self.radice / "-progetti-alfa" / (S1 + ".jsonl"), FILE_PRINCIPALE + [
            {"type": "custom-title", "customTitle": "guarda <!--<script> e </script> $& qui", "sessionId": S1}])
        self.lancia("--lingua", "it")
        html = (self.tmp / "p.html").read_text(encoding="utf-8")
        blocco = html.split('<script type="application/json" id="dati">')[1].split("</script>")[0]
        self.assertNotIn("<", blocco)
        self.assertEqual(json.loads(blocco)["sessioni"][S1]["titolo"], "guarda <!--<script> e </script> $& qui")

    def test_progetto_da_sottocartella(self):
        os.environ["CLAUDE_PROJECT_DIR"] = "/progetti/alfa/src"
        try:
            codice, testo = self.lancia("progetto", "--lingua", "it")
        finally:
            del os.environ["CLAUDE_PROJECT_DIR"]
        self.assertEqual(codice, 0)
        self.assertIn("Prova alfa", testo)

    def test_cartella_senza_sessioni(self):
        os.environ["CLAUDE_PROJECT_DIR"] = "/progetti/beta"
        try:
            codice, _ = self.lancia("progetto", "--lingua", "it")
        finally:
            del os.environ["CLAUDE_PROJECT_DIR"]
        self.assertEqual(codice, 1)

    def test_settimana_scorsa_in_due_parole(self):
        codice, _ = self.lancia("settimana", "scorsa", "--lingua", "it")
        self.assertEqual(codice, 0)

    def test_periodo_vuoto(self):
        codice, testo = self.lancia("2025-01", "--lingua", "it")
        self.assertEqual(codice, 0)
        self.assertIn("Nessuna sessione", testo)


class Listino(Base):
    def test_senza_internet_usa_quello_del_programma(self):
        prezzi, fonte = listino.carica(in_linea=False)
        self.assertEqual(fonte, "programma")
        self.assertEqual(prezzi["modelli"]["claude-opus-5"]["letti"], 5)

    def test_scartato_se_rovinato(self):
        buono, _ = listino.carica(in_linea=False)
        self.assertTrue(listino._valido(buono))
        self.assertFalse(listino._valido({"verificati_il": "2099-01-01", "modelli": {"x": {"letti": "gratis"}}}))
        self.assertFalse(listino._valido({"modelli": {}}))

    def test_usa_quello_scaricato_se_piu_recente(self):
        nuovo, _ = listino.carica(in_linea=False)
        nuovo = json.loads(json.dumps(nuovo))
        nuovo["verificati_il"] = "2099-01-01"
        nuovo["modelli"]["claude-opus-5"]["letti"] = 4
        archivio = lettura.cartella_archivio() / "prezzi-aggiornati.json"
        archivio.parent.mkdir(parents=True, exist_ok=True)
        archivio.write_text(json.dumps({"preso": time.time(), "listino": nuovo}))
        prezzi, fonte = listino.carica(in_linea=False)
        self.assertEqual((fonte, prezzi["modelli"]["claude-opus-5"]["letti"]), ("aggiornato", 4))


class Piccoli(unittest.TestCase):
    def test_nomi_modello(self):
        n = calcolo.nome_modello
        self.assertEqual(n("claude-haiku-4-5-20251001"), "claude-haiku-4-5")
        self.assertEqual(n("claude-opus-5[1m]"), "claude-opus-5")
        self.assertEqual(n("us.anthropic.claude-opus-4-8-v1:0"), "claude-opus-4-8")
        self.assertEqual(n("claude-opus-4-20250514"), "claude-opus-4")

    def test_periodi(self):
        oggi = date(2026, 9, 18)
        self.assertEqual(periodo("7g", oggi), ("2026-09-12", "2026-09-18"))
        self.assertEqual(periodo("30d", oggi), ("2026-08-20", "2026-09-18"))
        self.assertEqual(periodo("mese", oggi), ("2026-09-01", "2026-09-18"))
        self.assertEqual(periodo("2026-02", oggi), ("2026-02-01", "2026-02-28"))
        self.assertEqual(periodo("2026-12", oggi), ("2026-12-01", "2026-12-31"))
        self.assertEqual(periodo("2026-09-01..2026-09-05", oggi), ("2026-09-01", "2026-09-05"))
        self.assertEqual(periodo("tutto", oggi), (None, None))
        # 18/09/2026 e' un venerdi'
        self.assertEqual(periodo("oggi", oggi), ("2026-09-18", "2026-09-18"))
        self.assertEqual(periodo("ieri", oggi), ("2026-09-17", "2026-09-17"))
        self.assertEqual(periodo("settimana", oggi), ("2026-09-14", "2026-09-18"))
        self.assertEqual(periodo("settimana-scorsa", oggi), ("2026-09-07", "2026-09-13"))
        self.assertEqual(periodo("mese-scorso", oggi), ("2026-08-01", "2026-08-31"))
        self.assertEqual(periodo("mese-scorso", date(2026, 1, 10)), ("2025-12-01", "2025-12-31"))
        self.assertEqual(periodo("anno", oggi), ("2026-01-01", "2026-09-18"))
        self.assertEqual(periodo("yesterday", oggi), ("2026-09-17", "2026-09-17"))
        for sbagliato in ("domani", "0g", "2026-02-30", "2026-13", "2026-09-15..2026-09-01"):
            with self.assertRaises(ValueError):
                periodo(sbagliato, oggi)


if __name__ == "__main__":
    unittest.main()
