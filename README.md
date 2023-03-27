# GPT in the Shell

  
### What is this?

An experiment inspired by reading the paper [ReAct: Synergizing Reasoning and Acting in Language Models](https://react-lm.github.io/) and [A simple Python implementation of the ReAct pattern for LLMs](https://til.simonwillison.net/llms/python-react-pattern) by [Simon Willison](https://github.com/simonw)
  

## How to use it?

### Prerequisites
An [OpenAI API key](https://platform.openai.com/account/api-keys)

### Usage
```bash
# Build the docker image
docker build  -t  gpt-shell  .

# Run the docker image
docker run  --env  OPENAI_API_KEY=sk-xxxxxxx  -it  gpt-shell
```

### Examples

<img src="https://raw.githubusercontent.com/jla/gpt-shell/assets/examples/is-google-down.png" alt="Is Google down?" width="600">

------------------------

<img src="https://raw.githubusercontent.com/jla/gpt-shell/assets/examples/any-open-ports.png" alt="Any open ports?" width="600">

-------------------------

<img src="https://raw.githubusercontent.com/jla/gpt-shell/assets/examples/who-am-i.png" alt="Who am I?" width="600">



### Disclaimer

- This code is just an **experiment**, it will burn your API credits quite fast and could destroy all your data if not run in an empty container/vm.
