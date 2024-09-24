import os
import ast
import shutil
import logging

logging.basicConfig(level=logging.WARNING)

import ast
import logging
from typing import cast


class AsyncToSyncTransformer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.unconverted_nodes = []

    def visit_AsyncFunctionDef(self, node):
        # Remove 'async' from function definitions
        self.generic_visit(node)  # Mutate in place
        new_node = ast.FunctionDef(
            name=node.name,
            args=node.args,
            body=node.body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_comment=node.type_comment,
        )
        # Copy essential attributes
        new_node.lineno = node.lineno
        new_node.col_offset = node.col_offset
        new_node.end_lineno = node.end_lineno
        new_node.end_col_offset = node.end_col_offset
        return new_node

    def visit_Await(self, node):
        # Remove 'await' from 'await' expressions
        self.generic_visit(node)
        return node.value  # Remove the Await node, keep the value

    def visit_AsyncWith(self, node):
        # Convert 'async with' to 'with'
        self.generic_visit(node)
        new_node = ast.With(
            items=node.items, body=node.body, type_comment=node.type_comment
        )
        # Copy essential attributes
        new_node.lineno = node.lineno
        new_node.col_offset = node.col_offset
        new_node.end_lineno = node.end_lineno
        new_node.end_col_offset = node.end_col_offset
        return new_node

    def visit_AsyncFor(self, node):
        # Convert 'async for' to 'for'
        self.generic_visit(node)
        new_node = ast.For(
            target=node.target,
            iter=node.iter,
            body=node.body,
            orelse=node.orelse,
            type_comment=node.type_comment,
        )
        # Copy essential attributes
        new_node.lineno = node.lineno
        new_node.col_offset = node.col_offset
        new_node.end_lineno = node.end_lineno
        new_node.end_col_offset = node.end_col_offset
        return new_node

    # Rest of your methods remain the same
    # ...

    def visit_Import(self, node):
        # Replace imports
        self.generic_visit(node)
        new_names = []
        for alias in node.names:
            if alias.name == "playwright.async_api":
                alias = ast.alias(name="playwright.sync_api", asname=alias.asname)
            elif alias.name == "asyncio":
                alias = ast.alias(name="time", asname=alias.asname)
            elif alias.name.startswith("dendrite_sdk"):
                new_name = alias.name.replace("dendrite_sdk", "dendrite_sync_sdk", 1)
                alias = ast.alias(name=new_name, asname=alias.asname)
            new_names.append(alias)
        node.names = new_names
        return node

    def visit_ImportFrom(self, node):
        # Replace imports
        self.generic_visit(node)
        if node.module == "playwright.async_api":
            node.module = "playwright.sync_api"
            new_names = []
            for alias in node.names:
                if alias.name == "async_playwright":
                    alias = ast.alias(name="sync_playwright", asname=alias.asname)
                new_names.append(alias)
            node.names = new_names
        elif node.module == "asyncio":
            node.module = "time"
        elif node.module and node.module.startswith("dendrite_sdk"):
            node.module = node.module.replace("dendrite_sdk", "dendrite_sdk_sync", 1)
        return node

    def visit_Call(self, node):
        # Replace 'asyncio.sleep' with 'time.sleep', etc.
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == "asyncio" and node.func.attr == "sleep":
                    node.func.value.id = "time"  # Replace 'asyncio' with 'time'
                elif node.func.value.id == "httpx" and node.func.attr == "AsyncClient":
                    node.func.attr = "Client"  # Replace 'AsyncClient' with 'Client'
        return node

    def visit_Attribute(self, node):
        # Replace 'httpx.AsyncClient' with 'httpx.Client'
        self.generic_visit(node)
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "httpx"
            and node.attr == "AsyncClient"
        ):
            node.attr = "Client"
        return node

    def visit_Name(self, node):
        # Replace 'AsyncClient' with 'Client' if used directly
        if node.id == "async_playwright":
            node.id = "sync_playwright"
        elif node.id == "AsyncClient":
            node.id = "Client"
        return node

    def visit_AsyncGenerator(self, node):
        # Cannot convert async generators to sync generators
        logging.warning(f"Cannot convert async generator at line {node.lineno}")
        self.unconverted_nodes.append(node)
        return node

    def visit_YieldFrom(self, node):
        # Cannot convert 'yield from' in async functions
        logging.warning(
            f"Cannot convert 'yield from' in async function at line {node.lineno}"
        )
        self.unconverted_nodes.append(node)
        return node


def process_file(source_path, target_path):
    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logging.error(f"Syntax error in file {source_path}: {e}")
        return

    transformer = AsyncToSyncTransformer()
    transformer.visit(tree)

    if transformer.unconverted_nodes:
        logging.warning(f"Some nodes could not be converted in {source_path}")

    # ast.unparse is available in Python 3.9+

    new_code = ast.unparse(tree)
    # Write the transformed code to target path
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def process_directory(source_dir, target_dir):
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            source_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, relative_path)

            if filename.endswith(".py"):
                process_file(source_path, target_path)
            else:
                # Copy non-Python files directly
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(source_path, target_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python async_to_sync.py <source_dir> <target_dir>")
        sys.exit(1)
    source_dir = sys.argv[1]
    target_dir = sys.argv[2]
    process_directory(source_dir, target_dir)
