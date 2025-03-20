import typing as t
import typing_extensions as te
import os
import dotenv as de
import langgraph.graph as lg
import langgraph.graph.message as lgm
import langgraph.checkpoint.memory as lcm
import langchain_ollama as lo
import textwrap as tw
import pydantic as pyd
import fastapi as fapi
import contextlib as cl
from fastapi.middleware.cors import CORSMiddleware


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


class State(te.TypedDict):
    messages: t.Annotated[list, lgm.add_messages]


class generic_chat_node:
    _self = None

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._initialize(*args, **kwargs)
        return cls._self

    def _initialize(
        self,
        interface: str,
        model: str,
        api_key: str,
        endpoint: str,
        temperature=0.5,
        **kwargs,
    ):
        self.model_name = model
        self.model_interface = interface
        self.endpoint = endpoint
        self.temperature = temperature
        self.llm = model_factory(
            model_interface=interface,
            model_name=self.model_name,
            api_key=api_key,
            temperature=temperature,
            endpoint=self.endpoint,
            **kwargs,
        )

    def get_model_name(self):
        """
        Return the name of the model.

        Returns:
            str: The name of the model.
        """
        return self.model_name

    def get_model_type(self):
        """
        Return the Langchain interface class of the model.

        Returns:
            str: The Langchain interface class of the model.
        """
        return self.model_interface

    def get_response(self, state: State):
        return {"messages": self.llm.invoke(state["messages"])}


class ChatInput(pyd.BaseModel):
    message: str


class UserManager:
    def generate_user_thread_index(cls, user_id: str):
        # Eventually this would involve a DB lookup to make sure we generate a thread not already stored.
        # For now, we'll just choose "42"
        return 42

    def __init__(self, user_id: str, selected_thread: int = None):
        self.user_id = user_id  # Unique user key.
        if selected_thread is not None:
            self.current_user_thread = selected_thread
        else:
            self.current_user_thread = cls.generate_user_thread_index(user_id)
        self.thread_id = self.user_id + "_" + str(self.current_user_thread)

    def get_thread_id(self):
        return self.thread_id


config = {"configurable": {"thread_id": 1}}


class GraphManager:
    def __init__(self):
        self.graph = None
        self.memory = lcm.MemorySaver()

    def initialize_graph(self):
        de.load_dotenv()
        graph_builder = lg.StateGraph(State)
        chatnode = generic_chat_node(
            interface="ChatOllama",
            model="mistral_nemo_conservative",
            api_key=None,
            endpoint=None,
            temperature=0.5,
            num_predict=1500,
        )
        graph_builder.add_node("chatnode", chatnode.get_response)
        graph_builder.add_edge(lg.START, "chatnode")
        graph_builder.add_edge("chatnode", lg.END)
        self.graph = graph_builder.compile(checkpointer=self.memory)
        return self.graph

    def free_graph_resources(self):
        pass  # For now


graph_manager = GraphManager()


@cl.asynccontextmanager
async def service_lifecycle(app: fapi.FastAPI):
    """
    Lifecycle context for the oracle service.
    """
    # Startup
    graph_manager.initialize_graph()

    # Run
    yield

    # Shutdown
    graph_manager.free_graph_resources()


app = fapi.FastAPI(lifespan=service_lifecycle)

# Add after creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/initialize")
async def initialize_endpoint(user_identifier: str = fapi.Query(...)):
    try:
        current_user = UserManager(user_identifier, selected_thread=1)
        if not current_user:
            raise ValueError("User not found")
        return {"success": f"User {user_identifier} logged in!"}

    except Exception as err:
        print(f"Error setting user {str(err)}")
        raise fapi.HTTPException(status_code=500, detail=str(err))


@app.post("/chat")
async def chat_endpoint(chat_input: ChatInput):
    try:
        if not graph_manager.graph:
            raise ValueError("Graph not initialized")

        responses = []
        for event in graph_manager.graph.stream(
            {"messages": [{"role": "user", "content": chat_input.message}]},
            config,
            # stream_mode="values",
        ):
            for value in event.values():
                responses.append(value["messages"].content)
        return {"responses": responses[0] if responses else "..."}
    except Exception as err:
        print(f"Error in chat endpoint: {str(err)}")
        raise fapi.HTTPException(status_code=500, detail=str(err))


@app.get("/get_conversation")
async def get_conversation_endpoint():
    try:
        if not graph_manager.graph:
            raise ValueError("Graph not initialized")

        # Get the conversation history from the memory
        conversation = []
        if graph_manager.memory:
            conversation = graph_manager.graph.get_state(config).values["messages"]
            return conversation
    except Exception as err:
        print(f"Error retrieving conversation: {str(err)}")
        raise fapi.HTTPException(status_code=500, detail=str(err))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0", port=8000)
