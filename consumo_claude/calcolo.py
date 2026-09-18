"""Dai dati letti alle misure: token, dollari, lavoro umano equivalente.

L'unita' di base e' la "cella": una sessione in un giorno. Tutti i riepiloghi
(per progetto, per sessione, per periodo) sono somme di celle, sia qui sia
nella pagina HTML, che rifa' gli stessi conti quando si cambia periodo.
"""

import fnmatch
import json
import os
import re
from datetime import datetime
from pathlib import Path

DATI = Path(__file__).parent / "dati"

# Posizioni nei vettori numerici di una cella (usate anche dalla pagina HTML).
CAMPI = ["letti", "scritti", "cache_scritti", "cache_riletti", "pensiero",
         "costo", "ore_a", "ore_b", "minuti", "risposte", "azioni"]
LETTI, SCRITTI, CACHE_SCRITTI, CACHE_RILETTI, PENSIERO, COSTO, ORE_A, ORE_B, \
    MINUTI, RISPOSTE, AZIONI = range(len(CAMPI))


def _unisci(base, sopra):
    for k, v in sopra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _unisci(base[k], v)
        else:
            base[k] = v
    return base


def cartella_impostazioni():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "consumo-claude"


def carica_json(nome):
    """File dei dati del programma, con sopra le modifiche dell'utente se ci sono."""
    with open(DATI / nome, encoding="utf-8") as f:
        dati = json.load(f)
    personale = cartella_impostazioni() / nome
    if personale.is_file():
        with open(personale, encoding="utf-8") as f:
            _unisci(dati, json.load(f))
    return dati


def nome_modello(modello):
    """Riporta i nomi dei modelli alla forma del listino.

    claude-haiku-4-5-20251001 -> claude-haiku-4-5, claude-opus-5[1m] ->
    claude-opus-5, us.anthropic.claude-opus-4-8-v1:0 -> claude-opus-4-8.
    """
    m = modello.lower().strip()
    m = re.sub(r"\[.*?\]$", "", m)
    m = m.split(".")[-1] if "anthropic." in m else m
    m = re.sub(r"-v\d+(:\d+)?$", "", m)
    m = re.sub(r"@\d{8}$", "", m)
    m = re.sub(r"-\d{8}$", "", m)
    return m


class Prezzi:
    def __init__(self, listino):
        self.listino = listino

    def tariffa(self, modello, veloce):
        nome = nome_modello(modello)
        if veloce and nome in self.listino.get("modalita_veloce", {}):
            return self.listino["modalita_veloce"][nome]
        return self.listino["modelli"].get(nome)

    def costo(self, r):
        """Dollari di una risposta, o None se il modello non e' nel listino."""
        _, _, _, modello, veloce, geo, letti, scritti, c5m, c1h, riletti, _, ricerche = r
        t = self.tariffa(modello, veloce)
        if t is None:
            return None
        dollari = (letti * t["letti"] + scritti * t["scritti"] + c5m * t["cache_5m"]
                   + c1h * t["cache_1h"] + riletti * t["riletti"]) / 1e6
        if geo == "us":
            dollari *= self.listino.get("moltiplicatore_solo_usa", 1)
        return dollari + ricerche * self.listino.get("ricerca_web_per_mille", 0) / 1000


class Stima:
    """Ore di lavoro umano di un blocco, con i due metodi della specifica."""

    def __init__(self, imp):
        self.righe_ora = imp["metodo_a_volume"]["righe_codice_ora"]
        self.parole_ora = imp["metodo_a_volume"]["parole_testo_ora"]
        self.minuti = imp["metodo_b_minuti_per_azione"]
        self.strumenti = imp["strumenti"]
        self.testo = set(imp["estensioni_testo"])
        self._categorie = {}

    def categoria(self, strumento):
        if strumento not in self._categorie:
            cat = self.strumenti.get(strumento)
            if cat is None:
                for schema, c in self.strumenti.items():
                    if "*" in schema and fnmatch.fnmatchcase(strumento, schema):
                        cat = c
                        break
            self._categorie[strumento] = cat
        return self._categorie[strumento]

    def ore(self, b):
        """(ore metodo A, ore metodo B, e' un'azione) per un blocco."""
        _, _, _, strumento, estensione, righe, parole = b
        if strumento == "":
            return parole / self.parole_ora, 0.0, False
        cat = self.categoria(strumento)
        ore_b = self.minuti.get(cat, 0) / 60 if cat else 0.0
        if righe or parole:
            if estensione in self.testo:
                ore_a = parole / self.parole_ora
            else:
                ore_a = righe / self.righe_ora
        else:
            ore_a = 0.0
        return ore_a, ore_b, True


def _giorno(secondi):
    return datetime.fromtimestamp(secondi).strftime("%Y-%m-%d")


def _nome_progetto(percorso):
    casa = str(Path.home())
    if percorso == casa:
        return "~"
    return os.path.basename(percorso.rstrip("/\\")) or percorso


def _progetto_da_cartella(file_percorso, radice):
    """Ripiego quando manca il campo cwd: il nome della cartella delle cronologie."""
    try:
        rel = Path(file_percorso).relative_to(radice)
        return rel.parts[0]
    except ValueError:
        return "?"


def calcola(file_letti, radice, prezzi, imp):
    """Costruisce il rapporto: progetti, sessioni, celle e avvisi."""
    stima = Stima(imp)
    pausa = imp["pausa_massima_minuti"] * 60

    celle = {}        # (sessione, giorno) -> vettore numerico
    modelli = {}      # (sessione, giorno, modello) -> [token, costo]
    ignoti = {}       # (sessione, giorno, modello) -> token senza prezzo
    momenti = {}      # sessione -> set di secondi
    info = {}         # sessione -> dati descrittivi
    estremi = {}      # sessione -> [prima, ultima] risposta o azione contata
    viste_risposte, visti_blocchi = set(), set()
    illeggibili = 0

    def cella(sid, sec):
        e = estremi.setdefault(sid, [sec, sec])
        e[0], e[1] = min(e[0], sec), max(e[1], sec)
        k = (sid, _giorno(sec))
        if k not in celle:
            celle[k] = [0] * len(CAMPI)
        return celle[k]

    # La stessa risposta compare su piu' righe: la prima porta un conteggio
    # provvisorio dei token scritti, le successive quello definitivo. Si tiene
    # il piu' alto, attribuito alla sessione e all'ora della prima comparsa.
    definitive = {}
    for _, dati in file_letti:
        for r in dati["risposte"]:
            if r[2] is None:
                continue
            gia = definitive.get(r[0])
            if gia is None:
                definitive[r[0]] = list(r)
            elif r[7] > gia[7]:
                definitive[r[0]] = gia[:3] + list(r[3:])

    for percorso, dati in file_letti:
        illeggibili += dati["illeggibili"]
        for sid, s in dati["sessioni"].items():
            i = info.setdefault(sid, {})
            for campo in ("titolo", "titolo_ai", "cwd"):
                if s.get(campo) and campo not in i:
                    i[campo] = s[campo]
            if "cartella" not in i and "subagents" not in Path(percorso).relative_to(radice).parts:
                i["cartella"] = _progetto_da_cartella(percorso, radice)
        for sid, sec in dati["momenti"]:
            momenti.setdefault(sid, set()).add(sec)
        for r in dati["risposte"]:
            if r[0] in viste_risposte or r[2] is None:
                continue
            viste_risposte.add(r[0])
            r = definitive[r[0]]
            c = cella(r[1], r[2])
            c[LETTI] += r[6]
            c[SCRITTI] += r[7]
            c[CACHE_SCRITTI] += r[8] + r[9]
            c[CACHE_RILETTI] += r[10]
            c[PENSIERO] += r[11]
            c[RISPOSTE] += 1
            dollari = prezzi.costo(r)
            token = r[6] + r[7] + r[8] + r[9] + r[10]
            modello = nome_modello(r[3])
            if dollari is None:
                ki = (r[1], _giorno(r[2]), modello)
                ignoti[ki] = ignoti.get(ki, 0) + token
                dollari = 0.0
            c[COSTO] += dollari
            km = (r[1], _giorno(r[2]), modello)
            voce = modelli.setdefault(km, [0, 0.0])
            voce[0] += token
            voce[1] += dollari
        for b in dati["blocchi"]:
            if b[0] in visti_blocchi or b[2] is None:
                continue
            visti_blocchi.add(b[0])
            ore_a, ore_b, azione = stima.ore(b)
            c = cella(b[1], b[2])
            c[ORE_A] += ore_a
            c[ORE_B] += ore_b
            if azione:
                c[AZIONI] += 1

    # Durata attiva: intervalli fra messaggi consecutivi, senza le pause lunghe.
    # Un intervallo va al giorno in cui finisce, o a quello in cui comincia se
    # nel giorno dopo non c'e' stata attivita': un messaggio dopo mezzanotte
    # non deve creare un giorno di lavoro fatto di soli minuti.
    for sid, tempi in momenti.items():
        ordinati = sorted(tempi)
        for prima, dopo in zip(ordinati, ordinati[1:]):
            if dopo - prima > pausa:
                continue
            k = (sid, _giorno(dopo))
            if k not in celle:
                k = (sid, _giorno(prima))
            if k in celle:
                celle[k][MINUTI] += (dopo - prima) / 60
                e = estremi[sid]
                e[0], e[1] = min(e[0], prima), max(e[1], dopo)

    # Solo le sessioni con almeno una risposta del modello.
    attive = {sid for (sid, _), v in celle.items() if v[RISPOSTE] or v[AZIONI]}
    progetti, sessioni = {}, {}
    for sid in sorted(attive):
        i = info.get(sid, {})
        percorso = i.get("cwd") or i.get("cartella") or "?"
        if percorso not in progetti:
            progetti[percorso] = {"nome": _nome_progetto(percorso), "percorso": percorso}
        # Inizio e fine dalle risposte contate, non da tutte le righe: una
        # sessione ripresa ricopia righe vecchie con la loro data.
        inizio, fine = estremi[sid]
        sessioni[sid] = {
            "progetto": percorso,
            "titolo": i.get("titolo") or i.get("titolo_ai") or "",
            "inizio": inizio,
            "fine": fine,
        }
    # Nomi uguali per progetti diversi: si aggiunge la cartella superiore.
    per_nome = {}
    for p in progetti.values():
        per_nome.setdefault(p["nome"], []).append(p)
    for uguali in per_nome.values():
        if len(uguali) > 1:
            for p in uguali:
                p["nome"] = os.path.join(os.path.basename(os.path.dirname(p["percorso"])), p["nome"])

    return {
        "progetti": progetti,
        "sessioni": sessioni,
        "celle": [[sid, g] + [round(x, 6) for x in v]
                  for (sid, g), v in sorted(celle.items()) if sid in attive],
        "modelli": [[sid, g, m, t, round(d, 6)]
                    for (sid, g, m), (t, d) in sorted(modelli.items()) if sid in attive],
        "ignoti": [[sid, g, m, t] for (sid, g, m), t in sorted(ignoti.items()) if sid in attive],
        "illeggibili": illeggibili,
    }


def riepiloga(celle, ore_giornata):
    """Somma un gruppo di celle e ne ricava ore, giorni e persone."""
    tot = [0.0] * len(CAMPI)
    giorni = set()
    for c in celle:
        giorni.add(c[1])
        for i, v in enumerate(c[2:]):
            tot[i] += v
    ore = (tot[ORE_A] + tot[ORE_B]) / 2
    return {
        "v": tot,
        "token": tot[LETTI] + tot[SCRITTI] + tot[CACHE_SCRITTI] + tot[CACHE_RILETTI],
        "ore": ore,
        "giorni_persona": ore / ore_giornata,
        "giorni_attivi": len(giorni),
    }


def persone_sessione(r):
    """Persone per finire nello stesso tempo attivo della sessione."""
    return r["ore"] / (r["v"][MINUTI] / 60) if r["v"][MINUTI] >= 1 else None


def persone_gruppo(r):
    """Persone per finire negli stessi giorni in cui si e' lavorato."""
    return r["giorni_persona"] / r["giorni_attivi"] if r["giorni_attivi"] else None
