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
import torch
import time
import json
import requests

proposed_link_size= {"videolezioni": None, "esercizi":None, "quiz":None, "documenti":None}

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def has_duplicates(seq):
    return len(seq) != len(set(seq))





class ValidateRipetizioneEserciziForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_ripetizione_esercizi_form"
    
    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Text]:
       
       
        lista_formati= tracker.slots.get("formati")
        if "esercizi" not in lista_formati:
            return []
        else:
            return  domain_slots


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
                if  int(minuti_number[0])<1 or int(minuti_number[0]) >=60 :
                    return {"tempo": None}
                else:    
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
        regex = re.compile('[@_#$%^&*<>\|}{~]')
        if(re.search(regex,slot_value) == None):
            return {"nome_corso": slot_value}
        else:
            return {"nome_corso": None}

        

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
            if int(età_number[0])<1 or int(età_number[0]) >=100 :
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
                if  int(lezioni_number[0])<1 or int(lezioni_number[0]) >100 :
                    return {"numero_lezioni": None}
                else: 
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
        elif slot_value not in ["0-30","30-60","60-90","90-120","120"]:
            
            return {"durata_lezioni": None}
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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                return {"disciplina": None}
            else:
                dispatcher.utter_message(text="Indica gli argomenti del corso, separati dalla virgola.")
                return {"disciplina": slot_value}
    
    def validate_lingua(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        lingue= ["italiano", "inglese", "francese", "tedesco", "cinese", "spagnolo", "giapponese","russo", "portoghese","arabo"]
        spell = Speller('it')
        lingua=spell(slot_value)
        if lingua in lingue:
            return {"lingua": lingua.lower()}
        else:
            return {"lingua": None}

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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica gli argomenti del corso, separati dalla virgola.")
                return {"argomenti": None}
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
            dispatcher.utter_message(text="Indica gli altri argomenti del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altri_argomenti":None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            dispatcher.utter_message(text="Indica le abilità iniziali che lo studente deve avere prima del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": False}

        else:
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica gli altri argomenti del corso, separati dalla virgola.")
                return{"vuole_altri_argomenti":None}
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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le abilità iniziali che lo studente deve avere prima del corso, separati dalla virgola.")
                return{"abilità":None}
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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le altre abilità iniziali del corso, separate dalla virgola.")
                return{"vuole_altre_abilità":None}
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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le competenze che lo studente deve raggiungere alla fine del corso, separate dalla virgola.")
                return{"competenze":None}
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
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le altre competenze che lo studente deve raggiungere  alla fine del corso, separate dalla virgola.")
                return{"vuole_altre_competenze":None}
            else:
                dispatcher.utter_message(text="desideri aggiungere altre competenze?")
                new_competenze = slot_value.split(',')
                new_competenze= competenze + new_competenze
                return {"competenze": new_competenze, "vuole_altre_competenze":None}
            
            

        
class ValidateModificaMetadati(FormValidationAction):
    def name(self) -> Text:
        return "validate_modifica_metadati_form"
  
    


    def validate_vuole_modifica(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        
        if slot_value:
            
            return {"vuole_modifica": True}
        else:
            
            return {"vuole_modifica": False, "requested_slot":None}
        

    def validate_metadato_da_modificare (
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        
        if slot_value == "durata_lezioni":
            dispatcher.utter_message(response="utter_ask_durata_lezioni")
        elif slot_value in ["argomenti","abilità","competenze"]:
            response= "Inserisci  {pronome} {aggettivo} {metadato}, {separazione} dalla virgola.".format(pronome="i" if slot_value == "argomenti" else "le",aggettivo="nuovi" if slot_value == "argomenti" else "nuove",metadato=slot_value,separazione="separati" if slot_value == "argomenti" else "separate" )
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo {slot_value}")
        return {"metadato_da_modificare": slot_value}
       
    
    def validate_cambio_metadato (
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        
        metadato= tracker.slots.get("metadato_da_modificare")
        if metadato == "abilità" or metadato == "competenze" or metadato == "argomenti":
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            lista_elementi = slot_value.split(',')
            if(re.search(regex,slot_value) != None):
                response= "Inserisci  {pronome} {aggettivo} {metadato}, {separazione} dalla virgola.".format(pronome="i" if metadato == "argomenti" else "le",aggettivo="nuovi" if metadato == "argomenti" else "nuove",metadato=metadato,separazione="separati" if metadato == "argomenti" else "separate" )
                dispatcher.utter_message(text=response)
                return {"cambio_metadato": None}
            else:
                return {f"{metadato}": lista_elementi}
        elif metadato=="età" or metadato=="numero_lezioni":
            numero = re.findall('[0-9]+', slot_value)
            if int(numero[0]) <1 or  int(numero[0]) >=100 :
                dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo {metadato}")
                return {"cambio_metadato": None}
            else:    
                return {f"{metadato}": int(numero[0])}
        elif metadato== "lingua":
            lingue= ["italiano", "inglese", "francese", "tedesco", "cinese", "spagnolo", "giapponese","russo", "portoghese","arabo"]
            spell = Speller('it')
            lingua=spell(slot_value.lower())
            if lingua in lingue:
                return {"lingua": lingua}
            else:
                dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo lingua")
                return {"cambio_metadato": None}
        elif metadato in ["nome_corso","disciplina"]:
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo {metadato}")
                return {"cambio_metadato": None}
            else:
                return  {f"{metadato}": slot_value}
        else:
            return {f"{metadato}": slot_value}
    
    def validate_vuole_modifica_altro(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
   
        
        if slot_value :
            
            return {"vuole_modifica_altro": None,  "cambio_metadato":None, "metadato_da_modificare":None}
        else:
            
            return {"vuole_modifica_altro": False, "requested_slot":None}

 

class ValidatePropostaLinkForm(FormValidationAction):
    controller_videolezioni=None
    controller_esercizi=None
    controller_quiz=None
    controller_documenti=None
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
     
        if not has_numbers(slot_value) or slot_value==" ":
            formati_list=["videolezioni","esercizi","quiz","documenti"]
            msg,num= create_responses("formati",tracker, dispatcher)
            dispatcher.utter_message(text=msg)
            proposed_link_size[f"{formati_list[0]}"]= num
            return {"formati":formati_list}
        else:
            formati_num = re.findall('[0-9]+', slot_value)
            mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
            formati_list= []
            formati_num= list(map(int, formati_num))
            print(formati_num)
            if not(all(i>0 and i<=4 for i in formati_num)) or has_duplicates(formati_num):
                    return {"formati":None}
            for i in formati_num:
                formati_list.append(mapping.get(i))
            msg,num= create_responses("formati",tracker, dispatcher)
            dispatcher.utter_message(text=msg)
            proposed_link_size[f"{formati_list[0]}"]= num
            print(proposed_link_size)
            return {"formati": formati_list}
        

    

    def validate_videolezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
        if not has_numbers(slot_value):
            dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
            return {"videolezioni":None}
        else:
            videolezioni_num = re.findall('[0-9]+', slot_value)
            videolezioni_num= list(map(int, videolezioni_num))
            if not(all(i<proposed_link_size["videolezioni"] for i in videolezioni_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"videolezioni":None}
            dispatcher.utter_message(text="desideri aggiungere altre videolezioni?")
            return {"videolezioni": videolezioni_num}
    
    def validate_aggiunta_videolezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_videolezioni
        formati= tracker.slots.get("formati")
        previous_slot=tracker.slots.get("aggiunta_videolezioni")
        print(previous_slot)
        next_slot = None
        for i in range(len(formati)):
            if formati[i]=="videolezioni" and i < len(formati)-1:
                next_slot= formati[i+1]
            elif formati[i]=="videolezioni" and i == len(formati)-1:
                next_slot = None
        print(slot_value)
        videolezioni=tracker.slots.get("videolezioni")
        altre_vid_num = re.findall('[0-9]+', slot_value)
        altre_vid_num= list(map(int, altre_vid_num))
        if tracker.get_intent_of_latest_message() == "conferma":
            dispatcher.utter_message(text="indica altre videolezioni")
            controller_videolezioni=False
            return {"aggiunta_videolezioni": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            controller_videolezioni=False
            if formati[len(formati)-1] != "videolezioni":
                msg,num = create_responses("videolezioni",tracker,dispatcher)
                dispatcher.utter_message(text=msg)
                proposed_link_size[f"{next_slot}"]=num
            return {"aggiunta_videolezioni": False}
        else:
            if (not has_numbers(slot_value) or not(all(i<proposed_link_size["videolezioni"] for i in altre_vid_num))) and controller_videolezioni==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_videolezioni":None}
            else:
                controller_videolezioni=True
                dispatcher.utter_message(text="desideri aggiungere altre videolezioni?")
                videolezioni_totale=videolezioni + altre_vid_num
                videolezioni_totale= list(dict.fromkeys(videolezioni_totale))
                return {"videolezioni": videolezioni_totale, "aggiunta_videolezioni":None}
    
    
            
       

    
    def validate_esercizi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        if not has_numbers(slot_value) :
            dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
            return {"esercizi":None}
        else:
            esercizi_num = re.findall('[0-9]+', slot_value)
            esercizi_num= list(map(int, esercizi_num))
            if not(all(i<proposed_link_size["esercizi"] for i in esercizi_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"esercizi":None}
            dispatcher.utter_message(text="vuoi aggiungere altri esercizi?")
            return {"esercizi": esercizi_num}
    
    def validate_aggiunta_esercizi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_esercizi
        formati= tracker.slots.get("formati")
        next_slot = None
        for i in range(len(formati)):
            if formati[i]=="esercizi" and i < len(formati)-1:
                next_slot= formati[i+1]
            elif formati[i]=="esercizi" and i == len(formati)-1:
                next_slot = None
        print(slot_value)
        esercizi=tracker.slots.get("esercizi")
        altri_es_num = re.findall('[0-9]+', slot_value)
        altri_es_num= list(map(int, altri_es_num))
        if tracker.get_intent_of_latest_message() == "conferma":
            controller_esercizi=False
            dispatcher.utter_message(text="indica altri esercizi")
            return {"aggiunta_esercizi": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            controller_esercizi=False
            if formati[len(formati)-1] != "esercizi":
                msg,num= create_responses("esercizi",tracker,dispatcher)
                dispatcher.utter_message(text=msg)
                proposed_link_size[f"{next_slot}"]=num
            return {"aggiunta_esercizi": False}

        else:
            if (not has_numbers(slot_value) or not(all(i<proposed_link_size["esercizi"] for i in altri_es_num))) and controller_esercizi==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_esercizi":None}
            else:
                controller_esercizi=True
                dispatcher.utter_message(text="desideri aggiungere altri esercizi?")
                esercizi_totale=esercizi + altri_es_num
                esercizi_totale= list(dict.fromkeys(esercizi_totale))
                return {"esercizi": esercizi_totale, "aggiunta_esercizi":None}
    
    
    
    def validate_quiz(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
        if not has_numbers(slot_value) :
            dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
            return {"quiz":None}
        else:
            quiz_num = re.findall('[0-9]+', slot_value)
            quiz_num= list(map(int, quiz_num))
            if not(all(i<proposed_link_size["quiz"] for i in quiz_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"quiz":None}
            dispatcher.utter_message(text="vuoi aggiungere altri quiz?")
            return {"quiz": quiz_num}
    
    
    
    def validate_aggiunta_quiz(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_quiz
        formati= tracker.slots.get("formati")
        next_slot = None
        for i in range(len(formati)):
            if formati[i]=="quiz" and i < len(formati)-1:
                next_slot= formati[i+1]
            elif formati[i]=="quiz" and i == len(formati)-1:
                next_slot = None
        print(slot_value)
        quiz=tracker.slots.get("quiz")
        altri_quiz_num = re.findall('[0-9]+', slot_value)
        altri_quiz_num= list(map(int, altri_quiz_num))
        if tracker.get_intent_of_latest_message() == "conferma":
            controller_quiz=False
            dispatcher.utter_message(text="indica altri quiz")
            return {"aggiunta_quiz": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            controller_quiz=False
            if formati[len(formati)-1] != "quiz":
                msg,num=create_responses("quiz",tracker , dispatcher)
                dispatcher.utter_message(text=msg)
                proposed_link_size[f"{next_slot}"]=num
            return {"aggiunta_quiz": False}

        else:
            if (not has_numbers(slot_value) or not(all(i<proposed_link_size["quiz"] for i in altri_quiz_num))) and controller_quiz==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_quiz":None}
            else:
                controller_quiz=True
                dispatcher.utter_message(text="desideri aggiungere altri quiz?")
                quiz_totale=quiz + altri_quiz_num
                quiz_totale= list(dict.fromkeys(quiz_totale))
                return {"quiz": quiz_totale, "aggiunta_quiz": None}
    
    def validate_documenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
        if not has_numbers(slot_value) :
            dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
            return {"documenti":None}
        else:
            mat_num = re.findall('[0-9]+', slot_value)
            mat_num= list(map(int, mat_num))
            if not(all(i<proposed_link_size["documenti"] for i in mat_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"documenti":None}
            dispatcher.utter_message(text="vuoi aggiungere altri docuementi?")
            return {"documenti": mat_num}
    
    def validate_aggiunta_documenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_documenti
        formati= tracker.slots.get("formati")
        next_slot = None
        for i in range(len(formati)):
            if formati[i]=="documenti" and i < len(formati)-1:
                next_slot= formati[i+1]
            elif formati[i]=="documente" and i == len(formati)-1:
                next_slot = None
        print(slot_value)
        documenti=tracker.slots.get("documenti")
        altri_doc_num = re.findall('[0-9]+', slot_value)
        altri_doc_num= list(map(int, altri_doc_num))
        if tracker.get_intent_of_latest_message() == "conferma":
            controller_documenti=False
            dispatcher.utter_message(text="indica altri documenti")
            return {"aggiunta_documenti": None}

        elif tracker.get_intent_of_latest_message() == "negazione":
            controller_documenti=False
            if formati[len(formati)-1] != "documenti":
                msg,num=create_responses("quiz",tracker , dispatcher)
                dispatcher.utter_message(text=msg)
                proposed_link_size[f"{next_slot}"]=num
            return {"aggiunta_documenti": False}

        else:
            if (not has_numbers(slot_value) or not(all(i<proposed_link_size["documenti"] for i in altri_doc_num))) and controller_documenti==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_documenti":None}
            else:
                controller_documenti=True
                dispatcher.utter_message(text="desideri aggiungere altri documenti?")
                documenti_totale=documenti + altri_doc_num
                documenti_totale= list(dict.fromkeys(documenti_totale))
                return {"documenti": documenti_totale, "aggiunta_documenti": None}
    
    
    

def create_responses (slot, tracker: Tracker, dispatcher: CollectingDispatcher):
    mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
    next_slot= None
    formati= tracker.slots.get("formati")
    request = tracker.get_slot("recommend_query")
    if slot=="formati":
        
        #RECOMMENDER LOGIC
        if not has_numbers(formati) or formati==" ":
            formati=['1','2','3','4']
        
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
            dispatcher.utter_message(f'-{i}) Titolo: {parsed[i][0]},\nLink{parsed[i][1]}')
        SlotSet(f"{mapping.get(int(formati[0]))}", text_to_save)
        return (f"Indica il numero di quelli che desideri. ", len(parsed))
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
            dispatcher.utter_message(f'-{i}) Titolo: {parsed[i][0]},\nLink{parsed[i][1]}')
        SlotSet(f"{next_slot}", text_to_save)
        return (f"Indica il numero di quelli che desideri.", len(parsed))


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
            "duration": "",
            "discipline": "",
            "language": "",
            "keywords": "",
        }

        #Map slots to a dictionary
        slotdict["duration"] = translator.translate(spell(str(tracker.get_slot("durata_lezioni"))))
        slotdict["discipline"] = translator.translate(spell(str(tracker.get_slot("disciplina"))))
        slotdict["language"] = translator.translate(spell(str(tracker.get_slot("lingua"))))
        slotdict["keywords"] = translator.translate(spell(str(tracker.get_slot("argomenti"))))
        
        #iterate over slots and parse
        for key in slotdict:
            #save the queries in a list
            total_kw_list = []
            queries = slotdict[key].split(", ")

            #create the embeddings of all the possible values in MERLOT
            file = open(f'merlotclean/{key}.txt')
            list = file.read().splitlines()
            corpus = list

            #load a pre made tensor for the embeddings
            corpus_embeddings = torch.load(f'tensors/{key}tensor.pt')

            #define the number of responses(needs to be tweaked accordingly)
            top_k = min(5, len(corpus))

            #calculate semantic similarities
            for query in queries:
                query_embedding = embedder.encode(query, convert_to_tensor=True)
                hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
                hits = hits[0]
                print("Query: "+ query)
                #insert the hits into the Json
                if key != "keywords":
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
            if key == "keywords":
                keyword_item = {key: total_kw_list}
                request.update(keyword_item)

            #placeholder print,, not needed in production
            print(json.dumps(request))

        return [SlotSet("recommend_query", request)]

