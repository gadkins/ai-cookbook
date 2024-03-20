import os
import subprocess
import json
import time
from termcolor import colored
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from transformers import AutoTokenizer

load_dotenv()  # This loads the variables from .env

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

tgi_api_base = api_endpoint + '/generate'

tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

# # ## Manually adjust the prompt. Not Recommended. Here is Vicuna 1.1 prompt format. System messages not supported.
# tokenizer.chat_template = "{% set sep = ' ' %}{% set sep2 = '</s>' %}{{ 'A chat between a curious user and an artificial intelligence assistant.\n\nThe assistant gives helpful, detailed, and polite answers to user questions.\n\n' }}{% if messages[0]['role'] == 'system' %}{{ '' }}{% set start_index = 1 %}{% else %}{% set start_index = 0 %}{% endif %}{% for i in range(start_index, messages|length) %}{% if messages[i]['role'] == 'user' %}{{ 'USER:\n' + messages[i]['content'].strip() + (sep if i % 2 == start_index else sep2) }}{% elif messages[i]['role'] == 'assistant' %}{{ 'ASSISTANT:\n' + messages[i]['content'].strip() + (sep if i % 2 == start_index else sep2) }}{% endif %}{% endfor %}{% if add_generation_prompt %}{{ 'ASSISTANT:\n' }}{% endif %}"

# # OPTION TO MANUALLY FORMAT MESSAGES (INSTEAD OF USING tokenizer.apply_chat_template)
# B_SYS = "<<SYS>>\n"
# E_SYS = "\n<</SYS>>\n\n"
# B_INST = "[INST] "
# E_INST = " [/INST]\n\n"
# BOS_token = "<s>"
# EOS_token = "</s>"

# def format_messages(messages):
    # formatted_string = ''
    # formatted_string += BOS_token
    # formatted_string += B_INST

    # for message in messages:
    #     if message['role'] == 'system':
    #         formatted_string += B_SYS
    #         formatted_string += message['content']
    #         formatted_string += E_SYS
    #     elif message['role'] in ['user']:
    #         formatted_string += message['content']
    #         formatted_string += E_INST
    #     elif message['role'] in ['assistant']:
    #         formatted_string += message['content']
    #         formatted_string += EOS_token
    #         formatted_string += BOS_token
    #         formatted_string += B_INST

    # return formatted_string

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request_runpod(messages):
    # formatted_messages = format_messages(messages)

    formatted_messages = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # print(formatted_messages)

    # Properly escape the string for JSON
    json_payload = json.dumps({
        "inputs": formatted_messages,
        "parameters": {
            "max_new_tokens": 500,
            "do_sample": False,
            # "stop": ["<step>"] #required for codellama 70b
            }})

    start_time = time.time()  # Start timing

    try:
        # Execute the curl command
        curl_command = f"""
        curl -s {tgi_api_base} \
            -X POST \
            -d '{json_payload}' \
            -H 'Content-Type: application/json'
        """

        response = subprocess.run(curl_command, shell=True, check=True, stdout=subprocess.PIPE)
        response_time = time.time() - start_time  # Calculate response time

        response = response.stdout.decode()
        response = json.loads(response).get("generated_text", "No generated text found")

        # # Log the first and last 25 characters and the response time
        # print(f"Response Time: {response_time} seconds")
        # print(f"Start of Response: {response[:25]}")
        # print(f"End of Response: {response[-25:]}")

        # Calculate tokens per second
        tokens_generated = len(response)/4  # Assuming each word is a token
        tokens_per_second = tokens_generated / response_time if response_time > 0 else 0
        prompt_tokens = chat_response.usage.prompt_tokens if completion_text else 0

        # Print promt and generated tokens, time taken and tokens per second
        print(f"Total Time: {response_time:.2f} seconds")
        print(f"Prompt Tokens: {prompt_tokens:.2f}")
        print(f"Tokens Generated: {tokens_generated:.2f}")
        print(f"Tokens per Second: {tokens_per_second:.2f}")

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
# messages.append({"role": "system", "content": "You are a helpful assistant."})
messages.append({"role": "user", "content": "Write a long essay on the topic of spring."})
# messages.append({"role": "user", "content": "Write a short piece of python code to add up the first 10 prime fibonacci numbers."})

chat_response = chat_completion_request_runpod(messages)
messages.append({"role": "assistant", "content": chat_response})

pretty_print_conversation(messages)