import json
from pathlib import Path
from typing import Dict

from pydantic import ValidationError

from ..models.global_config import GlobalConfig
from ..models.info_layout import InfoLayout
from ..utils.common import calculate_sha256
from ..utils.console import log


class _ConfigManager:
    """
    Class to manage configuration operations.
    """

    def __init__(self) -> None:
        self.defaults_SHA256 = "51d95f6580267b608add99c3945fe7da29dbb3004ba2320427fc09f62c1ca82e"
        self.CONFIG_ROOT = Path(__file__).parents[2] / "config"

        self._check_configfile()

    def _check_configfile(self) -> None:
        """
        Check if the configuration file exists, and create missing files.
        """
        back_config_path = self.CONFIG_ROOT / "schemas/defaults.json.bak"
        if calculate_sha256(back_config_path) != self.defaults_SHA256:
            raise ValueError(f"Checksum mismatch for {back_config_path}. The file may have been modified.")

        with open(back_config_path, "r", encoding="utf-8") as file:
            defaults: Dict[str, Dict] = json.load(file)

        # filter out developer-only keys
        defaults = {k: v for k, v in defaults.items() if not k.startswith("_")}

        for fname, cfg in defaults.items():
            dest: str = cfg.pop("_dest", "config")
            target_path = self.CONFIG_ROOT.parent / dest / fname
            if not target_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2, ensure_ascii=False)
                log.warn(f"Created default configuration file: {target_path}. Please review and modify its content.")

    def load_config(self, layout_name: str) -> None:
        """
        Loads the configuration data from the config file and validates by Pydantic.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is not valid.
        """
        try:
            self.config = GlobalConfig.model_validate_json(
                (self.CONFIG_ROOT / "global.json").read_text(encoding="utf-8")
            )
            self.layout = InfoLayout.model_validate_json(
                (self.CONFIG_ROOT / "layout" / layout_name).with_suffix(".json").read_text(encoding="utf-8")
            )

            # cross-model validation
            max_index = len(self.config.fonts) - 1
            if any(idx > max_index or idx < 0 for idx in self.layout.font_list):
                raise ValueError(f"Config validation failed:\nfont_list contains index out of bounds (max {max_index})")
            if self.layout.time_font > max_index or self.layout.time_font < 0:
                raise ValueError(f"Config validation failed:\ntime_font index out of bounds (max {max_index})")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Config file not found: {e}")

        except ValidationError as e:
            raise ValueError(f"Config validation failed:\n{e}")

        log.info(f"Configuration loaded successfully from layout: {layout_name}")


config_manager = _ConfigManager()
log.debug(
    f"ConfigManager initialized with name {__name__} (id: {id(config_manager)}). m"
    f"(If you see this message multiple times, the singleton may fail.)"
)
