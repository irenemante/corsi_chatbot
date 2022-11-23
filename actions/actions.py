# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from typing import Any, Text, Dict, List
#
from rasa_sdk import Action, Tracker
from rasa_sdk.events import FollowupAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk import Action
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet
from deep_translator import GoogleTranslator
from autocorrect import Speller
from sentence_transformers import SentenceTransformer, util
import re
import os
import torch
import time
import json
import requests

global LODict
LODict = {
    "videolezioni" : {},
    "esercizi" : {},
    "quiz" : {},
    "documenti" : {},
}

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)




class ValidateRipetizioneEserciziForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_ripetizione_esercizi_form"


    def validate_vuole_ripetizione(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
   
        
        if tracker.get_intent_of_latest_message() == "conferma":
            
            return {"vuole_ripetizione": True}
        else:
            SlotSet("vuole_ripetizione",False)
            
            return {"requested_slot": None}

        return {"vuole_ripetizione": None}
        

    def validate_tempo(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
        valore = tracker.get_slot("vuole_ripetizione")
        print(valore)
        minuti_number = re.findall('[0-9]+', slot_value)
        if valore:
            if not has_numbers(slot_value) and tracker.get_intent_of_latest_message() != "stop_form":
                return {"tempo":None}
            elif tracker.get_intent_of_latest_message() == "stop_form" and not has_numbers(slot_value):
                    return {"requested_slot": None,"tempo": None}
            else:
                minuti_number = re.findall('[0-9]+', slot_value)
                return {"tempo": int(minuti_number[0])}
            
        else:
                return {"tempo": None}

class ValidateCreazioneCorsoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_creazione_corso_form"


    def validate_nome_corso(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        
        if tracker.get_intent_of_latest_message()== "stop_form":
            return {"nome_corso": None, "requested_slot":None}
        else:
            
            return {"nome_corso": slot_value}

        

    def validate_età(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
      
        if not has_numbers(slot_value) and tracker.get_intent_of_latest_message() != "stop_form":
            return {"età":None}
        
        elif tracker.get_intent_of_latest_message() == "stop_form" and  not has_numbers(slot_value):
            return {"requested_slot": None,"età": None}
        else:
            età_number = re.findall('[0-9]+', slot_value)
            if  int(età_number[0]) >=100 :
                return {"età": None}
            else:    
                return {"età": int(età_number[0])}
    
    def validate_numero_lezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:

        if not has_numbers(slot_value) and tracker.get_intent_of_latest_message() != "stop_form":
            return {"numero_lezioni":None}
        elif tracker.get_intent_of_latest_message() == "stop_form" and not has_numbers(slot_value):
                return {"requested_slot": None,"numero_lezioni": None}
        else:
                lezioni_number = re.findall('[0-9]+', slot_value)
                return {"numero_lezioni": int(lezioni_number[0])}
    
    def validate_durata_lezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
        if tracker.get_intent_of_latest_message() == "stop_form":
            
            return {"requested_slot": None,"durata_lezioni": None}
        else:
            
            return {"durata_lezioni": slot_value}

    def validate_disciplina(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"disciplina":None}
        else:
            
            return {"disciplina": slot_value}
    
    def validate_lingua(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"lingua": None}
        else:
            dispatcher.utter_message(text="Indica gli argomenti del corso, separati dalla virgola.")
            return {"lingua": slot_value}


    def validate_argomenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("arg " + tracker.get_intent_of_latest_message())
        lista_argomenti = slot_value.split(',')
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"argomenti": None}
        else:
            dispatcher.utter_message(text="Vuoi aggiungere altri argomenti?")
            return {"argomenti": lista_argomenti}
       


    def validate_vuole_altri_argomenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("arg " + tracker.get_intent_of_latest_message())
        argomenti = tracker.get_slot("argomenti")
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="Indica gli altri arogmenti del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altri_argomenti":None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            dispatcher.utter_message(text="Indica le abilità iniziali che lo studente deve avere prima del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altri argomenti?")
            new_argomenti = slot_value.split(',')
            new_argomenti= argomenti + new_argomenti
            return {"argomenti": new_argomenti, "vuole_altri_argomenti":None}
       
        
        
            
        
    def validate_abilità(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("ab " + tracker.get_intent_of_latest_message())
        lista_abilità = slot_value.split(',')
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"abilità": None}
        else:
            dispatcher.utter_message(text="Vuoi aggiungere altre abilità?")
            return {"abilità": lista_abilità}
        


    def validate_vuole_altre_abilità(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("ab " + tracker.get_intent_of_latest_message())
        abilità = tracker.get_slot("abilità")
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="Indica le altre abilità iniziali del corso, separate dalla virgola.")
            return {"vuole_altre_abilità": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altre_abilità":None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            dispatcher.utter_message(text="Indica le competenze che lo studente deve raggiungere alla fine del corso, separate dalla virgola.")
            return {"vuole_altre_abilità": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altre abilità?")
            new_abilità = slot_value.split(',')
            new_abilità= abilità + new_abilità
            return {"abilità": new_abilità, "vuole_altre_abilità":None}
            
            

        


    def validate_competenze(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("comp " + tracker.get_intent_of_latest_message())
        lista_competenze = slot_value.split(',')
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"competenze": None}
        else:
            dispatcher.utter_message(text="Vuoi aggiungere altre competenze?")
            return {"competenze": lista_competenze}
       

    def validate_vuole_altre_competenze(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("comp " + tracker.get_intent_of_latest_message())
        competenze = tracker.get_slot("competenze")
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="Indica le altre competenze che lo studente deve raggiungere  alla fine del corso, separate dalla virgola.")
            return {"vuole_altre_competenze": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altre_competenze":None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            return {"vuole_altre_competenze": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altre competenze?")
            new_competenze = slot_value.split(',')
            new_competenze= competenze + new_competenze
            return {"competenze": new_competenze, "vuole_altre_competenze":None}
            
            

        
        

 

class ValidatePropostaLinkForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_proposta_link_form"
    
    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:
       
        new_list=[]
        lista_formati= tracker.slots.get("formati")
        if type(lista_formati) == list:
            for i in lista_formati:
                new_list.append(i)
                new_list.append(f"aggiunta_{i}")  
            return   domain_slots + new_list
        else:
            return  domain_slots
       
    def validate_formati(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
        formati=tracker.slots.get("formati")
        formati_num = re.findall('[0-9]+', formati)
        mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
        formati_list= []
        formati_num= list(map(int, formati_num))
        print(formati_num)
        for i in formati_num:
            formati_list.append(mapping.get(i))
        for j in formati_num:
            if j<1 or j>4:
                return {"formati":None}
            
        dispatcher.utter_message(text=create_responses("formati",tracker, dispatcher))
        return {"formati": formati_list}
        

    

    def validate_videolezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
       
        videlezioni_num = re.findall('[0-9]+', slot_value)
        dispatcher.utter_message(text="desideri aggiungere altre videolezioni?")
        return {"videolezioni": videlezioni_num}
    
    def validate_aggiunta_videolezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        formati= tracker.slots.get("formati")
        
        print(slot_value)
        videolezioni=tracker.slots.get("videolezioni")
        altre_vid_num = re.findall('[0-9]+', slot_value)
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="indica altre videolezioni")
            return {"aggiunta_videolezioni": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            if formati[len(formati)-1] != "videolezioni":
                dispatcher.utter_message(text=create_responses("videolezioni",tracker,dispatcher))
            return {"aggiunta_videolezioni": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altre videolezioni?")
            return {"videolezioni": videolezioni + altre_vid_num, "aggiunta_videolezioni":None}
    
    
            
       

    
    def validate_esercizi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
      
        esercizi_num = re.findall('[0-9]+', slot_value)
        dispatcher.utter_message(text="vuoi che ti proponga altri esercizi?")
        return {"esercizi": esercizi_num}
    
    def validate_aggiunta_esercizi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        formati= tracker.slots.get("formati")
        
        print(slot_value)
        esercizi=tracker.slots.get("esercizi")
        altri_es_num = re.findall('[0-9]+', slot_value)
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="indica altri esercizi")
            return {"aggiunta_esercizi": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            if formati[len(formati)-1] != "esercizi":
                dispatcher.utter_message(text=create_responses("esercizi",tracker,dispatcher))
            return {"aggiunta_esercizi": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altri esercizi?")
            return {"esercizi": esercizi + altri_es_num, "aggiunta_esercizi":None}
    
    
    
    def validate_quiz(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
       
        quiz_num = re.findall('[0-9]+', slot_value)
        dispatcher.utter_message(text="vuoi che ti proponga altri quiz?")
        return {"quiz": quiz_num}
    
    
    
    def validate_aggiunta_quiz(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        formati= tracker.slots.get("formati")
        
        print(slot_value)
        quiz=tracker.slots.get("quiz")
        altri_quiz_num = re.findall('[0-9]+', slot_value)
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="indica altri quiz")
            return {"aggiunta_quiz": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            if formati[len(formati)-1] != "quiz":
                dispatcher.utter_message(text=create_responses("quiz",tracker , dispatcher))
            return {"aggiunta_quiz": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altri quiz?")
            return {"quiz": quiz + altri_quiz_num, "aggiunta_quiz": None}
    
    def validate_documenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
        
        mat_num = re.findall('[0-9]+', slot_value)
        dispatcher.utter_message(text="vuoi che ti proponga altri docuementi?")
        return {"documenti": mat_num}
    
    def validate_aggiunta_documenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        formati= tracker.slots.get("formati")
        
        print(slot_value)
        documenti=tracker.slots.get("documenti")
        altri_doc_num = re.findall('[0-9]+', slot_value)
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="indica altri documenti")
            return {"aggiunta_documenti": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            if formati[len(formati)-1] != "documenti":
                dispatcher.utter_message(text=create_responses("documenti",tracker, dispatcher))
            return {"aggiunta_documenti": False}

        else:
            dispatcher.utter_message(text="desideri aggiungere altri documenti?")
            return {"documenti": documenti + altri_doc_num, "aggiunta_documenti": None}
    
    
    

def create_responses (slot, tracker: Tracker, dispatcher: CollectingDispatcher):
    mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
    next_slot= None
    formati= tracker.slots.get("formati")
    request = tracker.get_slot("recommend_query")
    if slot=="formati":
        
        #RECOMMENDER LOGIC

        needs_removing = tracker.get_slot(f"aggiunta_{mapping.get(int(formati[0]))}")
        request["type"] = mapping.get(int(formati[0]))
        request["remove"] = needs_removing
        request["public"] = ""
        print(request)
        response = requests.post('http://127.0.0.1:8080/recommend', json = request)
        parsed = json.loads(response.content)
        dispatcher.utter_message(f"Ora ti indicherò dei link a siti contenenti {mapping.get(int(formati[0]))}.")
        text_to_save = ""
        for i in range(len(parsed)):
            text_to_save += f'Titolo: {parsed[i][0]} \nLink {parsed[i][1]} \n'
            message = f'-{i}) Titolo: {parsed[i][0]},\nLink: {parsed[i][1]}'
            dispatcher.utter_message(text=message, image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQx1qo4tI97ysuUutaDvHlmYzABdgLYQejIwybA83k&s")
            LODict[mapping.get(int(formati[0]))][i] = [parsed[i][0], parsed[i][1]]
        SlotSet(f"{mapping.get(int(formati[0]))}", text_to_save)
        return (f"Indica il numero di quelli che desideri. ")
    else:
        for i in range(len(formati)):
            if formati[i]==slot and i < len(formati)-1:
                next_slot= formati[i+1]
            elif formati[i]==slot and i == len(formati)-1:
                next_slot = None
            

        #RECOMMENDER LOGIC

        needs_removing = tracker.get_slot(f"aggiunta_{next_slot}")
        request["type"] = next_slot
        request["remove"] = needs_removing
        request["public"] = ""
        response = requests.post('http://127.0.0.1:8080/recommend', json = request)
        parsed = json.loads(response.content)
        dispatcher.utter_message(f"Ora ti indicherò dei link a siti contenenti {next_slot}.")
        text_to_save = ""
        for i in range(len(parsed)):
            text_to_save += f'Titolo: {parsed[i][0]} \nLink {parsed[i][1]} \n'
            message = f'-{i}) Titolo: {parsed[i][0]},\nLink: {parsed[i][1]}'
            dispatcher.utter_message(text=message, image="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQx1qo4tI97ysuUutaDvHlmYzABdgLYQejIwybA83k&s")
            LODict[next_slot][i] = [parsed[i][0], parsed[i][1]]
        SlotSet(f"{next_slot}", text_to_save)
        return (f"Indica il numero di quelli che desideri.")


class ActionParseAll(Action):

    def name(self) -> Text:
        return "action_parse_all"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        #Step 1: for all slots get the value, spell it and translate it, save to a dict nomemetadato:metadato
        #Step 2: iterate over the dict keys and parse
        #Step 3: add every parsed result to a Json called request.json and send it to the recsys, save it locally
        
        #instantiate speller, translator and embedder
        spell = Speller('it')
        translator = GoogleTranslator(source = "auto", target='en')
        embedder = SentenceTransformer('all-MiniLM-L6-v2')


        #define the json that's going to be sent to RecSys
        request = {
            "request_type": "recommend",
            "user_id": tracker.sender_id,
        }

        #Get all slot values
        slotdict = {
            "Durata": "",
            "Età": "",
            "Keywords": "",
        }



        #Map slots to a dictionary
        slotdict["Durata"] = spell(str(tracker.get_slot("durata_lezioni")))
        slotdict["Età"] = spell(str(tracker.get_slot("età")))
        slotdict["Keywords"] = translator.translate(spell(str(tracker.get_slot("argomenti"))))
        
        #iterate over slots and parse
        for key in slotdict:
            #save the queries in a list
            total_kw_list = []
            queries = slotdict[key].split(", ")
            dir = os.getcwd()
            #create the embeddings of all the possible values in MERLOT
            file = open(f'Dataset/{key}.txt')
            list = file.read().splitlines()
            corpus = list

            #load a pre made tensor for the embeddings
            corpus_embeddings = torch.load(f'\\Tensors\\code_{key}_tensor.pt')

            #define the number of responses(needs to be tweaked accordingly)
            top_k = min(5, len(corpus))

            #calculate semantic similarities
            for query in queries:
                query_embedding = embedder.encode(query, convert_to_tensor=True)
                hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
                hits = hits[0]
                print("Query: "+ query)
                #insert the hits into the Json
                if key != "Keywords":
                    hit = hits[0]
                    item_to_append = {key: corpus[hit["corpus_id"]]}
                    request.update(item_to_append)
                #keyword is a multi field and dictionaries cant have multiple objects with the same key
                #so the top hit for every keyword is saved to a list and later put into the json
                else:
                    total_kw_list.append(corpus[hits[0]["corpus_id"]])
                for hit in hits:
                    print(corpus[hit['corpus_id']], "(Score: {:.4f})".format(hit['score']))
                print("==============================")
            if key == "Keywords":
                keyword_item = {key: total_kw_list}
                print("TotalKwLisis")
                print(total_kw_list)
                request.update(keyword_item)
                print("requestis")
                print(request)

            #placeholder print,, not needed in production
            request["Età"] = tracker.get_slot('età')
            request["Lingua"] = "Inglese"
            print(json.dumps(request))

        return [SlotSet("recommend_query", request)]


class ActionUserSelection(Action):
    def name(self) -> Text:
        return "action_user_selection"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any])-> List[Dict[Text,Any]]:
        formati = tracker.get_slot("formati")
        videolezionislot = None
        esercizislot = None
        quizslot = None
        documentislot = None
        if tracker.get_slot("videolezioni") != None : videolezionislot = list(tracker.get_slot("videolezioni"))
        print("videloeizioni slot = ")
        print(videolezionislot)
        if tracker.get_slot("esercizi") != None : esercizislot = list(tracker.get_slot("esercizi"))
        if tracker.get_slot("documenti") != None : documentislot = list(tracker.get_slot("documenti"))
        if tracker.get_slot("quiz") != None : quizslot = list(tracker.get_slot("quiz"))
        string = "I link che hai scelto sono: \n"
        # for every value in every slot search in the dict concat to a message and utter
        if videolezionislot != None :
            string += "Videolezioni:\n"
            for i in videolezionislot:
                i = str(i).split()
                i = int(i[0])
                string += f'Titolo: {LODict["videolezioni"][i][0]}\n Link: {LODict["videolezioni"][i][1]}'
        if esercizislot != None :
            string += "Esercizi: \n"
            for i in esercizislot:
                i = str(i).split()
                i = int(i[0])
                string += f'Titolo: {LODict["esercizi"][i][0]}\n Link: {LODict["esercizi"][i][1]}'
        if quizslot != None :
            string += "Quiz: \n"
            for i in quizslot:
                i = str(i).split()
                i = int(i[0])
                string += f'Titolo: {LODict["quiz"][i][0]}\n Link: {LODict["quiz"][i][1]}'
        if documentislot != None :
            string += "Documenti: \n"
            for i in documentislot:
                i = str(i).split()
                i = int(i[0])                
                string += f'Titolo: {LODict["documenti"][i][0]}\n Link: {LODict["documenti"][i][1]}'
        dispatcher.utter_message(string)
        return[]





# class ActionRecommendLezioni(Action):
#     def name(self) -> Text:
#         return "action_recommend_lezioni"

#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#         #recommend with the locally saved JSON
#         #prendere lo slot che chiede se vuole altri esercizi/quiz ecc, aggiunge il parametro remove
#         choosen_formats = tracker.get_slot("formati")
#         numbers = [int(x) for x in choosen_formats.split() if x.isdigit()]
#         mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
#         mapped_list = []
#         #crea una lista di parole dei formati scelti e itera su quelle
#         for i in range(numbers):
#             mapped_list.append(mapping[numbers[i]])
#         #itera sulla lista di formati scelti (da gestire il formato nel recommender system)
#         for format in mapped_list:

#             request = tracker.get_slot("recommend_query")
#             needs_removing = tracker.get_slot(f"aggiunta_{format}")
#             request["type"] = format
#             request["remove"] = needs_removing
#             response = requests.post('http://127.0.0.1:8080/recommend', json = request)
#             parsed = json.loads(response.content)
#             dispatcher.utter_message("Eccoi i link che vorrei proporti")
#             text_to_save = ""
#             for i in range(len(parsed)):
#                 text_to_save += f'Titolo: {parsed[i][0]} \nLink {parsed[i][1]} \n'
#                 dispatcher.utter_message(f'Titolo: {parsed[i][0]},\nLink{parsed[i][1]}')
#             SlotSet(f"{format}", text_to_save)
#         return
  
        
        
       





   

