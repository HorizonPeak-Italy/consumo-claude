#!/bin/sh
# Avvio dall'icona (Linux e Mac): mostra il riepilogo, apre la pagina e
# aspetta Invio, cosi' la finestra non si chiude prima di aver letto.
"$(dirname "$0")/bin/consumo-claude"
echo
printf "Premi Invio per chiudere... "
read x
