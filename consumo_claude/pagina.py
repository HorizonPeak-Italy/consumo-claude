"""Pagina HTML autonoma: un file unico con i dati dentro, senza risorse esterne."""

import json

from .calcolo import CAMPI, DATI


def scrivi(destinazione, rapporto, testi, progetto=None, dal=None, al=None):
    dati = dict(rapporto)
    dati["campi"] = CAMPI
    dati["testi"] = testi
    dati["iniziale"] = {"progetto": progetto, "dal": dal, "al": al}
    # "</" dentro un <script> chiuderebbe il blocco: si spezza.
    carico = json.dumps(dati, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    modello = (DATI / "pagina.html").read_text(encoding="utf-8")
    html = (modello.replace("__LINGUA__", rapporto["lingua"])
            .replace("__TITOLO__", testi["titolo"])
            .replace("__DATI__", carico))
    destinazione.write_text(html, encoding="utf-8")
