import json
from datetime import datetime
import pandas as pd
import numpy as np
import openai

import utils

STORE_PROMPT = """
Review the provided conversation and extract only the relevant information that could be useful for the model in future conversations.
Focus on key points, important details, and any unique insights that can help the model understand and respond more effectively in similar situations.
Please discard any irrelevant, repetitive, or unnecessary information.
Summarize the extracted information in a concise and clear manner, making it easy to integrate into the model's knowledge base.
At the end include a list of tags that can be used to categorize the conversation.
""".strip()

SEARCH_PROMPT = """
You will be provided with a user query and a list of memories that are related to the query.
Please sumarize the most relevant information from each memory and provide a response that can be used to answer the user query.
""".strip()

MODEL = 'gpt-4' # 'gpt-3.5-turbo'
EMBEDDING = 'text-embedding-ada-002'

try:
  df = pd.read_pickle('data/memory.pkl.gz')
except:
  df = pd.DataFrame(columns=['timestamp', 'text', 'embedding'])

def store(messages):
    global df
    # Remove admin role messages
    messages = [msg for msg in messages if msg[0] != 'system']
    response = openai.ChatCompletion.create(
            model=MODEL,
            messages=[
              {'role': 'system', 'content': STORE_PROMPT},
              {'role': 'user', 'content': json.dumps(messages)}
            ]
          )['choices'][0]['message']['content']
    embedding = openai.Embedding.create(
      input=response,
      model=EMBEDDING
    )['data'][0]['embedding']
    df = pd.concat([df, pd.DataFrame.from_records([{'timestamp': datetime.now(),'text': response, 'embedding': embedding}])])
    df.to_pickle('data/memory.pkl.gz')
    return response


def search(query, n=5):
    global df
    if df is None or df.empty: return
    embedding = openai.Embedding.create(
      input=query,
      model=EMBEDDING
    )['data'][0]['embedding']
    df['similarity'] = df.embedding.apply(lambda x: utils.cosine_similarity(x, embedding))
    hdf = df.sort_values("similarity", ascending=False).head(n)
    memories = (f'{elapsed}\n{text}' for elapsed, text in zip(hdf.timestamp.apply(utils.elapsed_time).values, hdf.text.values))
    content =  f"Query:\n{query}\n\n\nMemories:\n" + "\n\n--------\n\n".join(memories)
    return openai.ChatCompletion.create(
            model=MODEL,
            messages=[
              {'role': 'system', 'content': SEARCH_PROMPT},
              {'role': 'user', 'content': content}
            ]
          )['choices'][0]['message']['content']
