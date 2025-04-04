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

    def get_thread_config(self):
        return {"configurable": {"thread_id": self.thread_id}}
