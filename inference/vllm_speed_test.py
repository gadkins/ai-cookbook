from openai import OpenAI
import os
import time
from dotenv import load_dotenv
from termcolor import colored

# Load environment variables
load_dotenv()

# Retrieve the env variables
model = os.getenv('MODEL')
api_endpoint = os.getenv('API_ENDPOINT')

openai_api_base = api_endpoint + '/v1'

# Initialize the OpenAI client
client = OpenAI(
    api_key="EMPTY",  # Replace with your actual API key if required
    base_url=openai_api_base,
)

def chat_completion_request_openai(messages, client):
    start_time = time.time()  # Start timing

    # Create chat completions using the OpenAI client
    chat_response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        max_tokens=500
    )

    response_time = time.time() - start_time  # Calculate response time

    # Extract the completion text from the response
    if chat_response.choices:
        completion_text = chat_response.choices[0].message.content
    else:
        completion_text = None

    # Calculate tokens per second
    prompt_tokens = chat_response.usage.prompt_tokens if completion_text else 0
    tokens_generated = chat_response.usage.completion_tokens if completion_text else 0
    tokens_per_second = tokens_generated / response_time if response_time > 0 else 0

    # print(chat_response)

    # Print time taken and tokens per second
    print(f"Total Time: {response_time:.2f} seconds")
    print(f"Prompt Tokens: {prompt_tokens:.2f}")
    print(f"Tokens Generated: {tokens_generated:.2f}")
    print(f"Tokens per Second: {tokens_per_second:.2f}")

    return completion_text

def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }
    
    for message in messages:
        color = role_to_color.get(message["role"], "grey")
        print(colored(f"{message['role']}: {message['content']}\n", color))

# Test the function
messages = [
    {"role": "user", "content": "Write a long essay on the topic of spring."}
]

chat_response = chat_completion_request_openai(messages, client)
messages.append({"role": "assistant", "content": chat_response})

pretty_print_conversation(messages)