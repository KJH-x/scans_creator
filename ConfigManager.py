import os
import json
from typing import Dict, Union

class ConfigFileManager:
    """
    Class to manage configuration file operations.

    Responsibilities:
        - Check if the config file exists.
        - Create the config file if it doesn't exist.
        - Handle default config creation.

    Attributes:
        config_file (str): Path to the configuration file.
    """

    def __init__(self, config_file: str) -> None:
        """
        Initializes the ConfigFileManager with the path to the config file.

        Args:
            config_file (str): Path to the configuration file.
        """
        self.config_file: str = config_file

    def check_config_exists(self) -> bool:
        """
        Check if the configuration file exists.

        Returns:
            bool: True if the config file exists, False otherwise.
        """
        return os.path.exists(self.config_file)

    def create_default_config(self) -> None:
        """
        Create the default configuration file with predefined settings.
        This will be called when the config file is missing.
        """
        default_config: Dict[str, Union[str, bool, list]] = {
            "font_file": "fonts/serif.ttf",
            "font_file_2": "fonts/sans.ttf",
            "logo_file": "logo/logo.png",
            "resize": True,
            "grid_size": [4, 4]
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        print(f"Default config file created at {self.config_file}.")

class ConfigManager:
    """
    Class to manage configuration data loaded from a JSON file.

    Responsibilities:
        - Load configuration data from the config file.
        - Provide access to configuration data.
        - Validate and update the configuration if necessary.

    Attributes:
        config_file (str): Path to the configuration file.
        config_data (dict): Loaded configuration data.
    """

    def __init__(self, config_file: str, file_manager: ConfigFileManager) -> None:
        """
        Initializes the ConfigManager with the path to the config file and a ConfigFileManager instance.

        Args:
            config_file (str): Path to the configuration file.
            file_manager (ConfigFileManager): Instance to manage file creation and existence check.
        """
        self.config_file: str = config_file
        self.file_manager: ConfigFileManager = file_manager

        # Ensure the config file exists
        if not self.file_manager.check_config_exists():
            self.file_manager.create_default_config()

        # Load the configuration data
        self.config_data: Dict[str, Union[str, bool, list]] = self.load_config()

    def load_config(self) -> Dict[str, Union[str, bool, list]]:
        """
        Loads the configuration data from the config file.

        Returns:
            dict: The loaded configuration data.

        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is not a valid JSON.
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Config file {self.config_file} not found.")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            try:
                config: Dict[str, Union[str, bool, list]] = json.load(f)
                return config
            except json.JSONDecodeError:
                raise ValueError(f"Failed to decode JSON from {self.config_file}.")

    def get(self, key: str, default: Union[str, bool, list, None] = None) -> Union[str, bool, list, None]:
        """
        Get a configuration value by key.

        Args:
            key (str): The key to look for in the config.
            default: The default value to return if the key is not found.

        Returns:
            The value associated with the key, or the default value.
        """
        return self.config_data.get(key, default)

    def update(self, key: str, value: Union[str, bool, list]) -> bool:
        """
        Update a configuration value.

        Args:
            key (str): The key of the configuration to update.
            value: The new value to set.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if key in self.config_data:
            self.config_data[key] = value
            self.save_config()
            return True
        return False

    def save_config(self) -> None:
        """
        Saves the current configuration data back to the config file.
        """
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f, indent=4)
        print(f"Config file saved at {self.config_file}.")
