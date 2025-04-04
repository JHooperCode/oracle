import os
import langchain_ollama as lo
import backend.model_interfaces as mi


def output_start_error(model_interface, model_name, endpoint, error):
    print(
        f"Error:  Could not instantiate the {model_interface} interface with the {model_name} model at location {endpoint}."
    )
    print(f"\tLangchain returned the error message: {error}")
    return


def model_factory(
    *, model_interface, model_name, api_key, temperature=0.5, endpoint=None, **kwargs
):
    print(f"Model Interface Requested: {model_interface}")
    if os.getenv("MATURITY") == "test":
        # Return a mock interface here eventually for testing
        return None
    if model_interface == "ChatOllama":
        try:
            llm = mi.build_ollama_chat_interface(
                model_name, endpoint, temperature, **kwargs
            )
            return llm
        except Exception as err:
            output_start_error(model_interface, model_name, endpoint, err)
            return None
    else:
        print(f"Models other than ChatOllama are not currently implemented, sorry.")
        return None
