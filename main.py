import os
import sys
import subprocess
import openai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

if not os.environ.get('OPENAI_API_KEY'):
    raise Exception('OPENAI_API_KEY environment variable not set')


PROMPT = """
You run in a loop of Thought, Action, and Observation.
Use Thought to describe your thoughts about the question you have been asked.
Use Action to execute one of the actions available to you.
Try your best to find an action that will help you answer the question.
Observation will provide the result of running those actions.
Repeat the loop until you successfully complete the task.
At the end, you will output an Answer to the user.

Install any software you need.

Your available actions are:

shell:
e.g. shell: ls $HOME
Run a shell command. Command line tools are available.

eval:
e.g. eval: 1 + 1
Evaluate a python expression usign eval().

exec:
e.g. exec: print('Hello World')
Execute a python statement using exec().


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


EXAMPLE 2:
==================================================
Question:  How much disk space is available?
Thought: I should run a shell command to check the available disk space.
Action: shell: uptime

You will be called again with this:

Observation: Filesystem      Size  Used Avail Use% Mounted on 
overlay          59G   25G   31G  45% /  

You then output:

Answer: The available disk space is 31G

""".strip()

MODEL = 'gpt-4' # 'gpt-3.5-turbo' 
MAX_ITERATIONS = 10
PS1 ='GPT-Shell> '

console = Console()

def prompt(default=None):
    query(Prompt.ask(Text(PS1, style='bold dark_green'), default=default))

def query(query):
    if not query: return
    messages=[('system', PROMPT),('user', 'Question: ' + query)]

    itercount = 0
    while itercount < MAX_ITERATIONS:
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{'role': role, 'content': content} for role, content in messages]
        )['choices'][0]['message']['content']

        # Search for the final response
        if response.startswith('Answer:'):
            console.print(Panel(response[7:].strip(), title="GPT Response", title_align="left", border_style="green"))
            break
    
        console.print(Panel(response, title="GPT", title_align="left", border_style="green"))
        messages.append(('assistant', response))
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        action = None
        params = None
        for line in lines:
            if line.startswith('Action:'):
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
                    try:
                        exec(params)
                        output = 'Success'
                    except Exception as e:
                        output = str(e)
                else:
                    output = f'Unknown action: {action}'
                console.print(Panel('Observation: ' + output.strip(), title="Shell", title_align="left", border_style="blue"))
                messages.append(('user', output))
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