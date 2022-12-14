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

proposed_link_size= {"videolezioni": None, "esercizi":None, "quiz":None, "documenti":None}
lista_formati_generale= []

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

def has_duplicates(seq):
    return len(seq) != len(set(seq))

def eliminate_introduction_slots(lista, slot,dispatcher:CollectingDispatcher):
    if "sono" in lista[0] and not ":" in lista[0]:
        a = re.search(r'\b(sono)\b', lista[0])
        lista[0]=lista[0][a.start()+4+1:]
        if slot!="cambio":
            dispatcher.utter_message(
            text="vuoi aggiungere {aggettivo} {slot}? Clicca su si o no.".format(aggettivo="altri" if slot == "argomenti" else "altre",slot=slot),
            buttons= [{"title":"si","payload":"si"},
                {"title":"no","payload":"no"}
            ])
        return  lista
    elif ":" in lista[0]:
        lista[0]=lista[0].split(':')[1].strip()
        if slot!="cambio":
            dispatcher.utter_message(
            text="vuoi aggiungere {aggettivo} {slot}? Clicca su si o no.".format(aggettivo="altri" if slot == "argomenti" else "altre",slot=slot),
            buttons= [{"title":"si","payload":"si"},
                    {"title":"no","payload":"no"}
                ])
        return  lista





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
       
        additional_slots = []
        lista_formati= tracker.slots.get("formati")
        vuole_ripetizione=tracker.get_slot("vuole_ripetizione")
        if "esercizi" not in lista_formati:
            return []
        else:
            if not vuole_ripetizione:
                return  domain_slots
            else:
                additional_slots.append("tempo")
                return domain_slots + additional_slots


    
    

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
        slot=slot_value.lower()
        regex = re.compile('[@_#$%^&*<>\|}{~]')
        if(re.search(regex,slot) != None):
            return {"nome_corso": None}
        elif "??" in slot or "chiama" in slot:
            a = re.search(r'\b(??)|(chiama)\b', slot)
            sum_number= 1 if "??" in slot else 6
            title=slot[a.start()+sum_number+1:]
            return  {"nome_corso": title.strip()}
        else:
            return {"nome_corso": slot}
       

        

    def validate_et??(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
      
        if not has_numbers(slot_value) and tracker.get_intent_of_latest_message() != "stop_form":
            return {"et??":None}
        
        elif tracker.get_intent_of_latest_message() == "stop_form" and  not has_numbers(slot_value):
            return {"requested_slot": None,"et??": None}
        else:
            et??_number = re.findall('[0-9]+', slot_value)
            if int(et??_number[0])<1 or int(et??_number[0]) >50 :
                return {"et??": None}
            else:    
                return {"et??": int(et??_number[0])}
    
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
        else:
            dispatcher.utter_message(text="Indica gli argomenti del corso, separati dalla virgola.")
            return {"durata_lezioni": slot_value}
    
    def validate_difficolt??(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
     
     
        if tracker.get_intent_of_latest_message() == "stop_form":
            
            return {"requested_slot": None,"difficolt??": None}
        else:
            return {"difficolt??": slot_value}

    
    def validate_lingua(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        lingue= ["italiano", "inglese", "francese", "tedesco", "cinese", "spagnolo", "giapponese","russo", "portoghese","arabo"]
        spell = Speller('it')
        frase_corretta=spell(slot_value).lower()
        for i in lingue:
            if i in frase_corretta:
                return {"lingua": i.lower()}
        
        return {"lingua": None}

    def validate_argomenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("arg " + tracker.get_intent_of_latest_message())
        lista_argomenti = slot_value.lower().split(',')
        lista_argomenti= [i.strip() for i in lista_argomenti]
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"argomenti": None}
        else:
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica gli argomenti del corso, separati dalla virgola.")
                return {"argomenti": None}
            elif ":"  in lista_argomenti[0] or "sono" in lista_argomenti[0]:
                return {"argomenti":eliminate_introduction_slots(lista_argomenti,"argomenti", dispatcher)}
            else:
                dispatcher.utter_message(
                text="vuoi aggiungere altri argomenti? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                ])
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
        if slot_value == "si":
            dispatcher.utter_message(text="Indica gli altri argomenti del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altri_argomenti":None}

        elif slot_value == "no":
            dispatcher.utter_message(text="Indica le abilit?? iniziali che lo studente deve avere prima del corso, separati dalla virgola.")
            return {"vuole_altri_argomenti": False}

        else:
            altri_argomenti = slot_value.split(',')
            altri_argomenti= [i.strip() for i in altri_argomenti]
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica gli altri argomenti del corso, separati dalla virgola.")
                return{"vuole_altri_argomenti":None}
            elif ":"  in altri_argomenti[0] or "sono" in altri_argomenti[0]:
                new_arg=eliminate_introduction_slots(altri_argomenti,"argomenti", dispatcher)
                return {"argomenti":argomenti + new_arg,"vuole_altri_argomenti":None}
            else:
                dispatcher.utter_message(
                text="vuoi aggiungere altri argomenti? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                         {"title":"no","payload":"no"}
            ])
                new_argomenti= argomenti + altri_argomenti
                return {"argomenti": new_argomenti, "vuole_altri_argomenti":None}
       
        
        
            
        
    def validate_abilit??(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("ab " + tracker.get_intent_of_latest_message())
        lista_abilit?? = slot_value.lower().split(',')
        lista_abilit??= [i.strip() for i in lista_abilit??]
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"abilit??": None}
        else:
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le abilit?? iniziali che lo studente deve avere prima del corso, separati dalla virgola.")
                return{"abilit??":None}
            elif ":"  in lista_abilit??[0] or "sono" in lista_abilit??[0]:
                return {"abilit??":eliminate_introduction_slots(lista_abilit??,"abilit??", dispatcher)}
            else:
                dispatcher.utter_message(
                text="vuoi aggiungere altre abilit??? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                      {"title":"no","payload":"no"}
            ])
                return {"abilit??": lista_abilit??}
        


    def validate_vuole_altre_abilit??(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("ab " + tracker.get_intent_of_latest_message())
        abilit?? = tracker.get_slot("abilit??")
        if slot_value == "si":
            dispatcher.utter_message(text="Indica le altre abilit?? iniziali del corso, separate dalla virgola.")
            return {"vuole_altre_abilit??": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altre_abilit??":None}

        elif slot_value == "no":
            dispatcher.utter_message(text="Indica le competenze che lo studente deve raggiungere alla fine del corso, separate dalla virgola.")
            return {"vuole_altre_abilit??": False}

        else:
            altre_abilit?? = slot_value.split(',')
            altre_abilit??= [i.strip() for i in altre_abilit??]
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le altre abilit?? iniziali del corso, separate dalla virgola.")
                return{"vuole_altre_abilit??":None}
            elif ":"  in altre_abilit??[0] or "sono" in altre_abilit??[0]:
                new_ab=eliminate_introduction_slots(altre_abilit??,"abilit??", dispatcher)
                return {"abilit??":abilit?? + new_ab, "vuole_altre_abilit??":None}
            else:
                dispatcher.utter_message(
                    text="vuoi aggiungere altre abilit??? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                            {"title":"no","payload":"no"}
            ])
                new_abilit??= abilit?? + altre_abilit??
                return {"abilit??": new_abilit??, "vuole_altre_abilit??":None}
            
            

        


    def validate_competenze(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print("comp " + tracker.get_intent_of_latest_message())
        lista_competenze = slot_value.lower().split(',')
        lista_competenze= [i.strip() for i in lista_competenze]
        if tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot": None,"competenze": None}
        else:
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le competenze che lo studente deve raggiungere alla fine del corso, separate dalla virgola.")
                return{"competenze":None}
            elif ":"  in lista_competenze[0] or "sono" in lista_competenze[0]:
                return {"competenze":eliminate_introduction_slots(lista_competenze,"competenze", dispatcher)}
            else:
                dispatcher.utter_message(
                text="vuoi aggiungere altre competenze? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
            ])
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
        if slot_value == "si":
            dispatcher.utter_message(text="Indica le altre competenze che lo studente deve raggiungere  alla fine del corso, separate dalla virgola.")
            return {"vuole_altre_competenze": None}

        elif tracker.get_intent_of_latest_message() == "stop_form":
            return {"requested_slot":None, "vuole_altre_competenze":None}

        elif slot_value == "no":
            return {"vuole_altre_competenze": False}

        else:
            altre_competenze = slot_value.split(',')
            altre_competenze= [i.strip() for i in altre_competenze]
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text="Indica le altre competenze che lo studente deve raggiungere  alla fine del corso, separate dalla virgola.")
                return{"vuole_altre_competenze":None}
            elif ":"  in altre_competenze[0] or "sono" in altre_competenze[0]:
                new_comp=eliminate_introduction_slots(altre_competenze,"competenze", dispatcher)
                return {"competenze":competenze + new_comp , "vuole_altre_competenze":None}
            else:
                dispatcher.utter_message(
                    text="vuoi aggiungere altre competenze? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                            {"title":"no","payload":"no"}
            ])
                new_competenze= competenze + altre_competenze
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
        elif slot_value== "difficolt??":
            dispatcher.utter_message(response="utter_ask_difficolt??")
        elif slot_value in ["argomenti","abilit??","competenze"]:
            response= "Inserisci  {pronome} {aggettivo} {metadato}, {separazione} dalla virgola.".format(pronome="i" if slot_value == "argomenti" else "le",aggettivo="nuovi" if slot_value == "argomenti" else "nuove",metadato=slot_value,separazione="separati" if slot_value == "argomenti" else "separate" )
            dispatcher.utter_message(text=response)
        elif slot_value in ["nome_corso","numero_lezioni"]:
            dispatcher.utter_message(text="Inserisci il nuovo valore per il campo {metadato} (se ?? un campo numerico, usa le cifre)".format(metadato="nome del corso" if slot_value == "nome_corso" else "numero delle lezioni"))
        else:
            dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo {slot_value} (se ?? un campo numerico, usa le cifre).")
        return {"metadato_da_modificare": slot_value}
       
    
    def validate_cambio_metadato (
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        
        metadato= tracker.slots.get("metadato_da_modificare")
        if metadato == "abilit??" or metadato == "competenze" or metadato == "argomenti":
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            lista_elementi = slot_value.lower().split(',')
            lista_elementi= [i.strip() for i in lista_elementi]
            if(re.search(regex,slot_value) != None):
                response= "Inserisci  {pronome} {aggettivo} {metadato}, {separazione} dalla virgola.".format(pronome="i" if metadato == "argomenti" else "le",aggettivo="nuovi" if metadato == "argomenti" else "nuove",metadato=metadato,separazione="separati" if metadato == "argomenti" else "separate" )
                dispatcher.utter_message(text=response)
                return {"cambio_metadato": None}
            elif ":"  in lista_elementi[0] or "sono" in lista_elementi[0]:
                return {f"{metadato}":eliminate_introduction_slots(lista_elementi,"cambio", dispatcher)}
            else:
                return {f"{metadato}": lista_elementi}
        elif metadato=="et??" or metadato=="numero_lezioni":
            numero = re.findall('[0-9]+', slot_value)
            limite= 50 if metadato=="et??" else 100
            if len(numero)==0 or int(numero[0]) <1 or  int(numero[0]) >limite :
                dispatcher.utter_message(text="Inserisci il nuovo valore per il campo {valore} (per indicare il numero usa le cifre)".format(valore="numero delle lezioni" if metadato=="numero_lezioni" else "et??"))
                return {"cambio_metadato": None}
            else:    
                return {f"{metadato}": int(numero[0])}
        elif metadato== "lingua":
            lingue= ["italiano", "inglese", "francese", "tedesco", "cinese", "spagnolo", "giapponese","russo", "portoghese","arabo"]
            spell = Speller('it')
            frase_corretta=spell(slot_value).lower()
            for i in lingue:
                if i in frase_corretta:
                    return {"lingua": i.lower()}
            else:
                dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo lingua")
                return {"cambio_metadato": None}
        elif metadato == "nome_corso":
            regex = re.compile('[@_#$%^&*<>\|}{~]')
            if(re.search(regex,slot_value) != None):
                dispatcher.utter_message(text=f"Inserisci il nuovo valore per il campo {metadato}")
                return {"cambio_metadato": None}
            elif "??" in slot_value.lower() or "chiama" in slot_value.lower():
                a = re.search(r'\b(??)|(chiama)\b', slot_value.lower())
                sum_number= 1 if "??" in slot_value.lower() else 6
                title=slot_value[a.start()+sum_number+1:].lower()
                return  {f"{metadato}": title.strip()}
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
            for formato in lista_formati:
                if proposed_link_size[f"{formato}"] == 0:
                    new_list.remove(f"{formato}")
                    new_list.remove(f"aggiunta_{formato}")
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
        global lista_formati_generale
        if not has_numbers(slot_value) or slot_value==" ":
            formati_list=["videolezioni","esercizi","quiz","documenti"]
            lista_formati_generale= formati_list
            msg= create_responses("formati",tracker, dispatcher)
            dispatcher.utter_message(text=msg)
            return {"formati":formati_list}
        else:
            formati_num = re.findall('[0-9]+', slot_value)
            formati_num=list(dict.fromkeys(formati_num))
            mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
            formati_list= []
            formati_num= list(map(int, formati_num))
            if not(all(i>0 and i<=4 for i in formati_num)) or has_duplicates(formati_num):
                    return {"formati":None}
            for i in formati_num:
                formati_list.append(mapping.get(i))
            lista_formati_generale=formati_list
            msg= create_responses("formati",tracker, dispatcher)
            dispatcher.utter_message(text=msg)
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
            if not(all(i>0 and i<=proposed_link_size["videolezioni"] for i in videolezioni_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"videolezioni":None}
            dispatcher.utter_message(
                    text="desideri aggiungere altre videolezioni? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                ])
            return {"videolezioni": list(dict.fromkeys(videolezioni_num))}
    
    def validate_aggiunta_videolezioni(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_videolezioni
        formati= tracker.slots.get("formati")
        videolezioni=tracker.slots.get("videolezioni")
        altre_vid_num = re.findall('[0-9]+', slot_value)
        altre_vid_num= list(map(int, altre_vid_num))
        if slot_value == "si":
            dispatcher.utter_message(text="indica altre videolezioni")
            controller_videolezioni=False
            return {"aggiunta_videolezioni": None}

        elif slot_value == "no":
            controller_videolezioni=False
            if formati[len(formati)-1] != "videolezioni":
                msg= create_responses("videolezioni",tracker,dispatcher)
                dispatcher.utter_message(text=msg)
            return {"aggiunta_videolezioni": False}
        else:
            if (not has_numbers(slot_value) or not( all(i>0 and i<=proposed_link_size["videolezioni"] for i in altre_vid_num))) and controller_videolezioni==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_videolezioni":None}
            else:
                controller_videolezioni=True
                dispatcher.utter_message(
                    text="vuoi aggiungere altre videolezioni? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                            {"title":"no","payload":"no"}
                    ])
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
            if not(all(i>0 and i<=proposed_link_size["esercizi"] for i in esercizi_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"esercizi":None}
            dispatcher.utter_message(
                text="vuoi aggiungere altri esercizi? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                ])
            return {"esercizi": list(dict.fromkeys(esercizi_num))}
    
    def validate_aggiunta_esercizi(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_esercizi
        formati= tracker.slots.get("formati")
        esercizi=tracker.slots.get("esercizi")
        altri_es_num = re.findall('[0-9]+', slot_value)
        altri_es_num= list(map(int, altri_es_num))
        if slot_value == "si":
            controller_esercizi=False
            dispatcher.utter_message(text="indica altri esercizi")
            return {"aggiunta_esercizi": None}

        elif slot_value == "no":
            controller_esercizi=False
            if formati[len(formati)-1] != "esercizi":
                msg= create_responses("esercizi",tracker,dispatcher)
                dispatcher.utter_message(text=msg)
            return {"aggiunta_esercizi": False}

        else:
            if (not has_numbers(slot_value) or not( all(i>0 and i<=proposed_link_size["esercizi"] for i in altri_es_num))) and controller_esercizi==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_esercizi":None}
            else:
                controller_esercizi=True
                dispatcher.utter_message(
                    text="vuoi aggiungere altri esercizi? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                      {"title":"no","payload":"no"}
                    ])
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
            if not(all(i>0 and i<=proposed_link_size["quiz"] for i in quiz_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"quiz":None}
            dispatcher.utter_message(
                text="vuoi aggiungere altri quiz? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                ])
            return {"quiz": list(dict.fromkeys(quiz_num))}
    
    
    
    def validate_aggiunta_quiz(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_quiz
        formati= tracker.slots.get("formati")
        quiz=tracker.slots.get("quiz")
        altri_quiz_num = re.findall('[0-9]+', slot_value)
        altri_quiz_num= list(map(int, altri_quiz_num))
        if slot_value == "si":
            controller_quiz=False
            dispatcher.utter_message(text="indica altri quiz")
            return {"aggiunta_quiz": None}
        elif slot_value == "no":
            controller_quiz=False
            if formati[len(formati)-1] != "quiz":
                msg=create_responses("quiz",tracker , dispatcher)
                dispatcher.utter_message(text=msg)
            return {"aggiunta_quiz": False}

        else:
            if (not has_numbers(slot_value) or not(all(i>0 and i<=proposed_link_size["quiz"] for i in altri_quiz_num))) and controller_quiz==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_quiz":None}
            else:
                controller_quiz=True
                dispatcher.utter_message(
                    text="vuoi aggiungere altri quiz? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                    ])
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
            if not(all(i>0 and i<=proposed_link_size["documenti"] for i in mat_num)):
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"documenti":None}
            dispatcher.utter_message(
                text="vuoi aggiungere altri documenti? Clicca su si o no.",
                buttons= [{"title":"si","payload":"si"},
                        {"title":"no","payload":"no"}
                    ])
            return {"documenti": list(dict.fromkeys(mat_num))}
    
    def validate_aggiunta_documenti(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict
    ) -> Dict[Text, Any]:
        global controller_documenti
        formati= tracker.slots.get("formati")
        documenti=tracker.slots.get("documenti")
        altri_doc_num = re.findall('[0-9]+', slot_value)
        altri_doc_num= list(map(int, altri_doc_num))
        if slot_value == "si":
            controller_documenti=False
            dispatcher.utter_message(text="indica altri documenti")
            return {"aggiunta_documenti": None}

        elif slot_value == "no":
            controller_documenti=False
            if formati[len(formati)-1] != "documenti":
                msg=create_responses("documenti",tracker , dispatcher)
                dispatcher.utter_message(text=msg)
            return {"aggiunta_documenti": False}

        else:
            if (not has_numbers(slot_value) or not(all( i>0 and i<=proposed_link_size["documenti"] for i in altri_doc_num))) and controller_documenti==False:
                dispatcher.utter_message(text="Attenzione! Inserisci i numeri associati ai link che desideri")
                return {"aggiunta_documenti":None}
            else:
                controller_documenti=True
                dispatcher.utter_message(
                    text="vuoi aggiungere altri documenti? Clicca su si o no.",
                    buttons= [{"title":"si","payload":"si"},
                         {"title":"no","payload":"no"}
                    ])
                documenti_totale=documenti + altri_doc_num
                documenti_totale= list(dict.fromkeys(documenti_totale))
                return {"documenti": documenti_totale, "aggiunta_documenti": None}
    
    
    

def create_responses (slot, tracker: Tracker, dispatcher: CollectingDispatcher):
    mapping =  {1: 'videolezioni', 2: 'esercizi', 3: 'quiz', 4: 'documenti'}
    next_slot= None
    formati= tracker.slots.get("formati")
    request = tracker.get_slot("recommend_query")
    if slot=="formati":
        next_slot= lista_formati_generale[0]
        #RECOMMENDER LOGIC
    else:
        for i in range(len(lista_formati_generale)):
            if lista_formati_generale[i]==slot and i < len(lista_formati_generale)-1:
                next_slot= lista_formati_generale[i+1]
            elif lista_formati_generale[i]==slot and i == len(lista_formati_generale)-1:
                next_slot = None
            

        #RECOMMENDER LOGIC

    needs_removing = tracker.get_slot(f"aggiunta_{next_slot}")
    request["type"] = next_slot
    request["remove"] = needs_removing
    request["public"] = ""
    response = requests.post('http://127.0.0.1:8080/recommend', json = request)
    parsed = json.loads(response.content)
    proposed_link_size[f"{next_slot}"]=len(parsed)
    if len(parsed)==0:
        dispatcher.utter_message(text=f"Non ci sono link di {next_slot} che soddisfino le tue necessit??.")
        if next_slot!=lista_formati_generale[len(lista_formati_generale)-1]:
            return create_responses(f"{next_slot}",tracker,dispatcher)
    else:
        dispatcher.utter_message(f"Ora ti indicher?? dei link a siti contenenti {next_slot}.")
        text_to_save = ""
        for i in range(len(parsed)):
            text_to_save += f'Titolo: {parsed[i][0]} \nLink {parsed[i][1]} \n'
            message = f'-{i+1}) Titolo: {parsed[i][0]},\nLink: {parsed[i][1]}'
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
            "Et??": "",
            "Keywords": "",
        }



        #Map slots to a dictionary
        slotdict["Durata"] = spell(str(tracker.get_slot("durata_lezioni")))
        slotdict["Et??"] = spell(str(tracker.get_slot("et??")))
        slotdict["Keywords"] = translator.translate(spell(str(tracker.get_slot("argomenti"))))
        
        #iterate over slots and parse
        for key in slotdict:
            #save the queries in a list
            total_kw_list = []
            queries = slotdict[key].split(", ")
            print("queries "+ str(queries))
            dir = os.getcwd()
            #create the embeddings of all the possible values in MERLOT
            file = open(f'actions/Dataset/{key}.txt')
            list = file.read().splitlines()
            corpus = list

            #load a pre made tensor for the embeddings
            corpus_embeddings = torch.load(f"actions/Tensors/code_{key}_tensor.pt")

            #define the number of responses(needs to be tweaked accordingly)
            top_k = min(5, len(corpus))

            #calculate semantic similarities
            for query in queries:
                query_embedding = embedder.encode(query, convert_to_tensor=True)
                hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=5)
                print("hits" + " "+str(hits))
                hits = hits[0]
                print("Query: "+ query)
                #insert the hits into the Json
                if key != "Keywords":
                    hit = hits[0]
                    item_to_append = {key: corpus[hit["corpus_id"]]}
                    print("item_to_append"+" "+ str(item_to_append))
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
                #if tracker.get_slot("argomenti") == None:
                   # request["Keywords"]= tracker.get_slot("argomenti")
                #else:
                request.update(keyword_item)
                print("requests")
                print(request)

            #placeholder print,, not needed in production
            request["Et??"] = tracker.get_slot('et??')
            #request["Durata"] = tracker.get_slot('durata_lezioni')
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
        dispatcher.utter_message(text="I link che hai scelto sono:")
        # for every value in every slot search in the dict concat to a message and utter
        if "videolezioni" in lista_formati_generale :
            if videolezionislot==None:
                string_vid="Non ci sono link di videolezioni proposti."
            else:
                string_vid = "Videolezioni:\n"
                for i in videolezionislot:
                    i = str(i).split()
                    i = int(i[0])
                    string_vid += f'\nTitolo: {LODict["videolezioni"][i-1][0]}\n Link: {LODict["videolezioni"][i-1][1]}'
        else:
            string_vid=None
        if  "esercizi" in lista_formati_generale :
            if esercizislot==None:
                string_es="Non ci sono link di esercizi proposti."
            else:
                string_es = "Esercizi:\n"
                for i in esercizislot:
                    i = str(i).split()
                    i = int(i[0])
                    string_es += f'\nTitolo: {LODict["esercizi"][i-1][0]}\n Link: {LODict["esercizi"][i-1][1]}'
        else:
            string_es=None
        if  "quiz" in lista_formati_generale :
            if quizslot==None:
                string_quiz="Non ci sono link di quiz proposti."
            else:
                string_quiz = "Quiz:\n"
                for i in quizslot:
                    i = str(i).split()
                    i = int(i[0])
                    string_quiz += f'\nTitolo: {LODict["quiz"][i-1][0]}\n Link: {LODict["quiz"][i-1][1]}'
        else:
            string_quiz=None
        if  "documenti" in lista_formati_generale :
            if documentislot==None:
                string_doc="Non ci sono link di documenti proposti."
            else:
                string_doc = "Documenti:\n"
                for i in documentislot:
                    i = str(i).split()
                    i = int(i[0])                
                    string_doc += f'\nTitolo: {LODict["documenti"][i-1][0]}\n Link: {LODict["documenti"][i-1][1]}'
        else:
            string_doc=None
        textDict={"videolezioni":string_vid,"esercizi":string_es,"quiz":string_quiz,"documenti":string_doc}
        for i in lista_formati_generale:
            dispatcher.utter_message(text=textDict[f"{i}"])
        return[]

class ActionSummary(Action):
    def name(self) -> Text:
        return "action_summary"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any])-> List[Dict[Text,Any]]:
        nome_corso= tracker.get_slot("nome_corso")
        lingua= tracker.get_slot("lingua")
        et??= tracker.get_slot("et??")
        difficolt??= tracker.get_slot("difficolt??")
        numero_lezioni= tracker.get_slot("numero_lezioni")
        durata_lezioni= tracker.get_slot("durata_lezioni")
        argomenti= tracker.get_slot("argomenti")
        abilit??= tracker.get_slot("abilit??")
        competenze= tracker.get_slot("competenze")

        testo= "Le informazioni sul corso sono:\n"
        testo+= f"- nome del corso: {nome_corso}\n"
        testo+= f"- lingua: {lingua}\n"
        testo+= "- et??: {valore}\n".format(valore="non indicata" if et??==None else et??)
        testo+= "- difficolt??: {valore}\n".format(valore="non indicata" if difficolt??==None else difficolt??)
        testo+= "- numero delle lezioni: {valore}\n".format(valore="non indicato" if numero_lezioni==None else numero_lezioni)
        testo+= "- durata delle lezioni: {valore}\n".format(valore="non indicata" if durata_lezioni==None else durata_lezioni)
        testo+= "- argomenti: {valore}\n".format(valore="non indicati" if argomenti==None else argomenti)
        testo+= "- abilit??: {valore}\n".format(valore="non indicate" if abilit??==None else abilit??)
        testo+= "- competenze: {valore}\n".format(valore="non indicate" if competenze==None else competenze)

        dispatcher.utter_message(text=testo)
        
        return []

class ActionSummaryPostModifica(Action):
    def name(self) -> Text:
        return "action_summary_post_modifica"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any])-> List[Dict[Text,Any]]:
        nome_corso= tracker.get_slot("nome_corso")
        lingua= tracker.get_slot("lingua")
        et??= tracker.get_slot("et??")
        numero_lezioni= tracker.get_slot("numero_lezioni")
        durata_lezioni= tracker.get_slot("durata_lezioni")
        difficolt??= tracker.get_slot("difficolt??")
        argomenti= tracker.get_slot("argomenti")
        abilit??= tracker.get_slot("abilit??")
        competenze= tracker.get_slot("competenze")
        vuole_modifica= tracker.get_slot("vuole_modifica")
        if vuole_modifica:
            testo= "Le informazioni sul corso dopo la modifica sono:\n"
            testo+= f"- nome del corso: {nome_corso}\n"
            testo+= f"- lingua: {lingua}\n"
            testo+= "- et??: {valore}\n".format(valore="non indicata" if et??==None else et??)
            testo+= "- difficolt??: {valore}\n".format(valore="non indicata" if difficolt??==None else difficolt??)
            testo+= "- numero delle lezioni: {valore}\n".format(valore="non indicato" if numero_lezioni==None else numero_lezioni)
            testo+= "- durata delle lezioni: {valore}\n".format(valore="non indicata" if durata_lezioni==None else durata_lezioni)
            testo+= "- argomenti: {valore}\n".format(valore="non indicati" if argomenti==None else argomenti)
            testo+= "- abilit??: {valore}\n".format(valore="non indicate" if abilit??==None else abilit??)
            testo+= "- competenze: {valore}\n".format(valore="non indicate" if competenze==None else competenze)

            dispatcher.utter_message(text=testo)
        else:
            dispatcher.utter_message(text="Non ?? stata richiesta alcuna modifica dei campi.")
        
        return []

class ActionGrazie(Action):
    def name(self) -> Text:
        return "action_grazie"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text,Any])-> List[Dict[Text,Any]]:
        valutazione= tracker.get_slot("valutazione")
        print("val"+ " "+ valutazione)
        if valutazione == "no":
            dispatcher.utter_message(text="Grazie lo stesso!")
        else:
             dispatcher.utter_message(text="Grazie mille per la tua valutazione!")       
        
        return []