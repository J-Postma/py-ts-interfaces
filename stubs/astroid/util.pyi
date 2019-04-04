# Stubs for astroid.util (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any

def lazy_descriptor(obj: Any) -> Any: ...
def lazy_import(module_name: Any) -> Any: ...

class Uninferable:
    def __getattribute__(self, name: Any) -> Any: ...
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    def __bool__(self) -> bool: ...
    __nonzero__: Any = ...
    def accept(self, visitor: Any) -> Any: ...

class BadOperationMessage: ...

class BadUnaryOperationMessage(BadOperationMessage):
    operand: Any = ...
    op: Any = ...
    error: Any = ...
    def __init__(self, operand: Any, op: Any, error: Any) -> None: ...

class BadBinaryOperationMessage(BadOperationMessage):
    left_type: Any = ...
    right_type: Any = ...
    op: Any = ...
    def __init__(self, left_type: Any, op: Any, right_type: Any) -> None: ...

def proxy_alias(alias_name: Any, node_type: Any) -> Any: ...
def limit_inference(iterator: Any, size: Any) -> None: ...
