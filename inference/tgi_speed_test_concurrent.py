import threading
import os
import json
import time
import requests
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from transformers import AutoTokenizer

# Load environment variables
load_dotenv()

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

tgi_api_base = api_endpoint + '/generate'

tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

# # Manually adjust the prompt. Not Recommended. Here is Vicuna 1.1 prompt format. System messages not supported.
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

# @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request_threaded(messages, request_number):
    # formatted_messages = format_messages(messages)

    formatted_messages = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    json_payload = {"inputs": formatted_messages, "parameters": {"max_new_tokens": 500, "do_sample": False}}

    start_time = time.time()  # Start timing

    try:
        response = requests.post(tgi_api_base, json=json_payload)
        response_time = time.time() - start_time  # Calculate response time

        if response.status_code == 200:
            response_content = response.json().get("generated_text", "No generated text found")
        else:
            raise Exception(f"Request failed with status code {response.status_code}")

        # print(response_content)

        # Calculate tokens per second
        tokens_generated = len(response_content) / 4
        tokens_per_second = tokens_generated / response_time if response_time > 0 else 0

        # Print time taken and tokens per second for each request
        print(f"Request #{request_number}: Total Time: {response_time:.2f} seconds, Tokens per Second: {tokens_per_second:.2f}")

        return response_content
    except Exception as e:
        print(f"Unable to generate ChatCompletion response for Request #{request_number}")
        print(f"Exception: {e}")
        return str(e)

def send_request_every_x_seconds(interval, total_requests):
    for i in range(total_requests):
        threading.Timer(interval * i, send_request, args=(i+1,)).start()

def send_request(request_number):
    messages = [
        {"role": "user", "content": "Write a long essay on the topic of spring."}
    ]
    chat_completion_request_threaded(messages, request_number)

# Start sending requests every x seconds
send_request_every_x_seconds(0.125, 25)  # Modify as needed for your use case