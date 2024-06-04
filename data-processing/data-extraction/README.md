# Data Extraction
This folder provides methods for extracting structured data from text.

Features:
- Extract data in JSON or YAML format.
- JSON and YAML structure validation.
- Concurrent requests (for faster and cheaper processing than GPT4).
- Extraction from unlimited length text, via chunking.

> Note: For json, using a repetition penalty of 1.1 within chat_completion.py is recommended. No repetition penalty is recommended for YAML.

Supported models:
- All HuggingFace models are supported, although OpenChat 3.5 (original, not 0106) is highly recommended.
- Deploy a one-click TGI API for [OpenChat 3.5 7B](https://runpod.io/gsc?template=xiwn7cb3ro&ref=jmfkcdio) or check out the [one-click-llms](https://github.com/TrelisResearch/one-click-llms) repo for other one-click templates.

## Getting started
- Launch the runpod, using the OpenChat runpod template here: [OpenChat 3.5 7B API](https://runpod.io/gsc?template=xiwn7cb3ro&ref=jmfkcdio).
- Modify the .env file of this repo to comment in the runpod tgi endpoint. Make sure to update the pod id.
- 'cd' into the 'data_extraction' folder of this repo and create a python virtual environment, activate the environment and install requirements.txt . See below for more details.
- Place input file in the input_files folder. Default is berkshire23_60k.txt.
- Define the JSON/YAML schema into `./json_files/json_schema.json` or `./yaml_files/yaml_schema.yaml`. Adjust the `prompts.py` file as needed. The same schema will be used into prompt and for validation.

## Here are some sample commands:
```
## Activating the python virtual environment
###  Instructions differ a little for Windows. Use ChatGPT for assistance.
## Run these commands from the data_extraction folder

python -m venv extractEnv

source extractEnv/bin/activate

pip install -r requirements.txt

# to send requests JSON, chunk_length is measured in characters (not tokens). [To tweak performance, try setting repetition_penalty to 1.1 in chat_completion.py .]
python tgi-data-extraction.py --chunk_length 8000 --output_format json --output_file_name output --batching True --input_file_name berkshire23_60k.txt

# to send requests YAML.
python tgi-data-extraction.py --chunk_length 8000 --output_format yaml --output_file_name output --batching True --input_file_name berkshire23_60k.txt
```

Usage Guide:

- `--chunk_length`: This argument sets the number of characters for chunking the text from which you are extracting. The default value is 8000, and the maximum value is 30000. 8000 characters is about 2k tokens and is where models trained on 4k tend to perform best.

- `--output_format`: This argument sets the output format. The options are 'yaml' and 'json'. The default is 'json'.

- `--output_file_name`: This argument sets the output file name. The default is 'output'.

- `--batching`: This argument sets whether to use batching.  The default is True. If batching is False, then the model will make sequential calls to the LLM with text lengths of chunk_length. If batching is true, then concurrent requests will be sent to LLM.

- `--input_file_name`: This argument sets the input file name. The default is 'berkshire23_60k.txt', which has 60k characters (about 15k tokens).

- Progress will be shown in your terminal
- Failed validations will be shown. The error rate will be shown at the end.
- The final compiled output will be stored in `./outputs/output.json` or `./outputs/output.yaml` (unless you specify a different output file name)

## Running Performance Comparisons
First, copy paste the exact command (including the text from which to extract) into ChatGPT or a GPT4 or GPT3.5 request. Paste the yaml or json response into outputs/gpt4.json or outputs/gpt4.yaml (this is already done if you run the default commands above for berkshire23_12.5k.txt).

Then, run either:
```
python compare.py json
```
or
```
python compare.py yaml
```
to compare either json or yaml performance (i.e. compare output.json with gpt4.json etc.)