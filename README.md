#CHATBOT PER LA CREAZIONE DI CORSI DIDATTICI

##Utilizzo del RS
Avviare il file rsServer da dentro la cartella SanicRS
Avviare rasa con rasa run --enable-api --cors="*"
Avviare le actions con rasa run actions

La front end si trova a 127.0.0.1/frontpage (bisogna attendere che il server sia online, circa 60/70 secondi dall'avvio di rsServer.py)
Si puó modificare la linea 109 di rsServer.py cambiando numero nella funzione head per avere piú o meno raccomandazioni
