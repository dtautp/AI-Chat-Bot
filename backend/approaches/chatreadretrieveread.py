import os
import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from approaches.approach import Approach
from text import nonewlines
import pandas as pd
from datetime import datetime

AZURE_SEARCH_INDEX = os.getenv ("AZURE_SEARCH_INDEX")
AZURE_OPENAI_MAX_CONTENT = os.getenv ("AZURE_OPENAI_MAX_CONTENT") or 4500

fecha_actual = datetime.now()
fecha_formateada = fecha_actual.strftime("%d/%m/%Y %H:%M:%S")


# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class ChatReadRetrieveReadApproach(Approach):
    # system_prompt = """
    # ## Task Goal
    #     - The goal is to act as a course assistant and clear all doubts for students about the FUNDAMENTALS OF ACCOUNTING AND FINANCE course.

    # ## Task Constructions
    #     - You will be given a list of SOURCES that you will need to use to ANSWER a QUESTION.
    #     - You must use the SOURCES to create an ANSWER to the QUESTION.
    #     - You must not use any other SOURCES.
    #     - Always include the SOURCE name for each fact in the response, referencing its full path with square brackets, e.g., [info1.txt].
    #     - Answer in the same language as the question. Avoid adding the word 'ANSWER' in the output, and format the response as a direct reply to the query.
    #     - In each answer, write a brief summary and structure the answer for better understanding, use bullets, separators or any list organizer if you think necessary.
    #     - Do not repeat information that you have already given previously.
    #     - Answer in a precise and summarized way for a student.
    #     - Responds to dates with a "dd - M, yyyy" format.
        
    # ## Task Input:
    #     "HISTORY": "{history}"
    #     "QUESTION": "{ask}"
    #     "SOURCES": "{sources}"

    # ## Task Output:
    # """

    # system_prompt = """
    # ## Objetivo
    #     - El objetivo es actuar como un asistente virtual del curso y despejar todas las dudas de los estudiantes sobre el curso FUNDAMENTOS DE CONTABILIDAD Y FINANZAS.

    # ## Instrucciones
    #     - Se le dará una lista de FUENTES que deberá utilizar para RESPONDER BREVEMENTE a la PREGUNTA.
    #     - Debes utilizar las FUENTES para crear una RESPUESTA a la PREGUNTA.
    #     - No debes utilizar ninguna otras FUENTES.
    #     - Responder en el mismo idioma de la pregunta. Evite agregar la palabra 'RESPUESTA' en el resultado y formatee la respuesta como una respuesta directa a la consulta.
    #     - En cada respuesta, escribe un BREVE RESUMEN y ORGANIZA la respuesta para una mejor comprensión utiliza viñetas, guiones o tablas si lo crees necesario.
    #     - No repetir información que ya hayas dado anteriormente.
    #     - Si las FUENTES tienen fechas, tomar en cuenta que las fechas se encuentran formateadas como "%d/%m/%Y".

    # ## Entrada:
    #     "Historial": "{history}"
    #     "Pregunta": "{ask}"
    #     "Fuentes": "{sources}"
    # """

# Eres un asistente de inteligencia artificial diseñado para ayudar a estudiantes universitarios a resolver sus dudas respecto a los temas de su curso de "Fundamentos de   Contabilidad y Finanzas" . Siempre debes basar tus respuestas en la información específica proporcionada por el sistema RAG, que ha recuperado datos relevantes de las fuentes y materiales del curso. Siempre que des una respuesta se breve y conciso, a no ser que el estudiante te pida lo contrario. No debes inventar información ni ofrecer datos que no hayan sido verificados por el RAG. Si no encuentras la respuesta en la información provista por el RAG, es mejor indicar que la información no está disponible en lugar de dar una respuesta incorrecta. Aquí está la pregunta del estudiante y la información recuperada por el RAG:

# Pregunta del estudiante: {pregunta_del_estudiante}

# Información del RAG: {información_recuperada_por_RAG}

# Por favor, formula tu respuesta basándote exclusivamente en la información del RAG.


    system_prompt = """
    ## Objetivo
      - El objetivo es actuar como un asistente virtual del curso y despejar todas las dudas de los estudiantes sobre el curso FUNDAMENTOS DE CONTABILIDAD Y FINANZAS.  
    
    ## Instrucciones
        - Utilice toda la información del contexto y el historial de conversación para responder una nueva pregunta. 
        - Si ve la respuesta en el historial de conversación anterior o en el contexto. Responda aclarando la información fuente. Si no lo ves en el contexto o en el historial de chat, simplemente di tú No encontré la respuesta en los datos proporcionados. No inventes cosas.
        - Se le dará una lista de FUENTES que deberá utilizar para RESPONDER BREVEMENTE a la PREGUNTA.
        - Debes utilizar las FUENTES para crear una RESPUESTA a la PREGUNTA.
        - No debes utilizar ninguna otras FUENTES.
        - Responder en el mismo idioma de la pregunta. Evite agregar la palabra 'RESPUESTA' en el resultado y formatee la respuesta como una respuesta directa a la consulta.
        - En cada respuesta, escribe un BREVE RESUMEN y ORGANIZA la respuesta para una mejor comprensión utiliza viñetas, guiones o tablas si lo crees necesario.
        - No repetir información que ya hayas dado anteriormente.
        - Si las FUENTES tienen fechas, tomar en cuenta que las fechas se encuentran formateadas como "%d/%m/%Y".

    ## Historial de conversaciones anteriores del interlocutor. "Humano" fue el usuario que hizo la nueva pregunta. "Asistente" eras tú como asistente:
    {history}
        
    ## Resultado de la búsqueda vectorial de la nueva pregunta:
    {sources}

    ## Nueva pregunta:
    {ask}

    ## Raespuesta:
    """


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
        # print (content)
        # Search -----------------------------------------
        
        # actualizar el historial de la conversación ------------
        messages = self.get_chat_history_as_messages(history)
        prompt  = [{"role": "system", 
                        "content": self.system_prompt.format(
                                    sources = content[:int(self.max_content)],
                                    ask = ask,
                                    history = messages)
                        }]
        
        print(prompt)
        print(fecha_formateada)

        # Answer ---------------------------- 
        completion = openai.ChatCompletion.create(
                engine=self.chatgpt_deployment,
                messages=prompt,
                temperature=overrides.get("temperature") or 0.7, 
                # temperature=1, 
                max_tokens=2000,
                # max_tokens=256,
            )
        
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