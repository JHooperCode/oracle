import os
import langchain_ollama as l_o
import ollama as oll
import requests as req


def verify_ollama_server(endpoint: str) -> bool:
    try:
        response = req.get(endpoint)
        return response.status_code == 200
    except Exception as err:
        raise err


def build_ollama_chat_interface(
    model_name: str, endpoint: str | None, temperature: float, **kwargs
):
    if endpoint is None:
        if os.getenv("OLLAMA_ENDPOINT") is not None:
            endpoint = os.getenv("OLLAMA_ENDPOINT")
            if "http://" not in endpoint:
                endpoint = "http://" + endpoint
        else:
            endpoint = "http://localhost:11434"

    try:
        verify_ollama_server(endpoint)
    except Exception as err:
        print(f"The Ollama server at {endpoint} is not working properly.")
        print(f"\tThe returned error trying to contact it was: {err}")
        return None

    api_key = "Ollama_Dont_Need_No_Stinking_API_Key"
    model_list = oll.list()
    try:
        model_names = [model.model.split(":")[0] for model in oll.list().models]
        #        model_names = [model_list.models.model for model_list in oll.list()]
        if model_name not in model_names:
            raise ValueError(
                f"The model {model_name} is not available on the Ollama server at {endpoint}."
            )
    except Exception as err:
        print(
            f"Could not get a list of Ollama model names from the Ollama server at {endpoint}."
        )
        raise err

    try:
        llm = l_o.ChatOllama(
            model=model_name,
            endpoint=endpoint,
            api_key=api_key,
            temperature=temperature,
            **kwargs,
        )
        return llm
    except Exception as err:
        raise err
