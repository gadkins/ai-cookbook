import yaml
from jsonschema import validate
from typing import Dict, Any
import jsonschema

class YamlAggregator:
    """
    A class used to aggregate YAML data based on a provided schema.

    ...

    Attributes
    ----------
    schema : Dict[str, Any]
        a dictionary representing the YAML schema
    aggregated_data : Dict[str, Any]
        a dictionary to store the aggregated data

    Methods
    -------
    load_schema(schema_file: str)
        Loads the YAML schema from a file.
    validate_yaml(data: Dict[str, Any])
        Validates the YAML data against the schema.
    aggregate_yaml(yaml_data: Dict[str, Any])
        Aggregates the YAML data.
    write_aggregated_data(output_file: str)
        Writes the aggregated data to a file.
    """

    def __init__(self, schema_file: str):
        self.schema = self.load_schema(schema_file)
        self.aggregated_data = {
            key: [] if self.schema["properties"][key]["type"] == "array" else None
            for key in self.schema["properties"].keys()
        }
        self.success = 0
        self.fail = 0

    def load_schema(self, schema_file: str) -> Dict[str, Any]:
        """Loads the YAML schema from a file."""
        with open(schema_file, "r") as file:
            return yaml.safe_load(file)

    def validate_yaml(self, data: Dict[str, Any]) -> bool:
        """Validates the YAML data against the schema."""
        try:
            validate(instance=data, schema=self.schema)
            print("YAML validation successful!")
            return True
        except jsonschema.exceptions.ValidationError as ve:
            print(f"Invalid yaml error - {ve}")
            return False

    def aggregate_yaml(self, yaml_data: Dict[str, Any]):
        """Aggregates the YAML data."""
        # Validate the YAML data
        is_valid = self.validate_yaml(yaml_data)
        if is_valid:
            self.success += 1
            # Aggregate the data
            for key, value in yaml_data.items():
                if key in self.aggregated_data:
                    # If the key is in the aggregated data, append or update the value based on its type
                    if self.schema["properties"][key]["type"] == "array":
                        # If the value is a list, extend the existing list
                        self.aggregated_data[key].extend(value)
                        # De-duplicate and sort the list
                        self.aggregated_data[key] = sorted(set(self.aggregated_data[key]))
                    else:
                        # If the value is not a list, update the existing value
                        self.aggregated_data[key] = value
        else:
            self.fail += 1

    def write_aggregated_data(self, output_file: str):
        """Writes the aggregated data to a file."""
        with open(output_file, "w") as file:
            yaml.dump(self.aggregated_data, file)
        print(
            f"Aggregation complete! The aggregated data has been written to '{output_file}'."
        )
