from typing import Dict, Literal, Optional, overload

from dendrite.logic.llm.agent import LLM

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore # tomllib is only included standard lib for python 3.11+


DEFAULT_LLM = {
    "extract_agent": LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500),
    "scroll_agent": LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500),
    "ask_page_agent": LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500),
    "segment_agent": LLM("gpt-4o", temperature=0, max_tokens=1500),
    "select_agent": LLM("claude-3-5-sonnet-20241022", temperature=0, max_tokens=1500),
    "verify_action_agent": LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500),
}

class LLMConfig():
    def __init__(self, default_agents: Optional[Dict[str, LLM]] = None, default_llm: Optional[LLM] = None):
        self.registered_llms: Dict[str, LLM] = DEFAULT_LLM.copy()
        if default_agents:
            self.registered_llms.update(default_agents)

        self.default_llm = default_llm or LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500)

    async def register_agent(self, agent: str, llm: LLM) -> None:
        """
        Register an LLM agent by name.

        Args:
            agent: The name of the agent to register
            llm: The LLM agent to register
        """
        self.registered_llms[agent] = llm

    async def register(self, agents: Dict[str, LLM]) -> None:
        """
        Register multiple LLM agents at once. Overrides if an agent has already been registered

        Args:
            agents: A dictionary of agent names to LLM agents
        """
        self.registered_llms.update(agents)

    @overload
    def get(self, agent: str) -> LLM: ...

    @overload
    def get(self, agent: str, default: LLM) -> LLM: ...

    @overload
    def get(self, agent: str, default: Optional[LLM] = ..., use_default: Literal[False] = False) -> Optional[LLM]: ...

    def get(
        self,
        agent: str,
        default: Optional[LLM] = None,
        use_default: bool = True,
    ) -> Optional[LLM]:
        """
        Get an LLM agent by name, optionally falling back to default if not found.

        Args:
            agent: The name of the agent to retrieve
            default: Optional specific default LLM to use if agent not found
            use_default: If True, use self.default_llm when agent not found and default is None

        Returns:
            Optional[LLM]: The requested LLM agent, default LLM, or None
        """
        llm = self.registered_llms.get(agent)
        if llm is not None:
            return llm

        if default is not None:
            return default

        if use_default and self.default_llm is not None:
            return self.default_llm

        return None


# Create a single instance
llm_config = LLMConfig()
