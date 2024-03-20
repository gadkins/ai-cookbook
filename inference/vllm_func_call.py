import os
import importlib
import json
from termcolor import colored
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI

# Load environment variables
load_dotenv()

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

openai_api_base = api_endpoint + '/v1'

# Initialize the OpenAI client
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),  # Replace with your actual API key
    base_url=openai_api_base,
)

# Import tools (a list of function metadata) and dynamically import functions
with open('./functions/tools.json', 'r') as file:
    tools = json.load(file)

functions = {
    tool["function"]["name"]: importlib.import_module(f"functions.{tool['function']['name']}").__dict__[tool["function"]["name"]]
    for tool in tools if tool["type"] == "function"
}

def execute_function_call(func_json, functions_dict):
    func_name = func_json.get("name")
    func_arguments = func_json.get("arguments", {})

    if func_name in functions_dict:
        if isinstance(func_arguments, dict):
            results = functions_dict[func_name](**func_arguments)
        else:
            results = "Error: Invalid arguments format"
    else:
        results = f"Error: function {func_name} does not exist"

    return results

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request_vllm(messages, client, recursion_depth=0, max_recursion_depth=4):
    if recursion_depth > max_recursion_depth:
        print("Maximum recursion depth reached")
        return

    try:
        chat_response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            max_tokens=500,
        )

        if chat_response.choices:
            completion_text = chat_response.choices[0].message.content
        else:
            completion_text = None

        function_call_json = None
        try:
            function_call_json = json.loads(completion_text)
        except json.JSONDecodeError as e:
            if not isinstance(completion_text, str):
                completion_text = json.dumps(completion_text, indent=4)
            messages.append({"role": "assistant", "content": completion_text})
            return

        if function_call_json.get("name") is not None:
            messages.append({"role": "function_call", "content": json.dumps(function_call_json, indent=4)})
            results = execute_function_call(function_call_json, functions)

            if not isinstance(results, str):
                results = json.dumps(results, indent=4)

            messages.append({"role": "function_response", "content": results})
            chat_completion_request_vllm(messages, client, recursion_depth + 1, max_recursion_depth)
        else:
            messages.append({"role": "assistant", "content": completion_text})

    except Exception as e:
        print(f"Error in generating response from the server: {e}")

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function_call": "blue",
        "function_response": "green",
    }

    for message in messages:
        if message["role"] in role_to_color:
            print(colored(f"{message['role']}: {message['content']}\n", role_to_color[message["role"]]))

###--- CHAT SCRIPT ---###
messages = []

# Function Metadata
messages.append({"role": "function_metadata", "content": json.dumps(tools, indent=4)})

# User Prompt
# messages.append({"role": "user", "content": "What is the current weather in London?"})
messages.append({"role": "user", "content": "What clothes should I wear? I am in Dublin"})
# messages.append({"role": "user", "content": "What is one plus one?"})

# Get an assistant response
chat_completion_request_vllm(messages, client)

# Print out the messages
pretty_print_conversation(messages)
