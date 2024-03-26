import os
import subprocess
import json
import time
from dotenv import load_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt
from transformers import AutoTokenizer

# This loads the variables from .env
load_dotenv()

# Retrieve the env variables
model, api_endpoint = os.getenv("MODEL"), os.getenv("API_ENDPOINT")

tgi_api_base = api_endpoint + "/generate"

tokenizer = AutoTokenizer.from_pretrained(model, trust_remote_code=True)

# # Manual chat template
# tokenizer.chat_template = '''{% if not add_generation_prompt is defined %}{% set add_generation_prompt = false %}{% endif %}{%- set ns = namespace(found=false) -%}{%- for message in messages -%}{%- if message['role'] == 'system' -%}{%- set ns.found = true -%}{%- endif -%}{%- endfor -%}{{bos_token}}{%- if not ns.found -%}{# Suppressed System Message #}{%- endif %}{%- for message in messages %}{%- if message['role'] != 'system' %}{%- if message['role'] == 'user' %}{{'### Instruction:\\n' + message['content'] + '\\n'}}{%- else %}{{'### Response:\\n' + message['content'] + '\\n\\n'}}{%- endif %}{%- endif %}{%- endfor %}{% if add_generation_prompt %}{{'### Response:'}}{% endif %}'''

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request_runpod(messages):
    # formatted_messages = format_messages(messages)

    formatted_messages = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    print(formatted_messages)

    # Properly escape the string for JSON and for shell execution
    json_payload = json.dumps(
        {
            "inputs": formatted_messages,
            "parameters": {
                "max_new_tokens": 500,
                "do_sample": False,
                # "repetition_penalty": 1.1, #can be useful for json, less so for yaml.
            },
        }
    )
    escaped_json_payload = json_payload.replace(
        "'", "'\\''"
    )  # Escape single quotes for shell

    start_time = time.time()  # Start timing

    try:
        # Execute the curl command
        curl_command = f"curl -s {tgi_api_base} -X POST -d '{escaped_json_payload}' -H 'Content-Type: application/json'"

        response = subprocess.run(
            curl_command, shell=True, check=True, stdout=subprocess.PIPE
        )
        response_time = time.time() - start_time  # Calculate response time

        response = response.stdout.decode()

        # print(response)

        response = json.loads(response).get("generated_text", "No generated text found")

        # Calculate tokens per second
        tokens_generated = len(response) / 4  # assuming 4 characters per word
        tokens_per_second = tokens_generated / response_time if response_time > 0 else 0

        # Print time taken and tokens per second
        print(f"Tokens generated: {tokens_generated:.2f}")
        print(f"Total Time Taken: {response_time:.2f} seconds")
        print(f"Tokens per Second: {tokens_per_second:.2f}")
        print(response)

        return response
    except subprocess.CalledProcessError as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return str(e)
