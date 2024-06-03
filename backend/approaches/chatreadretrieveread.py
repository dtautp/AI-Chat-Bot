import os
import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from approaches.approach import Approach
from text import nonewlines
import pandas as pd
from datetime import datetime
import firebase_module
import time

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
    SYSTEM_PROMPT_ID = 2
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
        top = overrides.get("top") or 3
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
        # Search -----------------------------------------
        
        # actualizar el historial de la conversación ------------
        messages = self.get_chat_history_as_messages(history)
        
        print(history)
        print(messages)
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
                # temperature=1, 
                max_tokens=2000,
                # max_tokens=256,
            )
        
        
        if (self.SYSTEM_PROMPT_ID != 'test'):
            request_dic = {
                    'system_prompt_id':self.SYSTEM_PROMPT_ID,
                    'response':completion.to_dict()['choices'][0]["message"]["content"],
                    'completion_tokens':completion.to_dict()['usage']['completion_tokens'],
                    'prompt_tokens':completion.to_dict()['usage']['prompt_tokens'],
                    'time_stamp':completion.to_dict()['created'],
                    'model':completion.to_dict()['model'],
                    'history_len':len(history),
                    'execution_time':time.time()-start_time,
                    'prompt_version':self.system_prompt['version_number'],
                    'knowledge_base_version':self.KNOWLEDGE_BASE_VERSION
            }
            firebase_module.insert_request(request_dic)
            


        response = completion["choices"][0]["message"]["content"]
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


# def generate_responses_from_csv(csv_path, search_client, chatgpt_deployment, gpt_deployment, sourcepage_field, content_field):
#     # Inicializar la clase ChatReadRetrieveReadApproach
#     approach = ChatReadRetrieveReadApproach(search_client, chatgpt_deployment, gpt_deployment, sourcepage_field, content_field)
    
#     # Leer el archivo CSV usando pandas
#     df = pd.read_csv(csv_path)
    
#     # Asegurarse de que el DataFrame tiene la columna 'pregunta'
#     if 'pregunta' not in df.columns:
#         raise ValueError("El archivo CSV debe tener una columna llamada 'pregunta'")

#     # Agregar columnas para las respuestas y prompts
#     df['Prompt'] = ""
#     df['Respuesta 1'] = ""
#     df['Respuesta 2'] = ""
#     df['Respuesta 3'] = ""
#     df['Respuesta 4'] = ""

#     # Generar respuestas para cada pregunta
#     for index, row in df.iterrows():
#         history = [{"user": row["pregunta"]}]
#         overrides = {}
        
#         responses = []
#         total_tokens = 0

#         # Construir el prompt
#         prompt = approach.system_prompt.format(
#             sources="",
#             ask=row["pregunta"],
#             history=approach.get_chat_history_as_messages(history)
#         )

#         for i in range(4):
#             result = approach.run(history, overrides)
#             response = result["answer"]
#             responses.append(response)
            
#             # Calcular tokens consumidos
#             tokens = num_tokens_from_messages([{"role": "system", "content": prompt}, {"role": "assistant", "content": response}])
#             total_tokens += tokens

#             # Concatenar los tokens consumidos al final del prompt y la respuesta
#             prompt_with_tokens = prompt + f" [Tokens: {tokens}]"
#             response_with_tokens = response + f" [Tokens: {tokens}]"
            
#             if i == 0:
#                 df.at[index, 'Prompt'] = prompt_with_tokens
#             df.at[index, f'Respuesta {i+1}'] = response_with_tokens
    
#     # Sobrescribir el archivo CSV con las nuevas respuestas y prompts
#     df.to_csv(csv_path, index=False)

# # Función para calcular el número de tokens consumidos (debería estar definida en tu entorno)
# def num_tokens_from_messages(messages):
#     # Esta función es un placeholder. Deberías implementar la lógica para calcular los tokens consumidos.
#     # Aquí usamos un estimado simplificado:
#     tokens = sum(len(message["content"].split()) for message in messages)
#     return tokens

# # Ejemplo de uso
# # csv_path = "preguntas.csv"
# # search_client = SearchClient(...)  # Inicializa tu cliente de búsqueda de Azure
# # chatgpt_deployment = "chatgpt-deployment"
# # gpt_deployment = "gpt-deployment"
# # sourcepage_field = "sourcepage"
# # content_field = "content"

# # generate_responses_from_csv(csv_path, search_client, chatgpt_deployment, gpt_deployment, sourcepage_field, content_field)