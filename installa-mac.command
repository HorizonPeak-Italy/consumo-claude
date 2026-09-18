#!/bin/sh
# Doppio clic su Mac: avvia l'installazione nel Terminale.
sh "$(dirname "$0")/installa.sh"
printf "Premi Invio per chiudere..."
read x
