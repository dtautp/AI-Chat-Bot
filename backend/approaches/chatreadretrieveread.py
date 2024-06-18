import os
import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from approaches.approach import Approach
from text import nonewlines
from datetime import datetime
import firebase_module
import time
from helpers import format_datetime
from flask import session

AZURE_SEARCH_INDEX = os.getenv ("AZURE_SEARCH_INDEX")
AZURE_OPENAI_MAX_CONTENT = os.getenv ("AZURE_OPENAI_MAX_CONTENT") or 4500

fecha_actual = datetime.now()
fecha_formateada = fecha_actual.strftime("%d/%m/%Y %H:%M:%S")

# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class ChatReadRetrieveReadApproach(Approach):

# Eres un asistente de inteligencia artificial diseñado para ayudar a estudiantes universitarios a resolver sus dudas respecto a los temas de su curso de "Fundamentos de   Contabilidad y Finanzas" . Siempre debes basar tus respuestas en la información específica proporcionada por el sistema RAG, que ha recuperado datos relevantes de las fuentes y materiales del curso. Siempre que des una respuesta se breve y conciso, a no ser que el estudiante te pida lo contrario. No debes inventar información ni ofrecer datos que no hayan sido verificados por el RAG. Si no encuentras la respuesta en la información provista por el RAG, es mejor indicar que la información no está disponible en lugar de dar una respuesta incorrecta. Aquí está la pregunta del estudiante y la información recuperada por el RAG:

# Pregunta del estudiante: {pregunta_del_estudiante}

# Información del RAG: {información_recuperada_por_RAG}

# Por favor, formula tu respuesta basándote exclusivamente en la información del RAG.

    KNOWLEDGE_BASE_VERSION = 'v2'
    SYSTEM_PROMPT_ID = 3
    system_prompt = firebase_module.select_system_prompt_by_id(SYSTEM_PROMPT_ID)
    prompt_content = system_prompt['prompt_content']


    def __init__(self, search_client: SearchClient, chatgpt_deployment: str, gpt_deployment: str, sourcepage_field: str, content_field: str):
        self.search_client = search_client
        self.search_index = AZURE_SEARCH_INDEX
        self.chatgpt_deployment = chatgpt_deployment
        self.gpt_deployment = gpt_deployment
        self.sourcepage_field = sourcepage_field
        self.content_field = content_field
        self.max_content = AZURE_OPENAI_MAX_CONTENT

    def run(self, history: list[dict], overrides: dict) -> any:
        use_semantic_captions = True if overrides.get("semantic_captions") else False
        # top = overrides.get("top") or 3
        top = 5
        exclude_category = overrides.get("exclude_category") or None
        filter = "category ne '{}'".format(exclude_category.replace("'", "''")) if exclude_category else None
        # Search -----------------------------------------
        ask = history[len(history)-1]["user"]
        r = self.search_client.search(ask, filter=filter, top=top)
        if use_semantic_captions:
            results = [doc[self.sourcepage_field] + ": " + nonewlines(" . ".join([c.text for c in doc['@search.captions']])) for doc in r]
        else:
            results = [nonewlines(doc[self.content_field]) for doc in r]
        content = "\n".join(results)

        # Convertir cada resultado en una lista para el campo 'content'
        content_list = [result.split('\n') for result in results]
        print(content_list)
        # Search -----------------------------------------
        
        # actualizar el historial de la conversación ------------
        messages = self.get_chat_history_as_messages(history)
        
        # print(history)
        # print(messages)
        print(ask)

        prompt  = [{"role": "system", 
                        "content": self.prompt_content.format(
                                    sources = content[:int(self.max_content)],
                                    ask = ask,
                                    history = messages)
                        }]

        # Answer ---------------------------- 
        start_time = time.time()
        completion = openai.ChatCompletion.create(
                engine=self.chatgpt_deployment,
                messages=prompt,
                temperature=overrides.get("temperature") or 0.7, 
                max_tokens=500,
            )
        
        # print(completion.to_dict()['created'])
        # print(format_datetime(completion.to_dict()['created']))
        
        if (self.SYSTEM_PROMPT_ID != 'test'):
            request_dic = {
                    'system_prompt_id':self.SYSTEM_PROMPT_ID,
                    'query':ask,
                    'response':completion.to_dict()['choices'][0]["message"]["content"],
                    'search_content':content_list,
                    'history_content':history,
                    # 'device_id':session.get('device_id'),
                    'completion_tokens':completion.to_dict()['usage']['completion_tokens'],
                    'prompt_tokens':completion.to_dict()['usage']['prompt_tokens'],
                    'time_stamp':format_datetime(completion.to_dict()['created']),
                    'model':completion.to_dict()['model'],
                    'history_len':len(history),
                    'execution_time':time.time()-start_time,
                    'prompt_version':self.system_prompt['version_number'],
                    'knowledge_base_version':self.KNOWLEDGE_BASE_VERSION
            }
            firebase_module.insert_request(request_dic)
            
        response = completion["choices"][0]["message"]["content"]
        # print(response)
        # Answer ---------------------------- 
        return {"data_points": results, 
                "answer": response,
                "thoughts": ""
                }

    def get_chat_history_as_messages(self, history):
        history_list = []
        if len(history) == 0:
            return history_list
        for h in reversed(history):
            key = next(iter(h))
            try:
                history_item = {"role": "assistant", "content": h["bot"]}
                history_list.insert(0, history_item)
            except:
                pass
            key = next(iter(h))
            try:
                history_item = {"role": "user", "content": h["user"]}                
                history_list.insert(0, history_item)
            except:
                pass
        return history_list