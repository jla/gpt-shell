import ast
import io
from contextlib import redirect_stdout, redirect_stderr
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

