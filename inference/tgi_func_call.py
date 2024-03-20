import os
import re
import importlib
import subprocess
import json
import requests
import inspect
from termcolor import colored
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from transformers import AutoTokenizer

load_dotenv()  # This loads the variables from .env

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

tgi_api_base = api_endpoint + '/generate'

## Use this for models that are fine-tuned for function calling
tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

## ONE-SHOT TOKENIZER TEMPLATES (Only works with strong models)
## OpenChat 3.5 (recommended, although less robust than function calling fine-tuned model)
# tokenizer.chat_template="{% for message in messages %}{% if message['role'] == 'function_metadata' %}GPT4 Correct User: You have access to the following functions. Use them if required:\n\n{{ message['content'] }}\n\nIf relevant, make function calls rather than explaining how to make them. Where there is a function call available, you should prefer using the function call over guessing the answer. To call a function, respond - immediately and only - with a JSON object of the following sample format: {\"name\": \"get_current_weather\", \"arguments\": {\"city\": \"London\"}}\n\n{% elif message['role'] == 'user'  and loop.index0 == 1 %}{{ message['content'] }}{{ eos_token }}GPT4 Correct Assistant:{% elif message['role'] == 'assistant' %}{{ message['content'] }}{{ eos_token }}GPT4 Correct User: {% elif message['role'] == 'function_call' %}Function call: {{ message['content'] }}{{ eos_token }}GPT4 Correct User: {% elif message['role'] == 'function_response' %}Here is the response to the function call. If helpful, use it to respond to my question:\n\n{{ message['content'] }}{{ eos_token }}GPT4 Correct Assistant:{% elif message['role'] == 'user'  and loop.index0 != 1 %}{{ message['content'] }}{{ eos_token }}GPT4 Correct Assistant:{% endif %}{% endfor %}"
# # Mixtral - Much less robust than using the function-calling fine-tuned Mixtral model
# tokenizer.chat_template="{{ bos_token }} [INST] {% for message in messages %}{% if message['role'] == 'system' %}<<SYS>>\n{{ message['content'] }}\n<</SYS>>\n\n{% elif message['role'] == 'function_metadata' %}You have access to the following functions. Use them if required:\n\n{{ message['content'] }}\n\nTo call a function, respond with a JSON object in this format: \n{\n \"name\": \"function_name\",\n \"arguments\": {\n \"argument1\": \"value1\",\n \"argument2\": \"value2\"\n }\n}\nRespond with a JSON object only if you wish to make a function call. Any other response will be treated as a regular query. When making a function call, provide only the JSON object, nothing else. Make one function call at a time. After the function call, wait for the response.\n\n{% elif message['role'] == 'user' %}{{ message['content'] }} [/INST]\n\n{% elif message['role'] == 'assistant' %}{{ message['content'] }} [INST] {% elif message['role'] == 'function_call' %}{{ message['content'] }} [INST] {% elif message['role'] == 'function_response' %}Here is the response to the function call. If helpful, use it to respond to my question:\n\n{{ message['content'] }} [/INST]\n\n{% endif %}{% endfor %}"
                                                                                                                                                             
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

    # Check if the function exists
    if func_name not in functions_dict:
        return f"Error: function {func_name} does not exist"

    func = functions_dict[func_name]

    # Validate that provided arguments match the function's expected parameters
    expected_params = set(inspect.signature(func).parameters)
    if set(func_arguments) <= expected_params:
        try:
            return func(**func_arguments)
        except TypeError as e:
            return f"Error: Incorrect arguments provided. {e}"
    else:
        return f"Error: Incorrect argument keys. Expected: {', '.join(expected_params)}"

def test_api_up():
    url = tgi_api_base
    test_payload = json.dumps({"inputs": "Test", "parameters": {"max_new_tokens": 1, "do_sample": False}})

    try:
        response = requests.post(url, data=test_payload, headers={'Content-Type': 'application/json'})
        # If the response status code is 200, the API is up
        if response.status_code == 200:
            print("API is up and running.")
            return True
        else:
            print(f"API is not responding as expected. Status Code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error while checking API status: {e}")
        return False

# @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, recursion_depth=0, max_recursion_depth=2):
    # Check if API is up
    if not test_api_up():
        print("Exiting due to API being down.")
        return
    
    if recursion_depth > max_recursion_depth:
        print("Maximum recursion depth reached")
        return

    formatted_messages = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    print(formatted_messages)

    json_payload = json.dumps({
        "inputs": formatted_messages,
        "parameters": {
            "max_new_tokens": 500,
            "do_sample": False,
            # "stop": ["<step>"] #required for codellama 70b
            }})

    curl_command = f"""
    curl {tgi_api_base} \
        -X POST \
        -d '{json_payload}' \
        -H 'Content-Type: application/json'
    """

    try:
        response = subprocess.run(curl_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        response = response.stdout.decode()
        response = json.loads(response).get("generated_text", "No generated text found")

        function_call_json = None

        # Check if the response contains code block notation
        if response.startswith("```json") and response.endswith("```"):
            # Extract the JSON string
            response = response[7:-3].strip()  # Remove the ```json and ``` markers
        else:
            response = response
            
        # print(response)

        try:
            function_call_json = json.loads(response)
        except json.JSONDecodeError as e:
            # print(f"No JSON object present, {e}")
            if not isinstance(response, str):
                response = json.dumps(response, indent=4)
            messages.append({"role": "assistant", "content": response})
            return

        if function_call_json.get("name") is not None:
            messages.append({"role": "function_call", "content": json.dumps(function_call_json,indent=4)})
            results = execute_function_call(function_call_json, functions)

            if not isinstance(results, str):
                results = json.dumps(results, indent=4)

            messages.append({"role": "function_response", "content": results})
            chat_completion_request(messages, recursion_depth + 1, max_recursion_depth)
        else:
            messages.append({"role": "assistant", "content": response})

    except subprocess.CalledProcessError as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "function_call": "blue",
        "function_response": "green",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant":
            print(colored(f"assistant:{message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function_call":
            print(colored(f"function_call: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "function_response":
            print(colored(f"function_response: {message['content']}\n", role_to_color[message["role"]]))

###--- CHAT SCRIPT ---###
messages = []

# # Function Metadata
messages.append({"role": "function_metadata", "content": json.dumps(tools, indent=4)})

# # System Message
# messages.append({"role": "system", "content": "Do not make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous."})

# User Prompt
messages.append({"role": "user", "content": "What is the current weather in London?"})
# messages.append({"role": "user", "content": "What clothes should I wear? I am in Dublin"})
# messages.append({"role": "user", "content": "What is one plus one?"})

# Get an assistant response
chat_response = chat_completion_request(
    messages
)

# Print out the messages
pretty_print_conversation(messages)