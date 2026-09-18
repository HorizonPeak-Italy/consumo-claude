"""Cambio dal dollaro alla valuta scelta, aggiornato da solo a ogni lancio.

Chiede il tasso BCE del giorno a frankfurter.dev (servizio gratuito, senza
chiavi). La richiesta contiene solo le due valute: nessun dato dell'utente.
Il risultato si salva e vale 12 ore; senza internet si usa l'ultimo salvato,
e in mancanza di quello il valore fisso delle impostazioni.
"""

import json
import time
import urllib.request

from .lettura import cartella_archivio

INDIRIZZO = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=%s"
VALIDITA = 12 * 3600


def cambio(valuta, imp, in_linea=True):
    """(tasso, fonte, data). fonte: 'bce' se aggiornato, 'fisso' altrimenti."""
    if valuta == "USD":
        return 1.0, "fisso", None
    fisso = imp.get("cambio_da_dollaro", {}).get(valuta)
    if not imp.get("cambio_automatico", True):
        return fisso, "fisso", None

    archivio = cartella_archivio() / "cambio.json"
    salvato = None
    try:
        with open(archivio, encoding="utf-8") as f:
            salvato = json.load(f)
        if salvato.get("valuta") != valuta:
            salvato = None
    except (OSError, ValueError):
        pass
    if salvato and time.time() - salvato.get("preso", 0) < VALIDITA:
        return salvato["tasso"], "bce", salvato["data"]

    if in_linea:
        try:
            richiesta = urllib.request.Request(
                INDIRIZZO % valuta, headers={"User-Agent": "consumo-claude"})
            with urllib.request.urlopen(richiesta, timeout=4) as r:
                risposta = json.load(r)
            tasso = float(risposta["rates"][valuta])
            salvato = {"valuta": valuta, "tasso": tasso,
                       "data": risposta.get("date"), "preso": time.time()}
            archivio.parent.mkdir(parents=True, exist_ok=True)
            with open(archivio, "w", encoding="utf-8") as f:
                json.dump(salvato, f)
            return tasso, "bce", salvato["data"]
        except Exception:
            pass
    if salvato:
        return salvato["tasso"], "bce", salvato["data"]
    return fisso, "fisso", None
