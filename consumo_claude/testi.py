"""Testi in italiano e inglese, e formattazione dei numeri."""

import locale
import os

TESTI = {
    "it": {
        "titolo": "Consumo Claude",
        "sottotitolo": "Token, costo e lavoro umano equivalente delle sessioni di Claude Code",
        "periodo": "Periodo",
        "tutto": "Tutto",
        "ultimi_7": "Ultimi 7 giorni",
        "ultimi_30": "Ultimi 30 giorni",
        "ultimi_90": "Ultimi 90 giorni",
        "questo_mese": "Questo mese",
        "oggi": "Oggi",
        "ieri": "Ieri",
        "questa_settimana": "Questa settimana",
        "settimana_scorsa": "Settimana scorsa",
        "mese_scorso": "Mese scorso",
        "questo_anno": "Quest'anno",
        "personalizzato": "Personalizzato",
        "dal": "dal",
        "al": "al",
        "progetto": "Progetto",
        "progetti": "Progetti",
        "sessione": "Sessione",
        "sessioni": "Sessioni",
        "data": "Data",
        "durata": "Durata",
        "token": "Token",
        "claude": "Claude",
        "costo_claude": "Costo di Claude",
        "ore_persona": "Ore-persona",
        "giorni": "Giorni",
        "giorni_persona": "Giorni-persona",
        "persone": "Persone",
        "lavoro_umano": "Lavoro umano",
        "costo_lavoro": "Costo del lavoro umano",
        "totale": "Totale",
        "modello": "Modello",
        "modelli": "Per modello",
        "andamento": "Costo di Claude giorno per giorno",
        "letti": "Letti",
        "scritti": "Scritti",
        "di_cui_pensiero": "di cui ragionamento",
        "cache_scritti": "Scritti in cache",
        "cache_riletti": "Riletti dalla cache",
        "nessun_dato": "Nessuna sessione nel periodo scelto.",
        "nessuna_cronologia": "Nessuna cronologia trovata in %s",
        "progetto_non_trovato": "Nessuna sessione di Claude Code per questa cartella: %s",
        "sessione_non_trovata": "Sessione non trovata.",
        "tutti_progetti": "Tutti i progetti",
        "clic_progetto": "Clic su un progetto per vederne le sessioni.",
        "sessioni_di": "Sessioni di %s",
        "avviso_abbonamento": ("Con un abbonamento (Pro, Max) queste cifre non si pagano: "
                               "dicono quanto sarebbe costato a consumo, a listino API."),
        "avviso_ignoti": "Prezzo sconosciuto per %s (%s token non conteggiati in dollari): aggiungerlo a prezzi.json.",
        "avviso_illeggibili_1": ("Una riga delle cronologie è incompleta (succede quando una sessione viene "
                                 "interrotta mentre salva) ed è stata saltata: il conto può essere più basso "
                                 "di qualche centesimo."),
        "avviso_illeggibili": ("%s righe delle cronologie sono incomplete (succede quando una sessione viene "
                               "interrotta mentre salva) e sono state saltate: il conto può essere un po' più basso."),
        "avviso_condivisione": ("Questa pagina contiene i nomi dei progetti e i titoli delle sessioni: "
                                "nessun contenuto delle chat, ma i titoli possono dire molto. Attenzione se la condividi."),
        "pagina": "Pagina:",
        "metodo_titolo": "Come si calcola",
        "metodo_token": ("Token e costo vengono dalle cronologie di Claude Code, risposta per risposta, "
                         "con la tariffa del modello che ha risposto (listino verificato il %s). "
                         "Ogni risposta si conta una volta sola; i sotto-agenti si sommano alla sessione che li ha lanciati."),
        "metodo_umano": ("Il lavoro umano è una stima, non una misura. È la media di due metodi: "
                         "(A) quanto Claude ha scritto, al ritmo di una persona: %s righe di codice o %s parole di testo l'ora; "
                         "(B) quante azioni ha compiuto, ognuna con un tempo fisso: %s."),
        "metodo_persone": ("Giorni-persona = ore / %s. Persone = quante ne servirebbero per finire nello stesso tempo: "
                           "per una sessione ore-persona diviso la durata attiva (senza pause oltre %s minuti), "
                           "per un progetto giorni-persona diviso i giorni in cui ci si è lavorato."),
        "metodo_costo": "Costo del lavoro umano = ore-persona per %s l'ora.",
        "cambio_bce": "Cambio BCE del %s: 1 $ = %s %s.",
        "cambio_fisso": "Cambio fisso (non aggiornato): 1 $ = %s %s.",
        "azioni_nomi": {"leggere": "leggere un file", "cercare": "cercare", "comando": "lanciare un comando",
                        "modificare": "modificare un file", "creare": "creare un file",
                        "web": "ricerca o pagina web", "browser": "azione nel browser"},
        "minuti": "min",
        "senza_titolo": "(senza titolo)",
        "listino_titolo": "Listino prezzi del %s, dollari per milione di token",
        "listino_riga": "Prezzi a listino API del %s, aggiornati da soli (consumo-claude --listino per vederli).",
        "listino_nota": "Aggiornato da solo dal repository del programma, al massimo una volta al giorno.",
        "fonte_aggiornato": "aggiornato da internet",
        "fonte_programma": "quello del programma",
        "fonte_personale": "con i prezzi personali",
        "veloce": "modalità veloce",
        "cache_5m": "Cache 5 min",
        "cache_1h": "Cache 1 ora",
        "listino_pagina": "Listino prezzi",
        "listino_sotto": "Dollari per milione di token, listino API del %s. Si aggiorna da solo.",
        "grafico_esclusi": "Esclusi dal grafico %s giorni prima del %s con consumi minimi (%s in tutto): sono comunque nei totali.",
        "grafico_escluso": "Escluso dal grafico %s giorno prima del %s con consumi minimi (%s): è comunque nei totali.",
        "tema_chiaro": "Tema chiaro",
        "tariffa": "Tariffa",
        "in_valuta": "In euro",
        "tema_scuro": "Tema scuro",
        "modelli_nota": "Percentuale sul costo totale. Passa sopra una riga per vedere i token.",
        "aggiornata": "Dati fino al %s",
        "firma": "Consumo Claude, di Horizon Peak srls",
    },
    "en": {
        "titolo": "Claude Usage",
        "sottotitolo": "Tokens, cost and equivalent human work of your Claude Code sessions",
        "periodo": "Period",
        "tutto": "All time",
        "ultimi_7": "Last 7 days",
        "ultimi_30": "Last 30 days",
        "ultimi_90": "Last 90 days",
        "questo_mese": "This month",
        "oggi": "Today",
        "ieri": "Yesterday",
        "questa_settimana": "This week",
        "settimana_scorsa": "Last week",
        "mese_scorso": "Last month",
        "questo_anno": "This year",
        "personalizzato": "Custom",
        "dal": "from",
        "al": "to",
        "progetto": "Project",
        "progetti": "Projects",
        "sessione": "Session",
        "sessioni": "Sessions",
        "data": "Date",
        "durata": "Duration",
        "token": "Tokens",
        "claude": "Claude",
        "costo_claude": "Claude cost",
        "ore_persona": "Person-hours",
        "giorni": "Days",
        "giorni_persona": "Person-days",
        "persone": "People",
        "lavoro_umano": "Human work",
        "costo_lavoro": "Human work cost",
        "totale": "Total",
        "modello": "Model",
        "modelli": "By model",
        "andamento": "Claude cost per day",
        "letti": "Input",
        "scritti": "Output",
        "di_cui_pensiero": "of which thinking",
        "cache_scritti": "Cache writes",
        "cache_riletti": "Cache reads",
        "nessun_dato": "No sessions in the selected period.",
        "nessuna_cronologia": "No history found in %s",
        "progetto_non_trovato": "No Claude Code sessions for this folder: %s",
        "sessione_non_trovata": "Session not found.",
        "tutti_progetti": "All projects",
        "clic_progetto": "Click a project to see its sessions.",
        "sessioni_di": "Sessions of %s",
        "avviso_abbonamento": ("On a subscription (Pro, Max) you don't pay these amounts: "
                               "they show what it would have cost at API list prices."),
        "avviso_ignoti": "Unknown price for %s (%s tokens not counted in dollars): add it to prezzi.json.",
        "avviso_illeggibili_1": ("One history line is incomplete (this happens when a session is interrupted "
                                 "while saving) and was skipped: the total may be a few cents low."),
        "avviso_illeggibili": ("%s history lines are incomplete (this happens when a session is interrupted "
                               "while saving) and were skipped: the total may be slightly low."),
        "avviso_condivisione": ("This page contains project names and session titles: "
                                "no chat content, but titles can reveal a lot. Be careful when sharing it."),
        "pagina": "Page:",
        "metodo_titolo": "How it is calculated",
        "metodo_token": ("Tokens and cost come from the Claude Code history, response by response, "
                         "at the rate of the model that answered (price list checked on %s). "
                         "Each response is counted once; subagents are added to the session that launched them."),
        "metodo_umano": ("Human work is an estimate, not a measurement. It is the average of two methods: "
                         "(A) how much Claude wrote, at a person's pace: %s lines of code or %s words of text per hour; "
                         "(B) how many actions it took, each with a fixed time: %s."),
        "metodo_persone": ("Person-days = hours / %s. People = how many would be needed to finish in the same time: "
                           "for a session, person-hours divided by active time (excluding breaks over %s minutes); "
                           "for a project, person-days divided by the days it was worked on."),
        "metodo_costo": "Human work cost = person-hours at %s per hour.",
        "cambio_bce": "ECB rate of %s: $1 = %s %s.",
        "cambio_fisso": "Fixed rate (not updated): $1 = %s %s.",
        "azioni_nomi": {"leggere": "read a file", "cercare": "search", "comando": "run a command",
                        "modificare": "edit a file", "creare": "create a file",
                        "web": "web search or page", "browser": "browser action"},
        "minuti": "min",
        "senza_titolo": "(untitled)",
        "listino_titolo": "Price list of %s, dollars per million tokens",
        "listino_riga": "API list prices of %s, updated automatically (consumo-claude --prices to see them).",
        "listino_nota": "Updated automatically from the program's repository, at most once a day.",
        "fonte_aggiornato": "updated from the internet",
        "fonte_programma": "built into the program",
        "fonte_personale": "with personal prices",
        "veloce": "fast mode",
        "cache_5m": "Cache 5 min",
        "cache_1h": "Cache 1 hour",
        "listino_pagina": "Price list",
        "listino_sotto": "Dollars per million tokens, API list prices of %s. Updated automatically.",
        "grafico_esclusi": "%s days before %s with minimal usage (%s in total) are left out of the chart but included in the totals.",
        "grafico_escluso": "%s day before %s with minimal usage (%s) is left out of the chart but included in the totals.",
        "tema_chiaro": "Light theme",
        "tariffa": "Rate",
        "in_valuta": "Converted",
        "tema_scuro": "Dark theme",
        "modelli_nota": "Share of total cost. Hover a row to see the tokens.",
        "aggiornata": "Data up to %s",
        "firma": "Claude Usage (consumo-claude), by Horizon Peak srls",
    },
}

SIMBOLI = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}


def lingua_sistema():
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        v = os.environ.get(var)
        if v:
            return "it" if v.lower().startswith("it") else "en"
    try:
        v = locale.getlocale()[0] or ""
    except ValueError:
        v = ""
    return "it" if v.lower().startswith("it") else "en"


class Formato:
    def __init__(self, lingua):
        self.it = lingua == "it"

    def numero(self, x, decimali=0):
        s = "{:,.{}f}".format(x, decimali)
        if self.it:
            s = s.replace(",", "_").replace(".", ",").replace("_", ".")
        return s

    def token(self, x, con_parola=False):
        """Grandi numeri leggibili: 1,7 miliardi / 140 milioni / 57 mila (1.7B in inglese).

        con_parola aggiunge "token" ("1,7 miliardi di token").
        """
        unita = ((1e9, "miliardo", "miliardi"), (1e6, "milione", "milioni"), (1e3, "mila", "mila")) \
            if self.it else ((1e9, "B", "B"), (1e6, "M", "M"), (1e3, "K", "K"))
        for soglia, uno, tanti in unita:
            if x >= soglia:
                v = x / soglia
                testo = self.numero(v, 1 if v < 100 else 0)
                testo = testo[:-2] if testo.endswith((",0", ".0")) else testo
                if not self.it:
                    return testo + tanti + (" tokens" if con_parola else "")
                if soglia == 1e3:
                    testo = testo + " mila"
                else:
                    testo = testo + " " + (uno if testo == "1" else tanti)
                if con_parola:
                    testo += (" di token" if soglia > 1e3 else " token")
                return testo
        testo = self.numero(x)
        return testo + (" token" if self.it else " tokens") if con_parola else testo

    def soldi(self, x, valuta):
        simbolo = SIMBOLI.get(valuta, valuta)
        testo = self.numero(x, 2 if x < 100 else 0)
        return (testo + " " + simbolo) if self.it or valuta != "USD" else (simbolo + testo)

    def decimale(self, x):
        if x is None:
            return "-"
        return self.numero(x, 1 if x < 100 else 0)

    def durata(self, minuti):
        m = int(round(minuti))
        return "%d:%02d" % (m // 60, m % 60) if m >= 60 else "%d min" % m
