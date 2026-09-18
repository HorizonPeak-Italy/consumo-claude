"""consumo-claude: token, costo e lavoro umano equivalente di Claude Code.

Uso:  consumo-claude [progetto|sessione] [periodo] [opzioni]
      periodo: oggi, ieri, settimana, settimana scorsa, mese, mese scorso, anno,
               7g, 30g, 2026-09, 2026-09-01..2026-09-15, tutto
"""

import argparse
import json
import os
import re
import sys
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path

from . import calcolo, cambio, lettura, listino, pagina
from .testi import TESTI, Formato, lingua_sistema

PAROLE_PROGETTO = {"progetto", "project"}
PAROLE_SESSIONE = {"sessione", "session"}


def periodo(parola, oggi=None):
    """(dal, al) in forma AAAA-MM-GG, None = senza limite.

    La settimana va da lunedi' a oggi; "7g" sono gli ultimi 7 giorni.
    Date impossibili, "0g" e intervalli rovesciati danno ValueError.
    """
    dal, al = _periodo(parola, oggi or date.today())
    for d in (dal, al):
        if d is not None:
            date.fromisoformat(d)      # 2026-02-30 -> ValueError
    if dal and al and dal > al:
        raise ValueError(parola)
    return dal, al


def _periodo(parola, oggi):
    p = parola.lower()
    if p in ("tutto", "all"):
        return None, None
    if p in ("oggi", "today"):
        return oggi.isoformat(), oggi.isoformat()
    if p in ("ieri", "yesterday"):
        ieri = oggi - timedelta(days=1)
        return ieri.isoformat(), ieri.isoformat()
    lunedi = oggi - timedelta(days=oggi.weekday())
    if p in ("settimana", "week"):
        return lunedi.isoformat(), oggi.isoformat()
    if p in ("settimana-scorsa", "last-week"):
        return (lunedi - timedelta(days=7)).isoformat(), (lunedi - timedelta(days=1)).isoformat()
    if p in ("mese", "month"):
        return oggi.replace(day=1).isoformat(), oggi.isoformat()
    if p in ("mese-scorso", "last-month"):
        fine = oggi.replace(day=1) - timedelta(days=1)
        return fine.replace(day=1).isoformat(), fine.isoformat()
    if p in ("anno", "year"):
        return oggi.replace(month=1, day=1).isoformat(), oggi.isoformat()
    m = re.fullmatch(r"(\d+)[gd]", p)
    if m and int(m.group(1)) > 0:
        return (oggi - timedelta(days=int(m.group(1)) - 1)).isoformat(), oggi.isoformat()
    m = re.fullmatch(r"(\d{4})-(\d{2})", p)
    if m:
        anno, mese = int(m.group(1)), int(m.group(2))
        fine = date(anno + mese // 12, mese % 12 + 1, 1) - timedelta(days=1)
        return date(anno, mese, 1).isoformat(), fine.isoformat()
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})?\.\.(\d{4}-\d{2}-\d{2})?", p)
    if m and (m.group(1) or m.group(2)):
        return m.group(1), m.group(2)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p):
        return p, p
    raise ValueError(parola)


def argomenti(argv):
    a = argparse.ArgumentParser(
        prog="consumo-claude",
        description="Token, costo e lavoro umano equivalente delle sessioni di Claude Code.")
    a.add_argument("parole", nargs="*",
                   help="progetto | sessione, e un periodo: oggi, ieri, settimana, "
                        "settimana scorsa, mese, mese scorso, anno, 7g, 30g, 2026-09, "
                        "2026-09-01..2026-09-15, tutto")
    a.add_argument("--cartella", "--dir", help="cartella delle cronologie (predefinita ~/.claude/projects)")
    a.add_argument("--lingua", "--lang", choices=["it", "en"], help="lingua (predefinita quella del sistema)")
    a.add_argument("--sessione-id", "--session-id", help="sessione da mostrare con 'sessione'")
    a.add_argument("--non-aprire", "--no-open", action="store_true", help="non aprire la pagina nel browser")
    a.add_argument("--senza-pagina", "--no-page", action="store_true", help="non generare la pagina HTML")
    a.add_argument("--pagina", "--page", help="dove salvare la pagina HTML")
    a.add_argument("--json", action="store_true", help="stampa i dati calcolati in JSON, per altri programmi")
    a.add_argument("--offline", action="store_true", help="non aggiornare cambio e listino prezzi da internet")
    a.add_argument("--listino", "--prices", action="store_true", help="mostra il listino prezzi usato")
    a.add_argument("--continuo", "--watch", nargs="?", const=5, type=float, metavar="MINUTI",
                   help="rigenera la pagina ogni MINUTI (5 se non indicati) finche' non si chiude con Ctrl+C")
    a.add_argument("--tariffa", "--rate", type=float, metavar="N",
                   help="tariffa oraria del lavoro umano (predefinita 10 euro, o 45 dollari in inglese)")
    a.add_argument("--senza-archivio", "--no-cache", action="store_true", help="rileggi tutte le cronologie")
    a.add_argument("--impostazioni", "--settings", action="store_true",
                   help="crea (se manca) e mostra il file delle impostazioni personali")
    return a.parse_intermixed_args(argv)


def mostra_impostazioni():
    cartella = calcolo.cartella_impostazioni()
    cartella.mkdir(parents=True, exist_ok=True)
    for nome in ("impostazioni.json", "prezzi.json"):
        dest = cartella / nome
        if not dest.exists():
            dest.write_text((calcolo.DATI / nome).read_text(encoding="utf-8"), encoding="utf-8")
        print(dest)


def tabella(righe, intestazione, allinea):
    """Tabella di testo: allinea e' una stringa di 'l'/'r' per colonna."""
    tutte = [intestazione] + [r for r in righe if r is not None]
    larghezze = [max(len(str(r[i])) for r in tutte) for i in range(len(intestazione))]
    riga_vuota = "-" * (sum(larghezze) + 2 * (len(larghezze) - 1))
    uscita = []
    for n, r in enumerate([intestazione] + righe):
        if r is None:
            uscita.append(riga_vuota)
            continue
        celle = [str(v).ljust(larghezze[i]) if allinea[i] == "l" else str(v).rjust(larghezze[i])
                 for i, v in enumerate(r)]
        uscita.append("  ".join(celle).rstrip())
        if n == 0:
            uscita.append(riga_vuota)
    return "\n".join(uscita)


def taglia(testo, n):
    return testo if len(testo) <= n else testo[: n - 1] + "…"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    arg = argomenti(argv)
    if arg.continuo:
        return continuo(argv, arg.continuo)
    return _main(arg)


def continuo(argv, minuti):
    """Rigenera la pagina ogni tot minuti; il browser la apre solo la prima volta."""
    import time
    resto, i = [], 0
    while i < len(argv):      # si toglie --continuo e il suo eventuale numero
        x = argv[i]
        if x in ("--continuo", "--watch"):
            if i + 1 < len(argv) and re.fullmatch(r"\d+(\.\d+)?", argv[i + 1]):
                i += 1
        elif not x.startswith(("--continuo=", "--watch=")):
            resto.append(x)
        i += 1
    primo = True
    try:
        while True:
            codice = _main(argomenti(resto + ([] if primo else ["--non-aprire"])))
            if codice:
                return codice
            primo = False
            print("\n(%s)\n" % datetime.now().strftime("%H:%M"), flush=True)
            time.sleep(max(minuti, 0.5) * 60)
    except KeyboardInterrupt:
        return 0


def _main(arg):
    if arg.impostazioni:
        mostra_impostazioni()
        return 0

    lingua = arg.lingua or lingua_sistema()
    t = TESTI[lingua]
    fmt = Formato(lingua)

    # "settimana scorsa", "last week"... arrivano come due parole separate.
    parole = re.sub(r"\b(settimana|mese|last)\s+(scorsa|scorso|week|month)\b", r"\1-\2",
                    " ".join(arg.parole), flags=re.I).split()
    vista, dal, al = "tutto", None, None
    for parola in parole:
        if parola.lower() in PAROLE_PROGETTO:
            vista = "progetto"
        elif parola.lower() in PAROLE_SESSIONE:
            vista = "sessione"
        else:
            try:
                dal, al = periodo(parola)
            except ValueError:
                print("?? %s" % parola, file=sys.stderr)
                return 2

    imp = calcolo.carica_json("impostazioni.json")
    prezzi, fonte_listino = listino.carica(not arg.offline)
    if arg.listino:
        stampa_listino(prezzi, fonte_listino, t, fmt)
        return 0
    valuta = imp.get("valuta", "auto")
    if valuta == "auto":
        valuta = "EUR" if lingua == "it" else "USD"
    tariffa = arg.tariffa if arg.tariffa is not None and arg.tariffa >= 0 else imp["tariffa_oraria"].get(valuta)
    tasso, fonte_cambio, data_cambio = cambio.cambio(valuta, imp, not arg.offline)

    radice = lettura.cartella_cronologie(arg.cartella)
    file_letti = lettura.carica(radice, usa_archivio=not arg.senza_archivio)
    if not file_letti:
        print(t["nessuna_cronologia"] % radice, file=sys.stderr)
        return 1
    rapporto = calcolo.calcola(file_letti, radice, calcolo.Prezzi(prezzi), imp)

    rapporto.update({
        "lingua": lingua,
        "valuta": valuta,
        "tariffa": tariffa,
        "cambio": {"tasso": tasso, "fonte": fonte_cambio, "data": data_cambio},
        "parametri": imp,
        "prezzi_verificati": prezzi.get("verificati_il"),
        "listino": {"fonte": fonte_listino, "modelli": prezzi["modelli"],
                    "modalita_veloce": prezzi.get("modalita_veloce", {})},
        "generato": datetime.now().isoformat(timespec="minutes"),
    })

    # Filtri: progetto o sessione corrente, periodo.
    celle = [c for c in rapporto["celle"]
             if (dal is None or c[1] >= dal) and (al is None or c[1] <= al)]
    sessioni = rapporto["sessioni"]
    filtro_progetto = filtro_sessione = None
    if vista == "progetto":
        qui = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        # Vale anche una sottocartella del progetto, ma non la home o la radice,
        # che conterrebbero qualunque cartella.
        generiche = {os.path.realpath(str(Path.home())), os.path.realpath(os.sep)}
        candidati = [p for p in rapporto["progetti"]
                     if qui == os.path.realpath(p) or (
                         os.path.realpath(p) not in generiche
                         and qui.startswith(os.path.realpath(p).rstrip(os.sep) + os.sep))]
        if not candidati:
            print(t["progetto_non_trovato"] % qui, file=sys.stderr)
            return 1
        filtro_progetto = max(candidati, key=len)
        celle = [c for c in celle if sessioni[c[0]]["progetto"] == filtro_progetto]
    elif vista == "sessione":
        # Una sessione indicata ma inesistente e' un errore: mostrarne un'altra
        # al suo posto sarebbe fuorviante. Senza indicazioni, l'ultima del progetto.
        sid = arg.sessione_id or os.environ.get("CLAUDE_SESSION_ID")
        if not sid:
            qui = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
            del_progetto = [s for s, v in sessioni.items() if os.path.realpath(v["progetto"]) == qui]
            sid = max(del_progetto, key=lambda s: sessioni[s]["fine"]) if del_progetto else None
        if not sid or sid not in sessioni:
            print(t["sessione_non_trovata"], file=sys.stderr)
            return 1
        filtro_sessione = sid
        celle = [c for c in celle if c[0] == sid]

    if arg.json:
        # Solo quello che ricade nel periodo e nella vista scelti, con l'ordine
        # dei valori nelle celle.
        scelte = {(c[0], c[1]) for c in celle}
        uscita = dict(rapporto, campi_celle=["sessione", "giorno"] + calcolo.CAMPI,
                      celle=celle, dal=dal, al=al)
        uscita["modelli"] = [m for m in rapporto["modelli"] if (m[0], m[1]) in scelte]
        uscita["ignoti"] = [m for m in rapporto["ignoti"] if (m[0], m[1]) in scelte]
        in_uso = {c[0] for c in celle}
        uscita["sessioni"] = {k: v for k, v in sessioni.items() if k in in_uso}
        uscita["progetti"] = {k: v for k, v in rapporto["progetti"].items()
                              if any(s["progetto"] == k for s in uscita["sessioni"].values())}
        json.dump(uscita, sys.stdout, ensure_ascii=False)
        return 0

    stampa(rapporto, celle, vista, filtro_progetto, filtro_sessione, t, fmt, dal, al)

    if not arg.senza_pagina:
        destinazione = Path(arg.pagina) if arg.pagina else lettura.cartella_archivio() / "consumo-claude.html"
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        pagina.scrivi(destinazione, rapporto, t, filtro_progetto, dal, al)
        print("\n%s %s" % (t["pagina"], destinazione))
        if not arg.non_aprire:
            try:
                webbrowser.open(destinazione.resolve().as_uri())
            except Exception:
                pass
    print(t["firma"] + " · horizonpeak.it")
    return 0


def stampa_listino(prezzi, fonte, t, fmt):
    print(t["listino_titolo"] % prezzi.get("verificati_il", "?") + " (" + t["fonte_" + fonte] + ")\n")
    righe = []
    for nome, tar in sorted(prezzi["modelli"].items()):
        righe.append([nome] + [fmt.numero(tar[v], 2) for v in listino.VOCI])
    for nome, tar in sorted(prezzi.get("modalita_veloce", {}).items()):
        righe.append([nome + " (" + t["veloce"] + ")"] + [fmt.numero(tar[v], 2) for v in listino.VOCI])
    print(tabella(righe, [t["modello"], t["letti"], t["scritti"], t["cache_5m"], t["cache_1h"],
                          t["cache_riletti"]], "lrrrrr"))
    print("\n" + t["listino_nota"])


def stampa(rapporto, celle, vista, filtro_progetto, filtro_sessione, t, fmt, dal, al):
    ore_giornata = rapporto["parametri"]["ore_giornata"]
    valuta, tariffa = rapporto["valuta"], rapporto["tariffa"]
    sessioni, progetti = rapporto["sessioni"], rapporto["progetti"]

    def umano(r):
        return fmt.soldi(r["ore"] * tariffa, valuta) if tariffa else "-"

    intervallo = ""
    if dal or al:
        intervallo = "  (%s … %s)" % (dal or "", al or "")
    if not celle:
        print(t["nessun_dato"])
        return

    if vista == "tutto":
        print(t["titolo"] + " · " + t["tutti_progetti"] + intervallo + "\n")
        gruppi = {}
        for c in celle:
            gruppi.setdefault(sessioni[c[0]]["progetto"], []).append(c)
        righe = []
        for p, cc in gruppi.items():
            r = calcolo.riepiloga(cc, ore_giornata)
            righe.append((r["v"][calcolo.COSTO], [
                taglia(progetti[p]["nome"], 30), fmt.numero(len({c[0] for c in cc})), fmt.token(r["token"]),
                fmt.soldi(r["v"][calcolo.COSTO], "USD"), fmt.decimale(r["ore"]),
                fmt.decimale(r["giorni_persona"]), fmt.decimale(calcolo.persone_gruppo(r)), umano(r)]))
        righe = [r for _, r in sorted(righe, key=lambda x: -x[0])]
        intest = [t["progetto"], t["sessioni"], t["token"], t["claude"], t["ore_persona"],
                  t["giorni"], t["persone"], t["lavoro_umano"]]
        r = calcolo.riepiloga(celle, ore_giornata)
        righe.append(None)
        righe.append([t["totale"], fmt.numero(len({c[0] for c in celle})), fmt.token(r["token"]),
                      fmt.soldi(r["v"][calcolo.COSTO], "USD"), fmt.decimale(r["ore"]),
                      fmt.decimale(r["giorni_persona"]), fmt.decimale(calcolo.persone_gruppo(r)), umano(r)])
        print(tabella(righe, intest, "lrrrrrrr"))
    elif vista == "progetto":
        print(t["titolo"] + " · " + progetti[filtro_progetto]["nome"] + intervallo + "\n")
        gruppi = {}
        for c in celle:
            gruppi.setdefault(c[0], []).append(c)
        righe = []
        for sid, cc in sorted(gruppi.items(), key=lambda x: -sessioni[x[0]]["inizio"]):
            r = calcolo.riepiloga(cc, ore_giornata)
            righe.append([datetime.fromtimestamp(sessioni[sid]["inizio"]).strftime("%Y-%m-%d"),
                          taglia(sessioni[sid]["titolo"] or t["senza_titolo"], 38), fmt.durata(r["v"][calcolo.MINUTI]),
                          fmt.token(r["token"]), fmt.soldi(r["v"][calcolo.COSTO], "USD"),
                          fmt.decimale(r["ore"]), fmt.decimale(calcolo.persone_sessione(r)), umano(r)])
        r = calcolo.riepiloga(celle, ore_giornata)
        righe.append(None)
        righe.append([t["totale"], "%s %s" % (fmt.numero(len(gruppi)), t["sessioni"].lower()),
                      fmt.durata(r["v"][calcolo.MINUTI]), fmt.token(r["token"]),
                      fmt.soldi(r["v"][calcolo.COSTO], "USD"), fmt.decimale(r["ore"]),
                      fmt.decimale(calcolo.persone_gruppo(r)), umano(r)])
        print(tabella(righe, [t["data"], t["sessione"], t["durata"], t["token"], t["claude"],
                              t["ore_persona"], t["persone"], t["lavoro_umano"]], "lllrrrrr"))
    else:
        s = sessioni[filtro_sessione]
        r = calcolo.riepiloga(celle, ore_giornata)
        v = r["v"]
        print(t["titolo"] + " · " + t["sessione"] + ": " + (s["titolo"] or t["senza_titolo"]))
        print(progetti[s["progetto"]]["nome"] + " · " +
              datetime.fromtimestamp(s["inizio"]).strftime("%Y-%m-%d %H:%M") + "\n")
        voci = [
            (t["durata"], fmt.durata(v[calcolo.MINUTI])),
            (t["letti"], fmt.token(v[calcolo.LETTI])),
            (t["scritti"], "%s (%s %s)" % (fmt.token(v[calcolo.SCRITTI]), t["di_cui_pensiero"],
                                           fmt.token(v[calcolo.PENSIERO]))),
            (t["cache_scritti"], fmt.token(v[calcolo.CACHE_SCRITTI])),
            (t["cache_riletti"], fmt.token(v[calcolo.CACHE_RILETTI])),
            (t["costo_claude"], fmt.soldi(v[calcolo.COSTO], "USD")),
            (t["ore_persona"], fmt.decimale(r["ore"])),
            (t["giorni_persona"], fmt.decimale(r["giorni_persona"])),
            (t["persone"], fmt.decimale(calcolo.persone_sessione(r))),
            (t["costo_lavoro"], umano(r)),
        ]
        larghezza = max(len(k) for k, _ in voci)
        for k, val in voci:
            print("  " + k.ljust(larghezza) + "  " + val)
        per_modello = {}
        for sid, g, m, tok, dollari in rapporto["modelli"]:
            if sid == filtro_sessione and any(c[1] == g for c in celle):
                x = per_modello.setdefault(m, [0, 0.0])
                x[0] += tok
                x[1] += dollari
        if per_modello:
            print()
            print(tabella([[m, fmt.token(x[0]), fmt.soldi(x[1], "USD")]
                           for m, x in sorted(per_modello.items(), key=lambda y: -y[1][1])],
                          [t["modello"], t["token"], t["claude"]], "lrr"))

    print()
    scelte = {(c[0], c[1]) for c in celle}
    ignoti = {}
    for sid, g, m, tok in rapporto["ignoti"]:
        if (sid, g) in scelte:
            ignoti[m] = ignoti.get(m, 0) + tok
    for m, tok in sorted(ignoti.items()):
        print("! " + t["avviso_ignoti"] % (m, fmt.token(tok)))
    if rapporto["illeggibili"] == 1:
        print("! " + t["avviso_illeggibili_1"])
    elif rapporto["illeggibili"]:
        print("! " + t["avviso_illeggibili"] % fmt.numero(rapporto["illeggibili"]))
    print(t["avviso_abbonamento"])
    print(t["listino_riga"] % rapporto["prezzi_verificati"])


if __name__ == "__main__":
    sys.exit(main())
