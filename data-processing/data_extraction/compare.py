import pandas as pd
import json
import yaml
import argparse

# Argument parsing
parser = argparse.ArgumentParser(description='Process JSON or YAML files.')
parser.add_argument('filetype', choices=['json', 'yaml'], help='The file format to process (json or yaml)')
args = parser.parse_args()

# Function to load schema
def load_schema(filetype):
    filename = f"./{'json' if filetype == 'json' else 'yaml'}_files/{filetype}_schema.{'json' if filetype == 'json' else 'yaml'}"
    with open(filename, 'r') as f:
        if filetype == 'json':
            return json.load(f)
        elif filetype == 'yaml':
            return yaml.safe_load(f)

# Function to load data
def load_data(filetype, filename):
    with open(filename, 'r') as f:
        if filetype == 'json':
            return json.load(f)
        elif filetype == 'yaml':
            return yaml.safe_load(f)

# Function to create dataframes based on keys
def create_dataframe(data, key):
    return pd.DataFrame({key: data[key]}).sort_values(by=key).reset_index(drop=True)

# Load schemas
json_schema = load_schema('json')
yaml_schema = load_schema('yaml')

# Determine keys based on schema
keys = json_schema['properties'].keys() if args.filetype == 'json' else yaml_schema['properties'].keys()

# Load the datasets
data1 = load_data(args.filetype, 'outputs/output.' + args.filetype)
data2 = load_data(args.filetype, 'outputs/gpt4.' + args.filetype)
data3 = load_data(args.filetype, 'outputs/gpt3.5.' + args.filetype)  # Load data for gpt3.5

# Create dataframes for each key
dataframes = {}
for key in keys:
    df1 = create_dataframe(data1, key)
    df2 = create_dataframe(data2, key)
    df3 = create_dataframe(data3, key)  # Create dataframe for gpt3.5 data
    dataframes[key] = pd.DataFrame({'output': df1[key], 'gpt4': df2[key], 'gpt3.5': df3[key]})  # Include gpt3.5 in the dataframe

# Print and save dataframes
for key, df in dataframes.items():
    print(f"{key.capitalize()}:")
    print(df)
    df.to_csv(f'outputs/{key}.csv', index=False)
