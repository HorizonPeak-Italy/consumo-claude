# Consumo Claude

**Italiano** · [English](#english)

Quanti token hai consumato con Claude Code, quanto sarebbero costati a listino
API e quante persone, per quante ore e giorni, avrebbero dovuto lavorare per
fare lo stesso lavoro. Per ogni progetto e per ogni sessione.

```
Progetto            Sessioni          Token   Claude  Ore-persona  Giorni  Persone  Lavoro umano
-----------------------------------------------------------------------------------------------
sito-negozio              24   1,2 miliardi    742 $          268    33,5      2,1       5.360 €
app-mobile                17    530 milioni    351 $          190    23,8      1,9       3.800 €
...
```

Più una pagina da aprire nel browser, con grafico giorno per giorno, divisione
per modello, tabelle ordinabili e menu per scegliere periodo e progetto.

## Cosa conta e cosa no

Legge le cronologie che Claude Code salva **sul tuo computer**
(`~/.claude/projects`). Quindi:

| Dove usi Claude | Contato? |
|---|---|
| Claude Code nel terminale | Sì |
| Scheda Code dell'app desktop di Claude (sessioni locali) | Sì |
| Estensioni di Claude Code per VS Code e JetBrains | Sì |
| Lavori automatici con Claude Code o l'Agent SDK sul computer | Sì |
| Sessioni comandate dal telefono che girano sul computer | Sì |
| Claude Code sul web (claude.ai/code): gira nel cloud | No |
| Chat su claude.ai, app per telefono, Claude in Chrome da solo | No |

Ogni computer conta le proprie sessioni: se usi Claude Code su più computer,
va lanciato su ciascuno (oppure su uno solo, se le cartelle
`~/.claude/projects` sono sincronizzate).

## Installazione

### Il modo più semplice: installatore automatico

Estrai lo ZIP, poi:

| Sistema | Cosa fare |
|---|---|
| **Windows** | Doppio clic su `installa-windows.bat` |
| **Mac** | Doppio clic su `installa-mac.command`. Il Mac lo blocca perché viene da internet: apri *Impostazioni di Sistema → Privacy e sicurezza*, in fondo premi *Apri comunque*, poi di nuovo doppio clic |
| **Linux** | Nel terminale, dalla cartella estratta: `sh installa.sh` |

L'installatore controlla Python (su Windows, se manca, lo installa con il tuo
permesso), copia il programma in una cartella stabile, crea un'icona
"Consumo Claude" (desktop su Windows e Mac, menu delle applicazioni su Linux)
e, se hai Claude Code, aggiunge il comando `/consumo`. L'icona non consuma
token. Per togliere tutto (programma, icona, comando `/consumo`, archivio e
impostazioni): `Disinstalla.bat` in `%LOCALAPPDATA%\Programs\consumo-claude`
su Windows, `sh ~/.local/share/consumo-claude/disinstalla.sh` su Linux e Mac.

### A mano

Serve **Python 3.8 o successivo**: su Linux e Mac c'è quasi sempre, su Windows
si scarica da [python.org](https://www.python.org/downloads/) (spuntare "Add
python.exe to PATH").

### Claude Code nel terminale (Linux, Mac, Windows)

Dentro Claude Code, una volta sola per computer:

```
/plugin marketplace add HorizonPeak-Italy/consumo-claude
/plugin install consumo-claude@horizonpeak
```

Poi, da qualunque progetto:

```
/consumo
```

Oppure, dal terminale normale, fuori da Claude Code:

```
claude plugin marketplace add HorizonPeak-Italy/consumo-claude
claude plugin install consumo-claude@horizonpeak
```

### App desktop di Claude (scheda Code) e estensioni VS Code / JetBrains

Usano la stessa configurazione di Claude Code (`~/.claude`): dopo
l'installazione qui sopra, `/consumo` è disponibile anche lì. Se non hai mai
usato Claude Code da terminale, dai i due comandi `/plugin` direttamente nella
finestra della sessione.

### Senza plugin (qualunque sistema, zero token)

Scarica questo repository (pulsante *Code → Download ZIP*, oppure
`git clone https://github.com/HorizonPeak-Italy/consumo-claude`), poi dalla cartella:

```
bin/consumo-claude                 # Linux e Mac
python -m consumo_claude           # Windows (PowerShell o Prompt dei comandi)
```

### Telefono (Android, iPhone), Claude Code sul web, claude.ai

Non si installa: sul telefono Claude Code non gira e le cronologie stanno sul
computer. Se però comandi dal telefono una sessione di Claude Code che gira sul
tuo computer, `/consumo` funziona anche da lì e ti mostra la tabella nella chat.

## Uso

| Comando | Cosa fa |
|---|---|
| `/consumo` | Tutti i progetti, e apre la pagina nel browser |
| `/consumo progetto` | Le sessioni del progetto in cui ti trovi |
| `/consumo sessione` | La sessione in corso, divisa per modello |
| `/consumo oggi` · `ieri` · `settimana` · `settimana scorsa` · `mese` · `mese scorso` · `anno` | Periodi di calendario (la settimana parte dal lunedì) |
| `/consumo 7g` · `30g` · `2026-09` · `2026-09-01..2026-09-15` | Ultimi N giorni, un mese preciso, un intervallo |

Le parole si combinano: `/consumo progetto 30g`. Fuori da Claude Code le
stesse parole vanno dopo `consumo-claude`, più alcune opzioni
(`consumo-claude --help`): `--lingua en`, `--non-aprire`, `--json` (i dati
calcolati, per altri programmi), `--offline`.

**Da sapere:** `/consumo` dentro Claude passa il riepilogo nella conversazione e
consuma qualche migliaio di token ogni volta. Da terminale non costa nulla.

## Come si calcola

- **Token e costo** vengono dalle cronologie, risposta per risposta, con la
  tariffa del modello che ha risposto (`consumo_claude/dati/prezzi.json`). Ogni
  risposta si conta una volta sola, con il conteggio definitivo; i
  sotto-agenti si sommano alla sessione che li ha lanciati. Su un archivio
  reale di 7,3 miliardi di token il totale coincide con
  [ccusage](https://github.com/ryoppippi/ccusage) allo 0,06%.
- **Con un abbonamento (Pro, Max) il costo non si paga:** dice quanto sarebbe
  costato a consumo.
- **Il lavoro umano è una stima**, media di due metodi: (A) quanto Claude ha
  scritto, al ritmo di una persona (30 righe di codice o 500 parole l'ora);
  (B) quante azioni ha compiuto, ognuna con un tempo fisso (leggere un file 3
  minuti, modificarlo 10, crearlo 15, un comando 5...).
- **Persone** = quante ne servirebbero per finire nello stesso tempo di
  Claude: per una sessione, ore-persona diviso la durata attiva (senza le pause
  oltre 30 minuti); per un progetto, giorni-persona diviso i giorni in cui ci
  si è lavorato.
- **Costo del lavoro umano** = ore-persona per 10 € l'ora (45 $ in inglese).
  La tariffa si cambia nella casella *Tariffa* della pagina (che la ricorda) o
  da terminale con `--tariffa 15`. Il costo di Claude è convertito con il
  cambio BCE del giorno.

Tutti i numeri si cambiano: `consumo-claude --impostazioni` crea le copie
personali di `impostazioni.json` e `prezzi.json` e dice dove sono.

## Prezzi

Il listino (dollari per milione di token, per ogni modello e tipo di token) si
vede in fondo alla pagina o con `consumo-claude --listino`. **Si aggiorna da
solo:** Anthropic non pubblica i prezzi in un formato leggibile dai programmi,
quindi il listino sta in questo repository
([`prezzi.json`](consumo_claude/dati/prezzi.json)) e il programma ne scarica la
versione più recente al massimo una volta al giorno. Quando i prezzi cambiano
si aggiorna qui, e arrivano a tutti senza reinstallare.

## Privacy

Il programma legge le cronologie e non le modifica mai. Si collega a internet
solo per due cose, e nessuna delle due contiene dati tuoi:

- il cambio dollaro/euro della BCE da [frankfurter.dev](https://frankfurter.dev),
  al massimo ogni 12 ore;
- il listino prezzi da questo repository GitHub, al massimo una volta al giorno.

Si spengono entrambe con `--offline`.

La pagina HTML contiene nomi dei progetti e titoli delle sessioni (quelli che
Claude Code mostra nell'elenco), mai il testo dei messaggi. I titoli però
possono dire molto: attenzione se la condividi.

## Licenza

Apache 2.0, © 2026 [Horizon Peak srls](https://horizonpeak.it). Puoi usarlo,
modificarlo e ridistribuirlo anche per lavoro; chi ne ridistribuisce una
versione deve includere il file `NOTICE` e indicare le modifiche.

---

<a id="english"></a>

# Claude Usage (consumo-claude)

How many tokens you used with Claude Code, what they would have cost at API
list prices, and how many people, for how many hours and days, would have had
to work to do the same job. Per project and per session, in the terminal and
in a browser page with a daily chart, per-model breakdown, sortable tables
and period and project menus.

## What it counts

It reads the history Claude Code saves **on your computer**
(`~/.claude/projects`): the terminal, the Code tab of the Claude desktop app
(local sessions), the VS Code and JetBrains extensions, and automated runs on
the machine. It cannot see Claude Code on the web (claude.ai/code runs in the
cloud), claude.ai chats, the mobile apps or Claude in Chrome on its own.

## Install

Requires **Python 3.8+** (preinstalled on most Linux and Mac systems; on
Windows get it from [python.org](https://www.python.org/downloads/)).

**Claude Code (terminal, desktop app, IDE extensions)**, once per computer:

```
/plugin marketplace add HorizonPeak-Italy/consumo-claude
/plugin install consumo-claude@horizonpeak
```

**Automatic installers**: extract the ZIP, then double-click
`installa-windows.bat` (Windows) or `installa-mac.command` (Mac), or run
`sh installa.sh` (Linux). They check Python, copy the program, add a
"Consumo Claude" icon and, if Claude Code is present, the `/consumo` command.

**Without the plugin**: download this repository and run
`bin/consumo-claude` (Linux, Mac) or `python -m consumo_claude` (Windows)
from its folder. This costs no tokens.

## Use

`/consumo` (all projects), `/consumo project`, `/consumo session`, plus a
period: `today`, `yesterday`, `week`, `last week`, `month`, `last month`,
`year`, `7d`, `30d`, `2026-09`, `2026-09-01..2026-09-15`. Outside
Claude Code: `consumo-claude --help`. The language follows your system
(`--lang en|it`).

`/consumo` inside Claude puts the summary in the conversation and costs a few
thousand tokens each time; the standalone command costs nothing.
`consumo-claude --prices` shows the price list in use.

## How it is calculated

Cost uses the API list price of the model that produced each response
(`consumo_claude/dati/prezzi.json`); each response counts once, subagents are
added to their parent session. On subscription plans you don't pay this
amount: it shows what the usage would have cost. Human work is an estimate:
the average of (A) output volume at a human pace (30 lines of code or 500
words per hour) and (B) actions taken at fixed times (read a file 3 min, edit
10, create 15, run a command 5...). People = how many would be needed to
finish in the same time. Human cost = person-hours at $45/hour, adjustable in the page's *Rate* box or with `--rate`. Every
parameter can be changed: `consumo-claude --settings`.

## Privacy

Read-only. Two network calls, neither carrying your data: the ECB exchange
rate from frankfurter.dev (at most every 12 hours) and the price list from
this repository (at most once a day, so price changes reach everyone without
reinstalling). `--offline` disables both. The HTML page contains project names
and session titles, never message text.

## License

Apache 2.0, © 2026 [Horizon Peak srls](https://horizonpeak.it). See `NOTICE`.
