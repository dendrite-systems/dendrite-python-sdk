from typing import Dict, Literal, Optional, overload

from dendrite.logic.llm.agent import LLM

AGENTS = Literal[
    "extract_agent",
    "scroll_agent",
    "ask_page_agent",
    "segment_agent",
    "select_agent",
    "verify_action_agent",
]

DEFAULT_LLM: Dict[str, LLM] = {
    "extract_agent": LLM(
        "claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500
    ),
    "scroll_agent": LLM("claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500),
    "ask_page_agent": LLM(
        "claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500
    ),
    "segment_agent": LLM("claude-3-haiku-20240307", temperature=0, max_tokens=1500),
    "select_agent": LLM("claude-3-5-sonnet-20241022", temperature=0, max_tokens=1500),
    "verify_action_agent": LLM(
        "claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500
    ),
}


class LLMConfig:
    """
    Configuration class for Language Learning Models (LLMs) in Dendrite.

    This class manages the registration and retrieval of different LLM agents used
    throughout the system. It maintains a registry of LLM configurations for various
    agents and provides a default configuration when needed.

    Attributes:
        registered_llms (Dict[str, LLM]): Dictionary mapping agent names to their LLM configurations
        default_llm (LLM): Default LLM configuration used when no specific agent is found
    """

    def __init__(
        self,
        default_agents: Optional[Dict[str, LLM]] = None,
        default_llm: Optional[LLM] = None,
    ):
        """
        Initialize the LLMConfig with optional default configurations.

        Args:
            default_agents (Optional[Dict[str, LLM]]): Dictionary of agent names to LLM
                configurations to override the default agents. Defaults to None.
            default_llm (Optional[LLM]): Default LLM configuration to use when no
                specific agent is found. If None, uses Claude 3 Sonnet with default settings.
        """
        self.registered_llms: Dict[str, LLM] = DEFAULT_LLM.copy()
        if default_agents:
            self.registered_llms.update(default_agents)

        self.default_llm = default_llm or LLM(
            "claude-3-5-sonnet-20241022", temperature=0.3, max_tokens=1500
        )

    async def register_agent(self, agent: str, llm: LLM) -> None:
        """
        Register a single LLM agent configuration.

        Args:
            agent (str): The name of the agent to register
            llm (LLM): The LLM configuration to associate with the agent
        """
        self.registered_llms[agent] = llm

    async def register(self, agents: Dict[str, LLM]) -> None:
        """
        Register multiple LLM agent configurations at once.

        This method will override any existing agent configurations with the same names.

        Args:
            agents (Dict[str, LLM]): Dictionary mapping agent names to their LLM configurations
        """
        self.registered_llms.update(agents)

    @overload
    def get(self, agent: str) -> LLM: ...

    @overload
    def get(self, agent: str, default: LLM) -> LLM: ...

    @overload
    def get(
        self,
        agent: str,
        default: Optional[LLM] = ...,
        use_default: Literal[False] = False,
    ) -> Optional[LLM]: ...

    def get(
        self,
        agent: str,
        default: Optional[LLM] = None,
        use_default: bool = True,
    ) -> Optional[LLM]:
        """
        Get an LLM configuration by agent name.

        This method attempts to retrieve an LLM configuration in the following order:
        1. From the registered agents
        2. From the provided default parameter
        3. From the instance's default_llm (if use_default is True)

        Args:
            agent (str): The name of the agent whose configuration to retrieve
            default (Optional[LLM]): Specific default LLM to use if agent not found.
                Defaults to None.
            use_default (bool): Whether to use the instance's default_llm when agent
                is not found and no specific default is provided. Defaults to True.

        Returns:
            Optional[LLM]: The requested LLM configuration, or None if not found and
                no defaults are available or allowed.
        """
        llm = self.registered_llms.get(agent)
        if llm is not None:
            return llm

        if default is not None:
            return default

        if use_default and self.default_llm is not None:
            return self.default_llm

        return None
