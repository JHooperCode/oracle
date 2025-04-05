import backend.model_factory as bm
import oracle as o


class generic_chat_node:
    _self = None

    def __new__(cls, *args, **kwargs):
        if cls._self is None:
            cls._self = super().__new__(cls)
            cls._self._initialize(*args, **kwargs)
        return cls._self

    @classmethod
    def get_instance(cls):
        if cls._self is None:
            raise ValueError("Chat node not initialized")
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
        self.llm = bm.model_factory(
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

    def get_response(self, state: o.OracleState):
        return {"messages": self.llm.invoke(state["messages"])}
