import uuid
from typing import Dict, List, Optional


class SessionManager:
    """
    Manages conversational memory for multi-turn chat sessions.
    """
    def __init__(self, max_history_turns: int = 5):
        self.max_history_turns = max_history_turns
        self._sessions: Dict[str, List[Dict[str, str]]] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        if not session_id or session_id not in self._sessions:
            session_id = str(uuid.uuid4())
            self._sessions[session_id] = []
        return session_id

    def add_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        if session_id not in self._sessions:
            self._sessions[session_id] = []

        self._sessions[session_id].append({"role": "user", "content": user_message})
        self._sessions[session_id].append({"role": "assistant", "content": assistant_message})

        # Trim history to max_history_turns (2 messages per turn)
        max_messages = self.max_history_turns * 2
        if len(self._sessions[session_id]) > max_messages:
            self._sessions[session_id] = self._sessions[session_id][-max_messages:]

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return self._sessions.get(session_id, [])

    def format_history_for_prompt(self, session_id: str) -> str:
        history = self.get_history(session_id)
        if not history:
            return "No previous conversation."

        formatted = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]


# Singleton session manager
session_manager = SessionManager()
