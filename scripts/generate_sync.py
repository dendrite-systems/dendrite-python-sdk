import os
import ast
import shutil
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.WARNING)


class RenameTransformer(ast.NodeTransformer):
    def __init__(self, renames: Dict[str, str]):
        super().__init__()
        self.renames = renames

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.renames:
            node.id = self.renames[node.id]
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        if node.name in self.renames:
            node.name = self.renames[node.name]
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if node.name in self.renames:
            node.name = self.renames[node.name]
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr in self.renames:
            node.attr = self.renames[node.attr]
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        for alias in node.names:
            if alias.name in self.renames:
                alias.name = self.renames[alias.name]
            if alias.asname in self.renames:
                alias.asname = self.renames[alias.asname]
        return node

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            if alias.name in self.renames:
                alias.name = self.renames[alias.name]
            if alias.asname in self.renames:
                alias.asname = self.renames[alias.asname]
        return node

    def visit_Str(self, node: ast.Str) -> Any:
        for old, new in self.renames.items():
            node.s = node.s.replace(old, new)
        return node


class AsyncToSyncTransformer(ast.NodeTransformer):
    def __init__(self, renames: Dict[str, str]):
        super().__init__()
        self.unconverted_nodes = []
        self.renames = renames

    def visit_AsyncFunctionDef(self, node):
        # Remove 'async' from function definitions
        self.generic_visit(node)  # Mutate in place

        # Handle renaming __aenter__ to __enter__ and __aexit__ to __exit__
        if node.name == "__aenter__":
            new_name = "__enter__"
        elif node.name == "__aexit__":
            new_name = "__exit__"
        else:
            new_name = self.renames.get(node.name, node.name)

        new_node = ast.FunctionDef(
            name=new_name,
            args=node.args,
            body=node.body,
            decorator_list=node.decorator_list,
            returns=node.returns,
            type_comment=node.type_comment,
        )
        # Copy essential attributes
        new_node.lineno = node.lineno
        new_node.col_offset = node.col_offset
        new_node.end_lineno = getattr(node, "end_lineno", None)
        new_node.end_col_offset = getattr(node, "end_col_offset", None)
        return new_node

        new_node = ast.FunctionDef(
            name=self.renames.get(node.name, node.name),
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
                new_name = alias.name.replace(
                    "dendrite_sdk.async_api", "dendrite_sdk.sync_api", 1
                )
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
            node.module = node.module.replace(
                "dendrite_sdk.async_api", "dendrite_sdk.sync_api", 1
            )
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

    def visit_ClassDef(self, node):
        node.name = self.renames.get(node.name, node.name)
        return self.generic_visit(node)


def process_file(source_path, target_path, renames):
    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        logging.error(f"Syntax error in file {source_path}: {e}")
        return

    # Apply AsyncToSyncTransformer
    async_to_sync = AsyncToSyncTransformer(renames)
    tree = async_to_sync.visit(tree)

    # Apply RenameTransformer
    rename_transformer = RenameTransformer(renames)
    tree = rename_transformer.visit(tree)

    if async_to_sync.unconverted_nodes:
        logging.warning(f"Some nodes could not be converted in {source_path}")

    new_code = ast.unparse(tree)
    # Write the transformed code to target path
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(new_code)


def process_directory(source_dir, target_dir, renames):
    for dirpath, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            source_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, relative_path)

            if filename.endswith(".py"):
                process_file(source_path, target_path, renames)
            else:
                # Copy non-Python files directly
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(source_path, target_path)


if __name__ == "__main__":
    source_dir = "dendrite_sdk/async_api"
    target_dir = "dendrite_sdk/sync_api"
    renames = {
        "AsyncBrowserbaseDownload": "BrowserbaseDownload",
        "AsyncBrowserbaseBrowser": "BrowserbaseBrowser",
        "AsyncDendrite": "Dendrite",
        "BaseAsyncDendrite": "BaseDendrite",
        "AsyncElement": "Element",
        "AsyncPage": "Page",
        "AsyncDendriteRemoteBrowser": "DendriteRemoteBrowser",
        "AsyncElementsResponse": "ElementsResponse",
    }
    process_directory(source_dir, target_dir, renames)
