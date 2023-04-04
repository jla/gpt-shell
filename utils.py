import ast
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import Iterator, Tuple

def unindent(text:str) -> str:
    lines = text.splitlines()
    indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return '\n'.join(line[indent:] for line in lines)

def extract_code(lines: Iterator[str]) -> str:
    code = []
    for line in lines:
        if line == '```':
            return unindent('\n'.join(code))
        code.append(line)
    return None

def exec_code(code) -> Tuple[str, str, str|Exception]:
    with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
        try:
            result = exec_python(code)
        except Exception as e:
            result = e
        return out.getvalue(), err.getvalue(), result

def exec_python(code:str) -> str:
    block = ast.parse(code, mode='exec')
    last = ast.Expression(block.body.pop().value) if isinstance(block.body[-1], ast.Expr) else None
    _globals, _locals = {}, {}
    exec(compile(block, '<string>', mode='exec'), _globals, _locals)
    return eval(compile(last, '<string>', mode='eval'), _globals, _locals) if last else None

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def elapsed_time(timestamp: pd.Timestamp) -> str:
    now = datetime.now()
    elapsed = now - timestamp.to_pydatetime()
    
    if elapsed < timedelta(minutes=1):
        seconds = int(elapsed.total_seconds())
        return f"{seconds} seconds ago"
    elif elapsed < timedelta(hours=1):
        minutes = int(elapsed.total_seconds() // 60)
        return f"{minutes} minutes ago"
    elif elapsed < timedelta(days=1):
        hours = int(elapsed.total_seconds() // 3600)
        return f"{hours} hours ago"
    elif elapsed < timedelta(days=30):
        days = int(elapsed.total_seconds() // 86400)
        return f"{days} days ago"
    elif elapsed < timedelta(days=365):
        months = int(elapsed.total_seconds() // (30 * 86400))
        return f"{months} months ago"
    else:
        years = int(elapsed.total_seconds() // (365 * 86400))
        return f"{years} years ago"