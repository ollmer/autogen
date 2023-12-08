# Disable ruff linter for bare except
# ruff: noqa: E722

import os
import json
import autogen
from datetime import datetime
import testbed_utils
import traceback
from autogen.agentchat.contrib.web_surfer import WebSurferAgent
from autogen.agentchat.contrib.group_chat_moderator import GroupChatModerator

testbed_utils.init()
##############################


GAIA_SYSTEM_MESSAGE = (
    "You are a helpful AI assistant, and today's date is "
    + datetime.now().date().isoformat()
    + """.
I will ask you a question. Answer this question using your coding and language skills.
When answering questions, it is often best to start by stating all relevant facts that you already know, then work to from there to produce a final answer.
In the following cases, suggest python code (presented in a coding block beginning ```python) or shell script (presented in a coding block beginning ```sh) for the user to execute:
    1. When you need to collect info, use the code to output the info you need, for example, browse or search the web, download/read a file, print the content of a webpage or a file, check the operating system. After sufficient info is printed and the task is ready to be solved based on your language skill, you can solve the task by yourself.
    2. When you need to perform some task with code, use the code to perform the task and output the result. Finish the task smartly.
Answer the question step if you need to. If a plan is not provided, explain your plan first. Be clear which step uses code, and which step uses your language skill.
The user cannot provide any other feedback or perform any other action beyond executing the code appearing in the code block. The user can't modify your code, so do not suggest incomplete code which requires users to modify. Don't use a code block if it's not intended to be executed by the user. Don't include multiple code blocks in one response. Do not ask users to copy and paste code or results. Instead, use the 'print' function for the output when relevant. Check the execution result reported by the user.
If the result indicates there is an error, fix the error and output the code again. Suggest the full code instead of partial code or code changes. If the error can't be fixed or if the task is not solved even after the code is executed successfully, analyze the problem, revisit your assumption, collect additional info you need, and think of a different approach to try.
When you find an answer, report your thoughts, and finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER].
YOUR FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
If you are asked for a number, don't use comma to write your number neither use units such as $ or percent sign unless specified otherwise.
If you are asked for a string, don't use articles, neither abbreviations (e.g. for cities), and write the digits in plain text unless specified otherwise.
If you are asked for a comma separated list, apply the above rules depending of whether the element to be put in the list is a number or a string.
    """.strip()
)


config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={"model": ["__MODEL__"]},
)
llm_config = testbed_utils.default_llm_config(config_list, timeout=180)
llm_config["temperature"] = 0.1

summarizer_config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    filter_dict={"model": ["gpt-3.5-turbo-16k"]},
)
summarizer_llm_config = testbed_utils.default_llm_config(summarizer_config_list, timeout=180)
summarizer_llm_config["temperature"] = 0.1

assistant = autogen.AssistantAgent(
    "assistant",
    system_message=GAIA_SYSTEM_MESSAGE,
    description=autogen.AssistantAgent.DEFAULT_DESCRIPTION,
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    llm_config=llm_config,
)
user_proxy = autogen.UserProxyAgent(
    "code_interpreter",
    human_input_mode="NEVER",
    description="A code interpreter assistant who cannot write code or perform other tasks, but can EXECUTE Python or sh scripts (when provided in codeblocks) and report back the results.",
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
        "last_n_messages": "auto",
    },
    max_consecutive_auto_reply=10,
    default_auto_reply="",
)

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"

web_surfer = WebSurferAgent(
    "web_surfer",
    system_message=WebSurferAgent.DEFAULT_SURFER_PROMPT,
    llm_config=llm_config,
    summarizer_llm_config=summarizer_llm_config,
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    browser_config={
        "bing_api_key": os.environ["BING_API_KEY"],
        "viewport_size": 1024 * 5,
        "downloads_folder": "coding",
        "request_kwargs": {
            "headers": {"User-Agent": user_agent},
        },
    },
)

filename = "__FILE_NAME__".strip()
question = """
__PROMPT__
""".strip()

if len(filename) > 0:
    question = f"Consider the file '{filename}', which can be read from the current working directory. {question}"

groupchat = GroupChatModerator(
    agents=[assistant, user_proxy, web_surfer],
    messages=[],
    speaker_selection_method="__SELECTION_METHOD__",
    allow_repeat_speaker=[web_surfer],
    max_round=12,
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    is_termination_msg=lambda x: x.get("content", "").rstrip().find("FINAL ANSWER") >= 0,
    llm_config=llm_config,
)

try:
    manager.initiate_chat(manager, message=question)
except:
    traceback.print_exc()

##############################
testbed_utils.finalize(agents=[assistant, user_proxy, web_surfer, manager])
