import yaml
import json

from tqdm import tqdm

import concurrent.futures

from arg_parser import parse_arguments
from utils import read_text_file, check_output_file_format
from chat_completion import chat_completion_request_runpod
from prompts import json_extract_prompt, yaml_extract_prompt
from json_files.json_validation_aggregation import JsonAggregator
from yaml_files.yaml_validation_aggregation import YamlAggregator

# Read all the arguments
args = parse_arguments()

# Check the output file format
args.output_file_name = check_output_file_format(
    args.output_file_name, args.output_format
)

# Read the text file
text = read_text_file(f"./input_files/{args.input_file_name}")

# # Define variables
block_size: int = args.chunk_length

if args.output_format == "json":
    prompt = f"{json_extract_prompt}"

    # Initialize the JsonAggregator class
    aggregator = JsonAggregator("./json_files/json_schema.json")
elif args.output_format == "yaml":
    prompt = f"{yaml_extract_prompt}"

    # Initialize the YamlAggregator class
    aggregator = YamlAggregator("./yaml_files/yaml_schema.yaml")


# Define a function to send a request
def send_request(message):
    chat_response = chat_completion_request_runpod([message])
    return chat_response, message


# Define a function to process the chat response
def process_chat_response(chat_response, output_format):
    try:
        chat_response_dict = (
            json.loads(chat_response)
            if output_format == "json"
            else yaml.safe_load(chat_response.strip())
        )
        aggregator.aggregate_json(
            chat_response_dict
        ) if output_format == "json" else aggregator.aggregate_yaml(chat_response_dict)
    except (json.JSONDecodeError, yaml.YAMLError):
        print(f"Invalid {output_format.upper()} in chat response: {chat_response}")
        aggregator.fail += 1


# Create messages
message_lists = [
    [
        {
            "role": "user",
            "content": f"""{prompt}\n\n[TEXT_START]\n\n...{text[i : i + block_size]}...\n\n[TEXT_END]\n\nNow, answer immediately and only in {args.output_format} format.""",
        }
    ]
    for i in range(0, len(text), block_size)
]

if args.batching:
    # Initialize a counter
    request_counter = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Send the requests in parallel
        future_to_chat_response = {
            executor.submit(send_request, messages[0]): messages for messages in message_lists
        }

        for future in concurrent.futures.as_completed(future_to_chat_response):
            messages = future_to_chat_response[future]
            try:
                chat_response, _ = future.result()
            except Exception as exc:
                print(f"{messages[0]} generated an exception: {exc}")
            else:
                # Increment the counter
                request_counter += 1

                # Process the chat response
                process_chat_response(chat_response, args.output_format)

    print(f"Total number of requests: {request_counter}")

else:
    for messages in tqdm(message_lists):
        chat_response = chat_completion_request_runpod(messages)

        # Process the chat response
        process_chat_response(chat_response, args.output_format)

# Write the aggregated data to a file
aggregator.write_aggregated_data(f"./outputs/{args.output_file_name}")
if not aggregator.success:
    print("All validations failed")
else:
    total_attempts = aggregator.success + aggregator.fail
    if total_attempts > 0:
        error_rate = aggregator.fail / total_attempts
        print(f"Error rate is {error_rate}")
    else:
        print("No attempts were made, so the error rate cannot be calculated.")
