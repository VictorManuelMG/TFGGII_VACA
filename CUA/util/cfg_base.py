from typing import Literal, Type

from pydantic import BaseModel, model_validator
from pydantic_settings import (
    BaseSettings,
    CliSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from .path import project_root_path


class _LoggerSettings(BaseModel):
    name: str = __name__
    format: str = "%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] [Thread:%(threadName)s] %(message)s"
    loglevel: Literal["NOSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        "DEBUG"
    )
    logdir: str = str((project_root_path() / "logs").resolve())
    max_file_size_mb: int = 512
    max_logfiles: int = 2
    log_current_levels: bool = False


class _VerboseLevel(BaseModel):
    L1: bool = False
    L2: bool = False
    L3: bool = False
    L4: bool = False

    @model_validator(mode="after")
    def enable_previous_levels(self):
        # If a higher level is enabled, enable all lower levels
        if self.L4:
            self.L1 = self.L2 = self.L3 = True
        elif self.L3:
            self.L1 = self.L2 = True
        elif self.L2:
            self.L1 = True

        return self


class CfgBase(BaseSettings):
    cfg_file: str = str((project_root_path() / "cfg/cfg.yaml").resolve())

    logger: _LoggerSettings = _LoggerSettings()
    verbose: _VerboseLevel = _VerboseLevel()

    # Settings configuration:
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=((project_root_path() / ".env").resolve(), ".env", ".env.prod"),
        yaml_file=[cfg_file],
        env_nested_delimiter="__",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        instances: list[PydanticBaseSettingsSource] = []

        # env_settings()
        # cli = CliSettingsSource(
        #     settings_cls, cli_parse_args=True, cli_exit_on_error=False
        # )
        # instances.append(cli)

        yaml = YamlConfigSettingsSource(settings_cls)

        return (
            *instances,
            env_settings,
            dotenv_settings,
            init_settings,
            yaml,
            file_secret_settings,
        )  # ordered by top-down priority
