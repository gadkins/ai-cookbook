from termcolor import colored
import os


def pretty_print_conversation(messages):
    role_to_color = {
        "system": "red",
        "user": "green",
        "assistant": "blue",
        "tool": "magenta",
    }

    for message in messages:
        if message["role"] == "system":
            print(
                colored(
                    f"system: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "user":
            print(
                colored(f"user: {message['content']}\n", role_to_color[message["role"]])
            )
            with open("user_request.txt", "w") as file:
                file.write(message["content"] + "\n")
        elif message["role"] == "assistant" and message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['function_call']}\n",
                    role_to_color[message["role"]],
                )
            )
        elif message["role"] == "assistant" and not message.get("function_call"):
            print(
                colored(
                    f"assistant: {message['content']}\n", role_to_color[message["role"]]
                )
            )
        elif message["role"] == "tool":
            print(
                colored(
                    f"function ({message['name']}): {message['content']}\n",
                    role_to_color[message["role"]],
                )
            )


def read_text_file(text_file):
    with open(text_file, "r") as file:
        text = file.read()
    return text


def check_output_file_format(output_file_name, output_format):
    # Check if output_file has an extension
    _, file_extension = os.path.splitext(output_file_name)
    if not file_extension:
        # If not, add extension based on output_format
        output_file_name = f"{output_file_name}.{output_format}"

    return output_file_name
