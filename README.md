# CHATBOT PER LA CREAZIONE DI CORSI DIDATTICI

## Aprire il chatbot 
- installare Rasa sul proprio pc
- andare nella directory del chatbot
- fare rasa train
- avviare rasa con rasa run --enable-api --cors="*"
- in un'altra finestra del terminale, sempre andando nella directory del chatbot, avviare il file rsCode.py 
- in un'altra finestra del terminale avviare le actions con rasa run actions (sempre nella directory del chatbot)
- attendere 60 secondi dall'avvio del file rsCode
- il chatbot si trova alla pagina  127.0.0.1/frontpage 


## Utilizzo del RS
Si puó modificare la linea 119 di rsCode.py cambiando numero nella funzione head per avere piú o meno raccomandazioni
