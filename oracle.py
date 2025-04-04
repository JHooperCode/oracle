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
from fastapi.middleware.cors import CORSMiddleware


class OracleState(te.TypedDict):
    messages: t.Annotated[list, lgm.add_messages]


class ChatInput(pyd.BaseModel):
    message: str


config = {"configurable": {"thread_id": 1}}


class GraphManager:
    def __init__(self):
        self.graph = None
        self.memory = lcm.MemorySaver()

    def initialize_graph(self):
        de.load_dotenv()
        graph_builder = lg.StateGraph(OracleState)
        chatnode = bn.generic_chat_node(
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0", port=8000)
