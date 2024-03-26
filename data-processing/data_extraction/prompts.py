import json
import yaml

def read_schema(file_path):
    """Reads a JSON or YAML schema from a given file path."""
    try:
        if file_path.endswith('.json'):
            with open(file_path, "r") as f:
                return json.load(f)
        elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Please use '.json' or '.yaml/.yml'.")
    except Exception as e:
        raise FileNotFoundError(f"Error reading file: {e}")

def generate_example(schema):
    """Generates an example object based on the provided schema."""
    example = {}
    for key, value in schema["properties"].items():
        data_type = value.get("type", "string")
        if isinstance(data_type, list):
            data_type = data_type[0]

        example[key] = {
            "string": f"sample_string",
            "integer": 1,
            "boolean": True,
            "array": generate_array_example(value)
        }.get(data_type, "sample_value")

    return example

def generate_array_example(value):
    """Generates an example array based on the array type in schema."""
    item_type = value.get("items", {}).get("type", "string")
    if isinstance(item_type, list):
        item_type = item_type[0]

    return {
        "string": [f"sample_string_{i+1}" for i in range(2)],
        "integer": [i+1 for i in range(2)],
        "boolean": [True, False]
    }.get(item_type, ["sample_value"])

def create_extract_prompt(schema, data_format):
    """Creates an extraction prompt based on the provided schema and data format."""
    example = generate_example(schema)
    if data_format.lower() == "json":
        schema_str = json.dumps(schema, indent=4)
        example_str = json.dumps(example, indent=4)
    elif data_format.lower() == "yaml":
        schema_str = yaml.dump(schema, default_flow_style=False, indent=4)
        example_str = yaml.dump(example, default_flow_style=False, indent=4)
    else:
        raise ValueError("Unsupported data format. Please use 'JSON' or 'YAML'.")

    prompt = (
        f"Extract names and organizations from the provided text, and return them in {data_format} format. "
        f"Use the following schema:\n\n{schema_str}\n\n"
        f"Here's an example of a response in {data_format} format:\n\n{example_str}\n\n"
        f"Do not include anything that is not explicitly mentioned in the text. "
        f"Analyse the text carefully to ensure all requested data is extracted. "
        f"Include each name and organization only once. "
        f"Adhere strictly to the response format without adding extra spaces or text."
    )
    return prompt

# Example usage
json_schema = read_schema("./json_files/json_schema.json")
yaml_schema = read_schema("./yaml_files/yaml_schema.yaml")

json_extract_prompt = create_extract_prompt(json_schema, "JSON")
yaml_extract_prompt = create_extract_prompt(yaml_schema, "YAML")
