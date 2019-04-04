# Stubs for astroid._ast (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from collections import namedtuple
from typing import Optional

FunctionType = namedtuple('FunctionType', ['argtypes', 'returns'])

def parse_function_type_comment(type_comment: str) -> Optional[FunctionType]: ...
