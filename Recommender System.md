# Recommender System
### Query, dataset e filtri
Il RecSys utilizza un oggetto JSON del tipo :
{
    "request_type": "",
    "user-id":"",
    "duration": "",
    "discipline": "",
    "language": "",
    "public": "",
    "remove":"",
    "type": "",
    "keywords": []
}
Per effettuare le raccomandazioni.
Inizialmente il dataset (per ora viene usato il dataset merlot.csv con 1800 campi) viene filtrato con un filtro "duro" per la lingua e per la tipologia di risorsa didattica attraverso i campi "type" e "language". Il sistema non proporrá una risorsa italiana di tipo esercizio se sono state chieste risorse inglesi di tipo videolezione.
### CosineSimilarity
Il meccanismo di raccomandazione poi si basa su dei word embedding generati con un architettura a transformer: BERT.
Per ogni record del dataset i campi "discipline", "keywords" e "duration" vengono trasformati in embedding con BERT e convertiti a tensore. I tensori di ogni record vengono inseriti in un dataframe che avrá gli stessi indici del dataframe creato col dataset completo (Si avrá una corrispondenza di posizione tra gli oggetti "leggibili" e i relativi embedding). 
Una volta ricevuta la user query i campi corrispondenti vengono convertiti in embedding e poi inseriti in un tensore.
Per ogni metadato cercato per ogni record del dataset viene calcolata la CosineSimilarity  fra il tensore della user query e il tensore del record, lo score risultante viene inserito in un dataframe. Infine viene calcolato uno SCORE finale usando la media degli score dei singoli metadati per ogni record. Le risorse vengono raccomandate all'utente in base allo SCORE

# Parser dei metadati
### Preparazione del dataset
Partendo dal dataset utilizzato vengono presi per ogni metadato i singoli valori unici. Questi metadati vengono poi convertiti in embedding con BERT, vengono poi salvati successivamente come tensore, l'operazione é abbastanza lunga, quindi dopo aver creato gli embedding la prima volta vengono caricati i tensori. Al cambio del dataset vanno quindi ricreati da zero.
Vengono creati dai singoli valori unici anche dei file.txt (corpus) per avere un riferimento non embedding del valore risultante alla fine del processo

### Parsing
Una volta arrivato il messaggio dell'utente riguardo allo specifico metadato (es. disciplina = Matematica), viene controllato e corretto lo spelling, viene tradotto in inglese (in quanto i metadati nel dataset sono in inglese) e viene convertito in embedding e inserito in un tensore. Il tensore user viene confrontato con il tensore corrispondente dei metadati attraverso la funzione semantic_search della libreria SentenceTransformers, la funzione si basa sulla CosineSimilarity. Il risultato sono i K indici piú simili, sia lessicalmente che semanticamente alla parola inserita dall'utente. Passando gli indici nella lista generata con il corpus ottengo poi la parola esistente nel dataset.

#### Esempio:
1) usermsg(discplina = ecnoomia)
2) speller ecnoomia --> economia
3) translate economia --> economics
4) embedding economia --> tensore_utente
5) semantic_search(tensore_utente, tensore_corpus, topk=3) --> 1, 723, 223
6) corpus[1], corpus[723], corpus[223] --> Economics, Finance, Banking
