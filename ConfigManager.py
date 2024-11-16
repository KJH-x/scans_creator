import json
import os


class ConfigManager:
    """
    Class to manage configuration operations, including loading, saving,
    and creating default configurations if needed.

    Responsibilities:
        - Check if the config file exists and create it if missing.
        - Store default config files.
        - Check if the filepath in the configuration data exists.
        - Load configuration data from the config file.
        - Provide access to configuration data.
        - Update configuration data and save changes.
    """

    def __init__(self) -> None:
        """
        Initializes the ConfigManager with the path to the config file.
        After init, `activate_config()` is needed to run before use.
        """
        # Used for file existence verification in `_validate_file_paths`
        self.common_extensions = ['.png', '.json', ".ttf"]
        self.config_folder: str = "config"
        self.config_files: dict[str] = {
            "basic": os.path.join(self.config_folder, "basic.json"),
            "info_layout": os.path.join(self.config_folder, "info_layout.json")
        }
        
        self._check_configfile()
        self.active_configfile: str = ""

    def _check_configfile(self) -> None:
        """
        Check if the configuration file exists, and create missing files.
        """
        default_config = {
            os.path.join(self.config_folder, "basic.json"): {
                "font_file": "fonts/sans....ttf",
                "font_file_2": "fonts/serif....ttf",
                "logo_file": "logo/logo.png",
                "resize_scale": 2,
                "avoid_leading": True,
                "avoid_ending": True,
                "grid_shape": [
                    4,
                    4
                ]
            },
            os.path.join(self.config_folder, "info_layout.json"): {
                "fonts": [{"path": "fonts/sans....ttf","size": 45},{"path": "fonts/serif....ttf","size": 40}],
                "font_list": [0,1,1,1,1,1,1,1,1],
                "time_font": 1,
                "horizontal_spacing": 20,
                "vertical_spacing": 10,
                "content_margin_left": 30,
                "content_margin_top": 100,
                "title_margin_left": 30,
                "title_margin_top": 10,
                "shade_offset": [2,2],
                "text_color": [0,0,0],
                "shade_color": [49,49,49],
                "text_list": [[{"field": "F","key": "name"}],["　　　　【文件信息】","大　　小：","时　　长：","总比特率："],["",{"field": "F","key": "size"},{"field": "F","key": "duration"},{"field": "F","key": "bitrate"}],["　　　　【视频信息】","编　　码：","色　　彩：","尺　　寸：","帧　　率："],["",{"field": "V","key": "codec"},{"field": "V","key": "color"},{"field": "V","key": "frameSize"},{"field": "V","key": "frameRate"}],["　　　　【音频信息】","编　　码：","音频语言：","音频标题：","声　　道："],["",{"field": "A","key": "codec"},{"field": "A","key": "lang"},{"field": "A","key": "title"},{"field": "A","key": "channel"}],["　　　【字幕信息】","编　　码：","字幕语言：","字幕标题："],["",{"field": "S","key": "codec"},{"field": "S","key": "lang"},{"field": "S","key": "title"}]],
                "pos_list": [[30,10],[30,100],[230,100],[630,100],[830,100],[1330,100],[1530,100],[2030,100],[2230,100]]
            }
        }
        check_flag: bool = True
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
            
        for file_path in self.config_files.values():
            if not os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding='utf-8') as f:
                        json.dump(default_config[file_path], f, indent=4)
                    print(f"Created missing config file: {file_path}")
                    check_flag = False
                except KeyError:
                    print(f"Unknow filename: {file_path}")
                    
        if not check_flag:
            raise ValueError(f"The default configuration file needs to be set before use.")

    def activate_config(self, alias: str):
        config_file = self.config_files.get(alias)
        if config_file:
            self.active_configfile = config_file
            self._load_config()
            print(f"Activated config: {alias} -> {config_file}")
        else:
            print(f"Error: Config alias '{alias}' not found.")

    def _load_config(self) -> None:
        """
        Loads the configuration data from the config file and validates
        file paths for font and logo files.

        Raises:
            FileNotFoundError: If the config file does not exist or if specified
                            file paths for font_file, font_file_2, or logo_file do not exist.
            ValueError: If the config file is not a valid JSON.
        """
        with open(self.active_configfile, 'r', encoding='utf-8') as f:
            try:
                self.config: dict = json.load(f)
                self._validate_file_paths(self.config)
            except json.JSONDecodeError:
                raise ValueError(f"Failed to decode JSON from {self.active_configfile}.")
            except FileExistsError as e:
                raise FileExistsError(e)

    def _validate_file_paths(self, data: dict | list | str) -> None:
        """
        Recursively validates file paths in the given data, checking if any string matches 
        a known file extension from `self.common_extensions` and verifying that the file exists.
        Args:
            data (dict | list | str): The input data to be validated. Can be a dictionary, 
                                    list, or string.
                                    - If it's a dictionary, it recursively checks the values.
                                    - If it's a list, it recursively checks each item.
                                    - If it's a string, it checks if the string is a valid file path.
                                    - otherwise, skip this data.

        Raises:
            FileNotFoundError: If a string is determined to be a file path and the file does 
                                not exist on the filesystem.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                self._validate_file_paths(value)
        
        elif isinstance(data, list):
            for item in data:
                self._validate_file_paths(item)
        
        elif isinstance(data, str):
            if any(data.lower().endswith(ext) for ext in self.common_extensions):
                if not os.path.exists(data):
                    raise FileNotFoundError(f"File does not exist: {data}")

    def update(self, key: str, value) -> bool:
        """
        Update a configuration value.
        ! Not tested
        """
        if hasattr(self, key):
            setattr(self, key, value)
            self.save_config()
            return True
        return False

    def save_config(self) -> None:
        """
        Saves the current configuration data back to the config file.
        ! Not tested
        """
        with open(self.active_configfile, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        print(f"Config file saved at {self.active_configfile}.")

    def __getitem__(self, key):
        return self.config.get(key)
