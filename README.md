## The Oracle
A simple chatbot designed to interface with a desired Ollama hosted local LLM 
model.

## Usage
1.  You must have ollama installed and running as a server with at least one 
    working model.  (The default model looked for by the program is llama3.2:1b 
    which is a small model of ~1.25 GB size)

2.  open a terminal and run:
    python oracle.py &
    python -m http.server -d frontend 8080

3.  Navigate your webbrowser to localhost:8080

You should be able to converse with your Ollama hosted model.

If you would like to use a different model you can set up a .env file in the 
directory from which you launch oracle.py, with the environment variable set as:

MODEL="model-name:model_version"

e.g.

MODEL="hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q5_K_M"

Will load the model with that exact name exposed in your ollama server if it is
present.


## Changelog
- 0.1.0: Initial release
- 0.2.0: FastAPI Webapp version

