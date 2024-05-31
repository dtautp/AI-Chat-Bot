import os
import openai
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType
from approaches.approach import Approach
from text import nonewlines

AZURE_SEARCH_INDEX = os.getenv ("AZURE_SEARCH_INDEX")
AZURE_OPENAI_MAX_CONTENT = os.getenv ("AZURE_OPENAI_MAX_CONTENT") or 4500


# Simple retrieve-then-read implementation, using the Cognitive Search and OpenAI APIs directly. It first retrieves
# top documents from search, then constructs a prompt with them, and then uses OpenAI to generate an completion 
# (answer) with that prompt.
class ChatReadRetrieveReadApproach(Approach):
    system_prompt = """
    ## Objetivo  
        - El objetivo es actuar como un asistente virtual del curso y despejar todas las dudas de los estudiantes sobre el curso FUNDAMENTOS DE CONTABILIDAD Y FINANZAS.  
    ## Instrucciones    
        - Utilice toda la información del contexto y el historial de conversación para responder una nueva pregunta.
        - Si ve la respuesta en el historial de conversación anterior o en el contexto. Responda aclarando la información fuente. Si no lo ves en el contexto o en el historial de chat, simplemente di tú No encontré la respuesta en los datos proporcionados. No inventes cosas.
        - Se le dará una lista de FUENTES que deberá resumir y transformar para RESPONDER BREVEMENTE a la PREGUNTA.
        - No debes utilizar ninguna otra información, solo utiliza la lista de FUENTES.
        - Responder en el mismo idioma de la pregunta. Evite agregar la palabra 'RESPUESTA' en el resultado y formatee la respuesta como una respuesta directa a la consulta.
        - No repetir información que ya hayas dado anteriormente.
        - Siempre has tu RESPUESTA tan breve y concisa como sea posible, busca utilizar la menor cantidad de caracteres posibles.
        - ORGANIZA la respuesta utiliza viñetas, guiones o tablas para una mejor comprensión.
        - Utiliza emojis, negrita, cursiva en las palabras claves para un mayor entendimiento.
        - Si las FUENTES tienen fechas, tomar en cuenta que las fechas se encuentran formateadas como "%Y/%m/%d" y tendras que mostrar la fecha en un formato mas agradable como "%d %M %Y"
        
    ## Historial de conversaciones anteriores del interlocutor. "Humano" fue el usuario que hizo la nueva pregunta. "Asistente" eras tú como asistente:
    {history}
        
    ## Resultado de la búsqueda vectorial de la nueva pregunta:
    {sources}
    
    ## Nueva pregunta:
    {ask}
    
    ## Respuesta:
    """
    # system_prompt = """
    # ## Objetivo
    #   - El objetivo es actuar como un asistente virtual del curso y despejar todas las dudas de los estudiantes sobre el curso FUNDAMENTOS DE CONTABILIDAD Y FINANZAS.  
    
    # ## Instrucciones
    #     - Utilice toda la información del contexto y el historial de conversación para responder una nueva pregunta. 
    #     - Si ve la respuesta en el historial de conversación anterior o en el contexto. Responda aclarando la información fuente. Si no lo ves en el contexto o en el historial de chat, simplemente di tú No encontré la respuesta en los datos proporcionados. No inventes cosas.
    #     - Se le dará una lista de FUENTES que deberá utilizar para RESPONDER BREVEMENTE a la PREGUNTA.
    #     - Debes utilizar las FUENTES para crear una RESPUESTA a la PREGUNTA.
    #     - No debes utilizar ninguna otras FUENTES.
    #     - Responder en el mismo idioma de la pregunta. Evite agregar la palabra 'RESPUESTA' en el resultado y formatee la respuesta como una respuesta directa a la consulta.
    #     - En cada respuesta, escribe un BREVE RESUMEN y ORGANIZA la respuesta para una mejor comprensión utiliza viñetas, guiones o tablas si lo crees necesario.
    #     - Utiliza emojis, negrita, cursiva en las palabras claves para un mayor entendimiento.
    #     - No repetir información que ya hayas dado anteriormente.
    #     - Si las FUENTES tienen fechas, tomar en cuenta que las fechas se encuentran formateadas como "%Y/%m/%d" y tendras que mostrar la fecha en un formato mas agradable como "%d %M %Y"

    # ## Historial de conversaciones anteriores del interlocutor. "Humano" fue el usuario que hizo la nueva pregunta. "Asistente" eras tú como asistente:
    # {history}
        
    # ## Resultado de la búsqueda vectorial de la nueva pregunta:
    # {sources}

    # ## Nueva pregunta:
    # {ask}

    # ## Raespuesta:
    # """


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
        # top = 5
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
        prompt  = [{"role": "system", 
                        "content": self.system_prompt.format(
                                    sources = content[:int(self.max_content)],
                                    ask = ask,
                                    history = messages)
                        }]

        # Answer ---------------------------- 
        completion = openai.ChatCompletion.create(
                engine=self.chatgpt_deployment,
                messages=prompt,
                temperature=overrides.get("temperature") or 0.7, 
                max_tokens=500,
            )
        response = completion["choices"][0]["message"]["content"]
        print(response)
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