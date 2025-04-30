from langchain_anthropic import ChatAnthropic
import asyncio
from browser_use import Agent, Browser, BrowserConfig, BrowserContextConfig
from dotenv import load_dotenv


load_dotenv()


class browser:
    def __init__(
        self,
        anthropic_model: str = "claude-3-7-sonnet-latest",
        temperature: float = 0.0,
        timeout: int = 30,
        chrome_instance_path: str = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        max_steps: int = 75,
    ):
        """Initialization of browser_use agent.

        Args:
            anthropic_model (str, optional): Claude model for the agent reasoning. Defaults to "claude-3-7-sonnet-latest".
            temperature (float, optional): Temperature for the LLM. Defaults to 0.0.
            timeout (int, optional): Timeout X time in seconds passed. Defaults to 30.
            chrome_instance_path (_type_, optional): Chrome executable location to launch local chrome. Defaults to "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe".
            max_steps (int, optional): Max steps given by the user for the agent. Defaults to 8.
        """
        self.llm = ChatAnthropic(
            model_name=anthropic_model, temperature=temperature, timeout=timeout
        )  # type: ignore
        self.chrome_path = chrome_instance_path

        self.browser = Browser(
            config=BrowserConfig(
                headless=False,
                disable_security=True,
                _force_keep_browser_alive=True,
                chrome_instance_path=self.chrome_path,
                cdp_url="http://localhost:9222",
            )
        )

        self.max_steps = max_steps

        self.context_config = BrowserContextConfig(
            wait_for_network_idle_page_load_time=10,
            highlight_elements=False,
            viewport_expansion=500,
            _force_keep_context_alive=True,
        )

        self.context = None

    async def _init_context(self):
        """Initialization of context and browser, if it already exists it's deleted and reinizialitated again to keep the agent over the same browser."""
        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()

        self.browser = Browser(
            config=BrowserConfig(
                headless=False,
                disable_security=True,
                _force_keep_browser_alive=True,
                chrome_instance_path=self.chrome_path,
                cdp_url="http://localhost:9222",
            )
        )
        self.context = await self.browser.new_context(config=self.context_config)

    async def browser_executable(self, order: str):
        """Execution of browser user agent given a user's order.

        Args:
            order (str): Order given by the user to do over the web browser.

        Returns:
            final_result: returns the final result of the search or a message telling the user it couldn't do what he told it to.
        """
        cooldown_flag = False
        await self._init_context()
        fail_reason = None
        agent = Agent(
            task=order,
            llm=self.llm,
            browser=self.browser,
            browser_context=self.context,
            use_vision=True,
            max_failures=1,
        )

        for step in range(self.max_steps):
            prev_len = len(agent.state.history.history)
            await agent.step()

            for loop in range(10):
                await asyncio.sleep(0.1)
                if len(agent.state.history.history) > prev_len:
                    break

            if agent.state.history.is_done():
                break

            last = agent.state.history.history[-1]
            if "Failed:" in last.model_output.current_state.evaluation_previous_goal:  # type: ignore
                fail_reason = last.model_output.current_state.evaluation_previous_goal  # type:ignore
                break
            
            if "Error:" in last.model_output.current_state.evaluation_previous_goal:  # type: ignore
                fail_reason = last.model_output.current_state.evaluation_previous_goal  # type:ignore
                break

        if fail_reason is not None:
            cooldown_flag = True
            return (
                f"There's been a fail: {agent.state.history.final_result()} \nTry another approach as browser_use cannot overcome this.",
                cooldown_flag,
            )

        else:
            final_result = (
                agent.state.history.final_result() or "No se pudo obtener resultado"
            )

            return final_result, cooldown_flag
