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
    ## Task Goal
        - The goal is to act as a course assistant and clear all doubts for students about the FUNDAMENTALS OF ACCOUNTING AND FINANCE course.

    ## Task Constructions
        - You will be given a list of SOURCES that you will need to use to ANSWER a QUESTION.
        - You must use the SOURCES to create an ANSWER to the QUESTION.
        - You must not use any other SOURCES.
        - Always include the SOURCE name for each fact in the response, referencing its full path with square brackets, e.g., [info1.txt].
        - Answer in the same language as the question. Avoid adding the word 'ANSWER' in the output, and format the response as a direct reply to the query.
        - In each answer, write a brief summary and structure the answer for better understanding, use bullets, separators or any list organizer if you think necessary.
        - Do not repeat information that you have already given previously.
        - Answer in a precise and summarized way for a student.
        - Responds to dates with a "dd - M, yyyy" format.
        
    ## Task Input:
        "HISTORY": "{history}"
        "QUESTION": "{ask}"
        "SOURCES": "{sources}"

    ## Task Output:
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
        print (content)
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
