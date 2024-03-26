# Data Extraction
This folder provides methods for extracting structured data from text.

Todo Sagar:
- [x] Let's get rid of human and non-human. Nobody will want that structure. Let's revert to a simple json format with just name and organizations.
- [x] There is no 'main.py' - There is no main.py file. Do you mean tgi-data-extraction?
- [x] The runpod template has a max of 7500 input tokens, so we need to limit to that here too.
- [x] The command should also take in an optional argument of whether to set batching=True. The default is False. This also needs to be explained in the readme.
- [x] Add an input file name parameter to the command line argument. It should be optional and default to berkshire23.txt
- [x] Search for the instances of 'RONAN-COMMENT:' in this ReadMe for specific remarks.
- [x] Please clean up any un-used or outdated files in data_extraction.
- [x] In tgi data extraction it looks like you are importing a lot of modules that are not used.
- [x] In tgi-data-extraction I can see that the code is not generic. You have hard coded in the json structure. Rather, we need to use the structure defined in either prompts.py or in a file specifically for the json.
- [x] I think you are confusing tokens for characters in context length. This probably explains why you thought 8k context was working. Right now, you're only processing 8k characters, not tokens. there are about 4 characters per token. So actually, let's just stick to processing a max of 4k tokens, which means setting the context to 16000 characters.
- [x] For some reason, the script 'python tgi-data-extraction.py --context_length 16000 --output_format json --output_file_name output' is breaking when I use 16000 instead of 8000. That seems odd. Interestingly, YAML works without validation errors.
- [x] Take a look at the output.yaml file. You'll see that there are incorrect names and orgs, e.g. FirstName1 and org1.
- [] Better to rename all context_length variables as chunk_length, because it refers to the chunk length, not really the full context length.
- [] We need to explain in the readme, that when batching is False, then the model will make sequential calls to the LLM with text lengths of chunk_length. If batching is true, then batches of 32 calls will be submitted at once.
- [] Carefully read all code, there were a lot of typos and grammar mistakes in the prompt.
- [] You need to run each piece of code through chat gpt for errors. I found a lot of errors, for example an infinite loop in json_validation_aggregation.py

Other notes:
- [x] JSON and YAML extraction is now working for 16k character chunk sizes. 
- [] I have made a short version of the berkshire text for testing. Please keep that shorter file and let's use it as default. We don't want customers running a massive request on the long berkshire file as the default.
- [x] I did some testing on Mixtral and it's quite poor. A lot worse than OpenChat. Possibly a model like CodeLlama would be decent at these tasks, but I haven't tried running that yet.
- [x] I made a compare.py file that compares the output.json to a gpt4 json I made using berkshire23_12.5k.txt . OpenChat is just as good on names, but misses quite a few orgs.
- [x] All of my testing today was done with the original openchat (not the 0106 model). However, at the end, I tried out the 0601 model and it seems to have hallucinated two names. So I suggest we stick with the base model.
- [x] I also tested out the eetq version (8bit instead of 4bit awq) and it was similar to AWQ, but it hallucinated on one name (so maybe OpenChat will always hallucinate a bit).
- [x] I tested out bf16 (16 bit) OpenChat. Oddly, the 16bit was more likely to repeat values, so I had to address that by tweaking the prompt. Performance does seem best in 16 bit, so I recommend using that one for best quality. Template [here](https://runpod.io/gsc?template=xiwn7cb3ro&ref=jmfkcdio). Check out the csv files in the outputs folder, OpenChat is only missing Microsoft and also Geico. I don't know why, there may be something specific about those names.
- [x] Be careful that runpod input limit isn’t too short or there will be no text returned. It will just say “No text in response”. This was an issue when I tested Mixtral because the token input limit is short.

Parallel requests:
- [x] Build in threads for multiple concurrent requests: I have realised that - because you are sending requests in series - if you just run those requests on separate threads (as is done in the concurrent script in speed_tests), then this is essentially equivalent to doing parallel requests. So we can probably save time on trying to develop a parallel inference code. Technically, doing batches is probably a bit more efficient than just pinging the server quickly, but not much better I'm guessing. BTW, it's important to use multiple threads - I think - otherwise the things can get overloaded.

OR

- [] Build batching. If you decide to build batching (which is submitting and handling a batch of queries) I strongly suggest having one script for a single call tgi-data-extraction.py and another tgi-data-extraction-batched.py for batched calls. It makes testing a lot easier and you can have slightly different commands (adding batch_size to the batched script).

Todo Ronan:
- [x] Verify Sagar tasks above. Done on series requests.
- [x] Check performance of simple extraction. Compare with GPT4.
- [x] Add de-duplication to the yaml aggregation
- [x] Add de-duplication to the json aggregation
- [x] diagnose json performance. Fixed by using json.dumps with indentation - which forces double instead of single quotes, as required by json syntax (previously, our json examples were being parsed as single quote).
- [x] check out mistral 7b performance. Works better with yaml and struggles above 8k characters.
- [x] check mixtral performance again. It's bad, mostly fails.
- [x] Check Notux, a mixtral fine-tuning. Better, generates sensible yaml, but misses entries more than OpenChat 3.5 .
- [x] Cleaned up prompts.py
- [x] Fix a new bug I introduced mixing up json and yaml in prompts.
- [x] Test out DeepSeek Coder instruct model. yaml works, although organizations are incomplete. json doesn't seem to work. Repetition is also a problem. The base model blabs on.
- [x] Test out CodeLlama (if DeepSeek doesn't work well). This works reasonably well but misses values versus GPT4.
- [x] Test OpenChat 3.5 again. It's not perfect, but very close on names. For GPT4 as well, json maybe extracts more.
- [x] Mixtral remains terrible. Often fails on yaml and json.
- [x] OpenChat 3.5 0106 seems to hallucinate a little more.
- [x] Notux works, but the answers are inconsistent and not robust to small prompt tweaks.
- [x] Verify Sagar tasks above on batching/threading. Fixed a bug with setting up messages.
- [x] Check performance of batched extraction. Compare with GPT4. AT VERY LONG CONTEXT GPT4 FAILS TO GRAB ALL OF THE CONTEXT. As you go to longer context, you just get more errors.
