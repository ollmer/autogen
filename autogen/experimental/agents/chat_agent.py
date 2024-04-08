from typing import List
from autogen.experimental.chat import Chat
from autogen.experimental.types import AssistantMessage, ChatMessage
from ..agent import Agent


class ChatAgent(Agent):
    def __init__(self, chat: Chat):
        self._chat = chat

    @property
    def name(self) -> str:
        """The name of the agent."""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """The description of the agent. Used for the agent's introduction in
        a group chat setting."""
        raise NotImplementedError

    def reset(self) -> None:
        """Reset the agent's state."""
        raise NotImplementedError

    async def generate_reply(
        self,
        messages: List[ChatMessage],
    ) -> ChatMessage:
        for message in messages:
            self._chat.append_message(message)

        while not self._chat.done:
            _ = await self._chat.step()

        return AssistantMessage(content=self._chat.result)