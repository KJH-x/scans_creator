import json
from typing import Dict, List, Union
import os

from ConfigManager import calculate_sha256


def generate_type_annotation(schema):
    """
    Generates Python type annotations from a JSON schema.

    Args:
        schema (dict): JSON schema object.

    Returns:
        str: Python type annotation.
    """
    print(f"Searching {schema}")

    # Handle "anyOf", "oneOf" (Union types)
    if "anyOf" in schema or "oneOf" in schema:
        types = []
        for subschema in schema.get("anyOf", schema.get("oneOf", [])):
            types.append(generate_type_annotation(subschema))
        return " | ".join(types)

    if "type" not in schema:
        # {'path': {'type': 'string'}}
        # if len(keys:=schema.keys()):
        #     keys[0]
        return "Any"  # Fallback to Any if no type is found

    schema_type = schema["type"]

    # Handle basic types
    if schema_type == "string":
        return "str"
    elif schema_type == "integer":
        return "int"
    elif schema_type == "boolean":
        return "bool"
    elif schema_type == "object":
        # If it's an object, check if it has properties
        if "properties" in schema:
            for key in schema["properties"].keys():
                if schema["properties"][key]["type"] != "object":
                    # last recursive
                    return f"Dict[str, {generate_type_annotation(schema['properties'][key])}]"
                else:
                    return (
                        f"Dict[str, {generate_type_annotation({'type': 'object', 'properties': schema['properties']})}]"
                    )
        return "Dict[str, Any]"
    elif schema_type == "array":
        items = schema.get("items")
        if items:
            return f"List[{generate_type_annotation(items)}]"
        return "List[Any]"

    return "Any"  # Fallback to Any


def generate_jsonload_class_with_types(schema_folder, output_file, sha256_value):
    """
    Generates a Python file with a JSONLOAD class, including type annotations, based on a given JSON schema.

    Args:
        schema_folder (str): Path to the JSON schema foler.
        output_file (str): Path to the output Python file.
        sha256_value (str): The SHA-256 of `defaults.json.bak`.
    """
    schema_files = {}
    for root, _, files in os.walk(schema_folder):
        for file in files:
            if file.endswith(".schema.json"):  # Check if file ends with .schema.json
                base_name = file[:-12]  # Remove 11 characters for '.schema.json'
                full_path = os.path.join(root, file)
                schema_files[base_name] = full_path

    # "\t" will be replaced before output
    class_content = [
        "# This file is generated by ConfigPorperties.generator.py, do not modify this file directly.",
        "import os",
        "from typing import List, Any, Dict",
        "",
        "class Report:",
        "\tdef __init__(self) -> None:",
        "\t\t# ==================================================================================================",
        "\t\t# Just paste it into `ConfigManager.__init__()`",
    ]

    class_content.append("\t\t")
    class_content.append(f'\t\tself.defaults_SHA256 = "{sha256_value}"')
    class_content.append("\t\t")

    class_content.append("\t\tself.config_files: Dict[str, str] = {")
    for alias, _ in schema_files.items():
        class_content.append(f'\t\t\t"{alias}": os.path.join(self.config_folder, "{alias}.json"),')
    class_content[-1] = class_content[-1][:-1]  # remove ","
    class_content.append("\t\t}")

    class_content.append("\t\tself.config_schema_files: Dict[str, str] = {")
    for alias, _ in schema_files.items():
        class_content.append(f'\t\t\t"{alias}": os.path.join(self.config_schema_folder, "{alias}.schema.json"),')
    class_content[-1] = class_content[-1][:-1]  # remove ","
    class_content.append("\t\t}")

    class_content.append("")
    class_content.append(
        "\t\t# =================================================================================================="
    )
    class_content.append("\t\t# Just paste it into `ConfigManager._load_config()`")
    class_content.append("")

    for alias, path in schema_files.items():
        # Load the JSON schema
        with open(path, "r") as f:
            schema: Dict = json.load(f)

        # Extract properties from the schema
        properties: Dict = schema.get("properties", {})

        # Generate class properties, initialization and type annotations

        class_content.append(f'\t\tif self.active_configfile == os.path.join(self.config_folder, "{alias}.json"):')

        # Add properties with type annotations and initialization
        for prop, details in properties.items():
            type_annotation = generate_type_annotation(details)
            class_content.append(
                f"\t\t\tself.{prop}: {type_annotation} = self.config.get('{prop}', None)  # {details.get('description', '')}"
            )

        class_content.append("")
        # Add a method to display the loaded configuration (optional)
        # class_content.extend([
        #     "",
        #     "    def __repr__(self) -> str:",
        #     "        return str(self.__dict__)",
        # ])

        # Write the generated class to a file
        with open(output_file, "w") as f:
            result_content = "\n".join(class_content)
            result_content = result_content.replace("\t", "    ")
            f.write(result_content)

        print(f"Generated JSONLOAD class with type annotations in {output_file}")


if __name__ == "__main__":
    file_path = os.path.join("schemas", "defaults.json.bak")
    sha256_value = calculate_sha256(file_path)

    generate_jsonload_class_with_types("schemas", "ConfigPorperties.report.py", sha256_value)
