import typing as t
import typing_extensions as te
import dotenv as de
import langgraph.graph as lg
import langgraph.graph.message as lgm
import langgraph.checkpoint.memory as lcm
import langchain_core.messages as lm
import pydantic as pyd
import fastapi as fapi
import contextlib as cl
import backend.nodes as bn
import backend.users as bu
import os
from fastapi.middleware.cors import CORSMiddleware
import copy

DEFAULT_MODEL = "llama3.2:1b"
DEFAULT_INTERFACE = "ChatOllama"


class OracleState(te.TypedDict):
    messages: t.Annotated[list, lgm.add_messages]


class ChatInput(pyd.BaseModel):
    message: str


config = {"configurable": {"thread_id": 1}}


class GraphManager:
    def __init__(self):
        self.graph = None
        self.memory = lcm.MemorySaver()
        self.initial_environment = None

    def initialize_graph(self):
        self.initial_environment = copy.deepcopy(os.environ)
        de.load_dotenv()
        if os.getenv("MODEL") is None:
            model = DEFAULT_MODEL
        else:
            model = os.getenv("MODEL")
        if os.getenv("INTERFACE") is None:
            interface = DEFAULT_INTERFACE
        else:
            interface = os.getenv("INTERFACE")

        graph_builder = lg.StateGraph(OracleState)
        print(f"Initializing chat node with interface: {interface} and model: {model}")
        chatnode = bn.generic_chat_node(
            interface=interface,
            model=model,
            api_key=None,
            endpoint=None,
            temperature=0.5,
            num_predict=1500,
        )
        graph_builder.add_node("chatnode", chatnode.get_response)
        graph_builder.add_edge(lg.START, "chatnode")
        graph_builder.add_edge("chatnode", lg.END)
        self.graph = graph_builder.compile(checkpointer=self.memory)
        os.environ.clear()
        os.environ.update(self.initial_environment)
        return self.graph

    def free_graph_resources(self):
        os.environ.clear()
        os.environ.update(self.initial_environment)


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
        current_user = bu.UserManager(user_identifier, selected_thread=1)
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
            current_state = graph_manager.graph.get_state(config)
            if "messages" not in current_state.values:
                return {
                    "messages": [
                        lm.AIMessage(
                            content="I'm sorry, but I don't remember a previous conversation."
                        )
                    ]
                }
            else:
                return current_state.values
    except Exception as err:
        print(f"Error retrieving conversation: {str(err)}")
        raise fapi.HTTPException(status_code=500, detail=str(err))


@app.get("/get_model_info")
async def get_model_info():
    try:
        if not graph_manager.graph:
            print("Graph not initialized yet")
            raise ValueError("Graph not initialized")

        try:
            chatnode = bn.generic_chat_node.get_instance()
            model_name = chatnode.get_model_name()
            model_type = chatnode.get_model_type()
            print(f"Returning model info - name: {model_name}, type: {model_type}")
            return {"model_name": model_name, "model_type": model_type}
        except Exception as err:
            print(f"Error getting chat node instance or model info: {str(err)}")
            raise ValueError(f"Chat node error: {str(err)}")
    except Exception as err:
        print(f"Error getting model info: {str(err)}")
        raise fapi.HTTPException(status_code=500, detail=str(err))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0", port=8000)
