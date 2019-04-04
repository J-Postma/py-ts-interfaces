from collections import deque
from typing import Dict, List, NamedTuple, Optional, Set
import astroid
import os
import warnings


class Interface:
    pass


TYPE_MAP: Dict[str, str] = {
    "bool": "boolean",
    "str": "string",
    "int": "number",
    "float": "number",
    "complex": "number",
    "Any": "any",
    "List": "Array<any>",
    "Tuple": "[any]",
    "Union": "any",
}

SUBSCRIPT_FORMAT_MAP: Dict[str, str] = {
    "List": "Array<%s>",
    "Optional": "%s | null",
    "Tuple": "[%s]",
    "Union": "%s",
}


InterfaceAttributes = Dict[str, str]
PreparedInterfaces = Dict[str, InterfaceAttributes]


class Parser:
    def __init__(
        self,
        interface_qualname: str,
        outpath: str = "interfaces.ts",
        overwrite: bool = True,
    ) -> None:
        self.interface_qualname = interface_qualname
        self.outpath = outpath
        self.overwrite = overwrite
        self.seen_interfaces: Set[str] = set()

    def parse(self, code: str) -> PreparedInterfaces:
        interfaces: PreparedInterfaces = {}

        queue = deque([astroid.parse(code)])
        while queue:
            current = queue.popleft()
            children = current.get_children()
            if not isinstance(current, astroid.ClassDef):
                queue.extend(children)
                continue

            if not current.is_subtype_of(self.interface_qualname):
                queue.extend(children)
                continue

            if not has_dataclass_decorator(current.decorators):
                warnings.warn(
                    UserWarning("Non-dataclasses are not supported, see documentation.")
                )
                continue

            if current.name in self.seen_interfaces:
                warnings.warn(
                    UserWarning(
                        f"Found duplicate interface with name {current.name}."
                        "All interfaces after the first will be ignored"
                    )
                )
                continue

            self.seen_interfaces.add(current.name)
            interfaces[current.name] = get_types_from_classdef(current)
        return interfaces

    def write(self, prepared: PreparedInterfaces) -> None:
        serialized: List[str] = []

        for interface, attributes in prepared.items():
            serialized.append(f"interface {interface} {{\n")
            for attribute_name, attribute_type in attributes.items():
                serialized.append(f"    {attribute_name}: {attribute_type};\n")
            serialized.append("}\n\n")

        if not serialized:
            warnings.warn(UserWarning("Did not have anything to write to the file!"))

        if self.overwrite or not os.path.isfile(self.outpath):
            with open(self.outpath, "w") as f:
                f.write(
                    "// Generated using py-ts-interfaces.  "
                    "See https://github.com/cs-cordero/py-ts-interfaces\n\n"
                )

        with open(self.outpath, "a") as f:
            for line in serialized:
                f.write(line)
        print(f"Created {self.outpath}!")


def get_types_from_classdef(node: astroid.ClassDef) -> Dict[str, str]:
    serialized_types: Dict[str, str] = {}
    for child in node.body:
        if not isinstance(child, astroid.AnnAssign):
            continue
        child_name, child_type = parse_annassign_node(child)
        serialized_types[child_name] = child_type
    return serialized_types


class ParsedAnnAssign(NamedTuple):
    attr_name: str
    attr_type: str


def parse_annassign_node(node: astroid.AnnAssign) -> ParsedAnnAssign:
    def helper(node: astroid.node_classes.NodeNG) -> str:
        type_value = "UNKNOWN"
        if isinstance(node, astroid.Name):
            type_value = TYPE_MAP[node.name]
            if node.name == "Union":
                warnings.warn(
                    UserWarning(
                        "Came across an annotation for Union without any indexed types!"
                        " Coercing the annotation to any."
                    )
                )
        elif isinstance(node, astroid.Subscript):
            subscript_value = node.value
            type_format = SUBSCRIPT_FORMAT_MAP[subscript_value.name]
            type_value = type_format % helper(node.slice.value)
        elif isinstance(node, astroid.Tuple):
            inner_types = get_inner_tuple_types(node)
            delimiter = get_inner_tuple_delimiter(node)
            if delimiter != "UNKNOWN":
                type_value = delimiter.join(inner_types)

        return type_value

    def get_inner_tuple_types(tuple_node: astroid.Tuple) -> List[str]:
        # avoid using Set to keep order
        inner_types: List[str] = []
        for child in tuple_node.get_children():
            child_type = helper(child)
            if child_type not in inner_types:
                inner_types.append(child_type)
        return inner_types

    def get_inner_tuple_delimiter(tuple_node: astroid.Tuple) -> str:
        parent_subscript_name = tuple_node.parent.parent.value.name
        delimiter = "UNKNOWN"
        if parent_subscript_name == "Tuple":
            delimiter = ", "
        elif parent_subscript_name == "Union":
            delimiter = " | "
        return delimiter

    return ParsedAnnAssign(node.target.name, helper(node.annotation))


def has_dataclass_decorator(decorators: Optional[astroid.Decorators]) -> bool:
    if not decorators:
        return False

    return any(
        (getattr(decorator.func, "name", None) == "dataclass")
        if isinstance(decorator, astroid.Call)
        else decorator.name == "dataclass"
        for decorator in decorators.nodes
    )
