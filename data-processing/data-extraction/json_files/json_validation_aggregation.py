import json
import jsonschema
from jsonschema import validate
from typing import Dict, Any

class JsonAggregator:
    def __init__(self, schema_file: str):
        self.schema = self.load_schema(schema_file)
        self.aggregated_data = {key: set() for key in self.schema["properties"].keys()}
        self.success = 0
        self.fail = 0

    def load_schema(self, schema_file: str) -> Dict[str, Any]:
        with open(schema_file, "r") as file:
            return json.load(file)

    def validate_json(self, data: Dict[str, Any]) -> bool:
        try:
            validate(instance=data, schema=self.schema)
            return True
        except jsonschema.exceptions.ValidationError:
            return False

    def aggregate_json(self, json_data: Dict[str, Any]):
        if self.validate_json(json_data):
            self.success += 1
            for key, values in json_data.items():
                if isinstance(values, list):
                    self.aggregated_data[key].update(values)
        else:
            self.fail += 1

    def write_aggregated_data(self, output_file: str):
        final_data = {key: list(value) for key, value in self.aggregated_data.items()}
        with open(output_file, "w") as file:
            json.dump(final_data, file, indent=4)
        print(f"Aggregation complete! The aggregated data has been written to '{output_file}'.")

# Example usage
# aggregator = JsonAggregator("your_schema_file.json")
# aggregator.aggregate_json(your_json_data)
# aggregator.write_aggregated_data("output_file.json")
