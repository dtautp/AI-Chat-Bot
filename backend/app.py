import os
import mimetypes
import time
import logging
import openai
import pymongo
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
# , generate_responses_from_csv
from approaches.chat import get_answer

load_dotenv()

# Replace these with your own values, either in environment variables or directly here
AZURE_STORAGE_ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT") or "mystorageaccount"
AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER") or "content"
AZURE_SEARCH_SERVICE = os.environ.get("AZURE_SEARCH_SERVICE") or "gptkb"
AZURE_SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX") or "gptkbindex"
AZURE_SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY") or "gptkbindex"
AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")  or "myopenai"
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT") or "chat"
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY") or "key"
KB_FIELDS_CONTENT = os.environ.get("KB_FIELDS_CONTENT") or "content"
KB_FIELDS_CATEGORY = os.environ.get("KB_FIELDS_CATEGORY") or "category"
KB_FIELDS_SOURCEPAGE = os.environ.get("KB_FIELDS_SOURCEPAGE") or "sourcepage"

# Used by the OpenAI SDK
openai.api_type = "azure"
openai.api_base = AZURE_OPENAI_SERVICE
openai.api_version = "2023-03-15-preview"
openai.api_key = AZURE_OPENAI_KEY


# Set up clients for Cognitive Search and Storage
search_client = SearchClient(
    endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY))
chat_approaches = {
    "rrr": ChatReadRetrieveReadApproach(search_client, 
                                        AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                                        AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                                        KB_FIELDS_SOURCEPAGE,
                                        KB_FIELDS_CONTENT)
}


app = Flask(__name__)


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

# Ruta que siempre va a esperar el historial de conversacion 
# dentro del body del post
@app.route("/hello", methods=["GET"])
def hello():
    return "Hello I´m chatGPT"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        # ------------------------------------------
        # Usa prompt solamente, sin buscar en search
        """r = get_answer(request.json["history"])
        return jsonify(r)"""
        # ------------------------------------------
        
        # ------------------------------------------
        # Busca en search y responde, RAG simple
        approach = request.json["approach"]
        impl = chat_approaches.get(approach)

        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        r = impl.run(request.json["history"], request.json.get("overrides") or {})
        return jsonify(r)
        # ------------------------------------------
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


# @app.route('/generate-responses', methods=['POST'])
# def generate_responses():
#     # Redireccionar a la plantilla hola.html que está en la carpeta templates
#     return render_template('hola.html')

# @app.route('/generate-responses', methods=['POST'])
# def generate_responses():

#     open('/data/hola.txt', 'a').close()

#     try:
#         # Especifica la ruta completa del archivo CSV
#         csv_file_path = '/data/preguntas.csv'

#         # Genera las respuestas utilizando los parámetros de la clase ChatReadRetrieveReadApproach
#         approach = chat_approaches.get("rrr")  # Obtiene la instancia de la clase ChatReadRetrieveReadApproach
#         generate_responses_from_csv(csv_file_path, 
#                                     approach.search_client, 
#                                     approach.chatgpt_deployment, 
#                                     approach.gpt_deployment, 
#                                     approach.sourcepage_field, 
#                                     approach.content_field)

#         # Envía una respuesta exitosa
#         return jsonify({"message": "Responses generated successfully", "file": csv_file_path})
#     except Exception as e:
#         # Maneja cualquier excepción y envía una respuesta de error
#         logging.exception("Exception in /generate-responses")
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
    # app.run()
