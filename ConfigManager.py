import json
import os


class ConfigManager:
    """
    Class to manage configuration operations, including loading, saving,
    and creating default configurations if needed.

    Responsibilities:
        - Check if the config file exists and create it if missing.
        - Load configuration data from the config file.
        - Provide access to configuration data.
        - Update configuration data and save changes.

    Attributes:
        config_path (str): Path to the configuration file.
        font_file (str): Path to the font file.
        font_file_2 (str): Path to the second font file.
        logo_file (str): Path to the logo file.
        resize_scale (int): Scale for resize (resize to 1/resize_scale both in w and h).
        avoid_leading (bool): Whether to avoid leading or not.
        avoid_ending (bool): Whether to avoid ending or not.
        grid_shape (tuple[int, int]): Grid size configuration.
    """

    def __init__(self, config_path: str) -> None:
        """
        Initializes the ConfigManager with the path to the config file.

        Args:
            config_path (str): Path to the configuration file.
        """
        self.config_path: str = config_path

        # Ensure the config file exists; create a default one if missing
        if not self._check_config_exists():
            self._create_default_config()
            raise FileNotFoundError("No config yet")

        # Load the configuration data into individual attributes
        self.font_file: str
        self.font_file_2: str
        self.logo_file: str
        self.resize_scale: int
        self.avoid_leading: bool
        self.avoid_ending: bool
        self.grid_shape: tuple[int, int]

        self._load_config()

    def _check_config_exists(self) -> bool:
        """
        Check if the configuration file exists.

        Returns:
            bool: True if the config file exists, False otherwise.
        """
        return os.path.exists(self.config_path)

    def _create_default_config(self) -> None:
        """
        Create the default configuration file with predefined settings.
        Called when the config file is missing.
        """
        default_config = {
            "font_file": "fonts/serif.ttf",
            "font_file_2": "fonts/sans.ttf",
            "logo_file": "logo/logo.png",
            "resize_scale": 2,
            "avoid_leading": True,
            "avoid_ending": True,
            "grid_shape": (4, 4)
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        print(f"Default config file created at {self.config_path}.")

    def _load_config(self) -> None:
        """
        Loads the configuration data from the config file and validates
        file paths for font and logo files.

        Raises:
            FileNotFoundError: If the config file does not exist or if specified
                            file paths for font_file, font_file_2, or logo_file do not exist.
            ValueError: If the config file is not a valid JSON.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file {self.config_path} not found.")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                # Assign each config value to its respective instance variable
                self.font_file = config.get("font_file", "fonts/serif.ttf")
                self.font_file_2 = config.get("font_file_2", "fonts/sans.ttf")
                self.logo_file = config.get("logo_file", "logo/logo.png")
                self.resize_scale = config.get("resize_scale", 2)
                self.avoid_leading = config.get("avoid_leading", True)
                self.avoid_ending = config.get("avoid_ending", True)
                self.grid_shape = tuple(config.get("grid_shape", (4, 4)))

                # Validate the file paths for font and logo files
                if not os.path.exists(self.font_file):
                    raise FileNotFoundError(f"Font file not found at {self.font_file}")
                if not os.path.exists(self.font_file_2):
                    raise FileNotFoundError(f"Second font file not found at {self.font_file_2}")
                if not os.path.exists(self.logo_file):
                    raise FileNotFoundError(f"Logo file not found at {self.logo_file}")

            except json.JSONDecodeError:
                raise ValueError(f"Failed to decode JSON from {self.config_path}.")

    def update(self, key: str, value) -> bool:
        """
        Update a configuration value.

        Args:
            key (str): The key of the configuration to update.
            value: The new value to set.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if hasattr(self, key):
            setattr(self, key, value)
            self.save_config()
            return True
        return False

    def save_config(self) -> None:
        """
        Saves the current configuration data back to the config file.
        """
        config = {
            "font_file": self.font_file,
            "font_file_2": self.font_file_2,
            "logo_file": self.logo_file,
            "resize_scale": self.resize_scale,
            "avoid_leading": self.avoid_leading,
            "avoid_ending": self.avoid_ending,
            "grid_shape": self.grid_shape
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"Config file saved at {self.config_path}.")
