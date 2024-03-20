import os
import subprocess
import json
from termcolor import colored
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()  # This loads the variables from .env

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

tgi_api_base = api_endpoint + '/generate'

# # SET UP PROMPT FORMAT
# Llama 2 or Mistral
B_SYS = "<<SYS>>\n"
E_SYS = "\n<</SYS>>\n\n"
B_INST = "[INST] "
E_INST = " [/INST]\n\n"
BOS_token = "<s>"
EOS_token = "</s>"

# # OpenChat format
# B_INST, E_INST = "GPT4 Correct User: ", "<|end_of_turn|>GPT4 Correct Assistant:\n\n" #OpenChat style
# B_SYS = ""
# E_SYS = ""
# EOS_token = "<|end_of_turn|>"
# BOS_token = ""

# # Yi
# ## There is no system prompt possible
# B_INST, E_INST = "Human: ", " Assistant:" #Yi Style for function calling, no training space
# EOS_token = "<|endoftext|>"
# BOS_token = ""

# # # DeepSeek
# # ## There is no system prompt possible
# B_INST, E_INST = "User: ", "\n\nAssistant:" #Deepseek
# EOS_token = "<｜end▁of▁sentence｜>"
# BOS_token = ""

def format_messages(messages):
    formatted_string = ''
    formatted_string += BOS_token
    formatted_string += B_INST

    for message in messages:
        if message['role'] == 'system':
            formatted_string += B_SYS
            formatted_string += message['content']
            formatted_string += E_SYS
        elif message['role'] in ['user']:
            formatted_string += message['content']
            formatted_string += E_INST
        elif message['role'] in ['assistant']:
            formatted_string += message['content']
            formatted_string += EOS_token
            formatted_string += BOS_token
            formatted_string += B_INST

    return formatted_string

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request_runpod(messages):
    formatted_messages = format_messages(messages)

    # Properly escape the string for JSON
    json_payload = json.dumps({"inputs": formatted_messages, "parameters": {"max_new_tokens": 50}})

    # Construct the curl command
    curl_command = f"""
    curl {tgi_api_base} \
        -X POST \
        -d '{json_payload}' \
        -H 'Content-Type: application/json'
    """

    try:
        # Execute the curl command
        response = subprocess.run(curl_command, shell=True, check=True, stdout=subprocess.PIPE)
        response = response.stdout.decode()
        response = json.loads(response).get("generated_text", "No generated text found")
        return response
    except subprocess.CalledProcessError as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return str(e)
    
def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        if message["role"] == "system":
            print(colored(f"system: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "user":
            print(colored(f"user: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and message.get("function_call"):
            print(colored(f"assistant: {message['function_call']}\n", role_to_color[message["role"]]))
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(colored(f"assistant: {message['content']}\n", role_to_color[message["role"]]))
        elif message["role"] == "tool":
            print(colored(f"function ({message['name']}): {message['content']}\n", role_to_color[message["role"]]))

# Chat
messages = []
messages.append({"role": "system", "content": "You are a helpful assistant."})
messages.append({"role": "user", "content": "Count to ten please?"})

chat_response = chat_completion_request_runpod(messages)
messages.append({"role": "assistant", "content": chat_response})

pretty_print_conversation(messages)