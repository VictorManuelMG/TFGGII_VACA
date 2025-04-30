from CUA.tools.class_browser_use import browser
import pytest


def test_initialization():
    """Test the initialization of a object from class BrowserUse"""
    Browser = browser(
        anthropic_model="claude-3-7-sonnet-latest",
        temperature=0,
        timeout=100,
        chrome_instance_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        max_steps=20,
    )

    assert Browser.llm.model == "claude-3-7-sonnet-latest"
    assert Browser.llm.temperature == 0
    assert Browser.llm.default_request_timeout == 100
    assert (
        Browser.chrome_path
        == "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    )
    assert Browser.max_steps == 20


@pytest.mark.asyncio
async def test_init_context():
    """Test the generation of browser and context"""
    Browser = browser()
    await Browser._init_context()

    assert Browser.browser is not None
    assert Browser.context is not None


def test_browser_executable():
    """Cannot test browser_executable as it uses an LLM agent."""
    pass
