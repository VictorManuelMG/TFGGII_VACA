from pydantic import field_validator

from .util.cfg_base import CfgBase


class Cfg(CfgBase):
    openai_api_base: str = "https://api.openai.com/v1/"
    openai_api_key: str = "sk"

    temperature: float = 0.7

    port: int = 8080

    @field_validator("openai_api_key")
    def validate_api_key(cls, v):
        if not v or v.strip() == "":
            raise ValueError("OpenAI API key cannot be empty")
        return v.strip()


_CFG_INSTANCE: Cfg | None = None


def _init_cfg():
    global _CFG_INSTANCE
    default = Cfg()

    _CFG_INSTANCE = default


def get_cfg() -> Cfg:
    """Get the current CFG instance.

    Returns:
        Cfg: Cfg Instance. Can be mutated
    """
    global _CFG_INSTANCE
    if _CFG_INSTANCE is None:
        _init_cfg()
    assert _CFG_INSTANCE is not None
    return _CFG_INSTANCE
