import os
import langchain_ollama as lo


def model_factory(
    *, model_interface, model_name, api_key, temperature=0.5, endpoint=None, **kwargs
):
    print(f"Model Interface Requested: {model_interface}")
    if os.getenv("MATURITY") == "test":
        # Return a mock interface here eventually for testing
        return None
    if model_interface == "ChatOllama":
        if os.getenv("OLLAMA_ENDPOINT") and endpoint is None:
            endpoint = os.getenv("OLLAMA_ENDPOINT")
            if "http://" not in endpoint:
                endpoint = "http://" + endpoint
        else:
            endpoint = "http://localhost:11434"
        if api_key is None:
            api_key = "Ollama_No_API_Key"
        try:
            llm = lo.ChatOllama(
                model=model_name,
                endpoint=endpoint,
                api_key=api_key,
                temperature=temperature,
                **kwargs,
            )
            return llm
        except Exception as err:
            print(f"Error instantiating the ChatOllama interface: {err}")
    else:
        print(f"Models other than ChatOllama are not currently implemented, sorry.")
        return None
