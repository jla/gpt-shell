import os
import re
import sys
import subprocess
import requests
import shutil
import openai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

import memory
import utils

if not os.environ.get('OPENAI_API_KEY'):
    raise Exception('OPENAI_API_KEY environment variable not set')


PROMPT = """
You run in a loop of Thought, Action, and Observation.
Use Thought to describe your thoughts about the question you have been asked.
Memories will be provided to you if they are related to the question.
Find the Action according to your Thought.
Use Action to execute one of the actions available to you.
Observation will provide the result of running those actions.
If an action fail reformulate it and try again.
Repeat the loop until you successfully complete the task.
At the end, you will output an Answer to the user.

Your available actions are:

shell:
e.g. shell: ls $HOME
Run a shell command. Command line tools are available.
Use shell action to install any software you need to perform your task.
If a command is not available, you can install it using the shell action.
If the output of a shell action is not needed send it to /dev/null

eval:
e.g. eval: 1 + 1
Evaluate a python expression using eval().

exec:
e.g. exec: ```python
print('Hello World')
```
Execute a python statement using exec().
If you need OpenOpenAI API Key to run this code, you can use the OPENAI_API_KEY environment variable.

http_request:
e.g. http_request: GET https://example.com
Perform an HTTP request using the specified method (GET, POST, PUT, DELETE) and URL. You can provide data for POST and PUT requests.
For example, http_request: POST https://example.com {"key": "value"}

file_operations:
e.g. file_operations: create newfile.txt
Perform file operations such as create, copy, move, or delete. 
For example, file_operations: copy src.txt dest.txt

Here are some examples:

EXAMPLE 1:
==================================================
Question: What is the load average?
Thought: I should run a shell command to get the load average
Action: shell: uptime

You will be called again with this:

Observation: 12:59:51 up 55 days, 23:11,  1 user,  load average: 0.00, 0.00, 0.00

You then output:

Answer: load average: 0.00, 0.00, 0.00


""".strip()

MODEL = 'gpt-4' # 'gpt-3.5-turbo' 
MAX_ITERATIONS = 10
PS1 ='GPT-Shell> '

console = Console()
messages=[('system', PROMPT)]

def prompt(default=None):
    query(Prompt.ask(Text(PS1, style='bold dark_green'), default=default))

def query(query):
    if not query: return
    if query.strip()[0] != '|': # Reset conversation
        messages.clear()
        messages.append(('system', PROMPT))
    messages.append(('user', 'Question: ' + query))

    # Find related memories
    memories = memory.search(query)
    if memories:
        messages.append(('user', 'Memories: ' + query))
        console.print(Panel(memories, title="Memory: Search", title_align="left", border_style="grey50"))

    itercount = 0
    while itercount < MAX_ITERATIONS:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{'role': role, 'content': content} for role, content in messages]
        )['choices'][0]['message']['content']

        # Search for the final response
        if response.startswith('Answer:'):
            console.print(Panel(response[7:].strip(), title="GPT Response", title_align="left", border_style="green"))
            memories = memory.store(messages)
            console.print(Panel(memories, title="Memory: Store", title_align="left", border_style="grey50"))
            break
    
        console.print(Panel(response, title="GPT", title_align="left", border_style="green"))
        messages.append(('assistant', response))
        lines = iter([line for line in response.splitlines() if line.strip()])
        action = None
        params = None
        for line in lines:
            if line.startswith('Action:'):
                if not re.match(r'^Action:\s*(?:shell|eval|exec|http_request|file_operations)\s*:\s.*', line):
                    msg = "Observation: Invalid 'Action' format"
                    console.print(Panel(msg, title="Shell", title_align="left", border_style="red"))
                    messages.append(('user', msg))
                    action = False
                    break

                _, action, params = [p.strip() for p in line.split(':', 2)]
                if action == 'shell':
                    ret = subprocess.run(params, shell=True, text=True, capture_output=True)
                    output = ret.stdout + ret.stderr + f'Return code: {ret.returncode}'
                    
                elif action == 'eval':
                    try:
                        output = str(eval(params))
                    except Exception as e:
                        output = str(e)
                elif action == 'exec':
                    if params.strip() == '```python':
                        code = utils.extract_code(lines)
                        if code is None:
                            output = 'Invalid Action: Code block must start with ```python'
                        else:
                            stdout, stderr, result = utils.exec_code(code)
                            output = f"\nstdout:\n{stdout}\nstderr:\n{stderr}\n"
                            if isinstance(result, Exception):
                                output += f'exception:\n{result}'
                            else:
                                output += f'return:\n{result}'
                    else:
                        output = 'Invalid Action: Code block must start with ```python'
                elif action == 'http_request':
                    try:
                        method, url, *data = params.split(' ', 2)
                        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                            if method.upper() == 'GET':
                                response = requests.get(url)
                            elif method.upper() == 'POST':
                                response = requests.post(url, data=data[0] if data else None)
                            elif method.upper() == 'PUT':
                                response = requests.put(url, data=data[0] if data else None)
                            elif method.upper() == 'DELETE':
                                response = requests.delete(url)
                            else:
                                response = requests.request(method.upper(), url, data=data[0] if data else None)
                            output = f'Status code: {response.status_code}\nContent:\n{response.text}'
                        else:
                            output = f'Unsupported HTTP method: {method}'
                    except Exception as e:
                        output = str(e)
                elif action == 'file_operations':
                    try:
                        operation, *params = params.split(' ', 1)
                        if operation in ['create', 'copy', 'move', 'delete']:
                            # Perform file operation
                            if operation == 'create':
                                with open(params[0], 'w') as f:
                                    f.write('')
                                output = f"File created: {params[0]}"
                            elif operation == 'copy':
                                src, dest = params[0].split(' ')
                                shutil.copy(src, dest)
                                output = f"File copied from {src} to {dest}"
                            elif operation == 'move':
                                src, dest = params[0].split(' ')
                                shutil.move(src, dest)
                                output = f"File moved from {src} to {dest}"
                            elif operation == 'delete':
                                os.remove(params[0])
                                output = f"File deleted: {params[0]}"
                        else:
                            output = f'Unsupported file operation: {operation}'
                    except Exception as e:
                        output = str(e)  
                else:
                    output = f'Unknown action: {action}'
                console.print(Panel('Observation: ' + output.strip(), title="Shell", title_align="left", border_style="blue"))
                messages.append(('user', 'Observation: ' + output))
                itercount += 1
                    
        if action is None:
            # No action found
            break
        

if __name__ == '__main__':
    n = 0
    while(True):
        try:
            prompt(default='What time is it?' if n == 0 else None)
            n += 1
        except KeyboardInterrupt:
            console.print('\nBye!')
            sys.exit(0)
        except Exception as e:
            console.print(Panel(str(e), title="Error", title_align="left", border_style="red"))