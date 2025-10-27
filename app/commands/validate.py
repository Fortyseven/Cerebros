from __future__ import annotations


def rewrite_refs(obj, schema_dir_uri):
    """Recursively rewrite $ref values to use file URIs."""
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                # Only rewrite relative refs
                if not v.startswith("http") and not v.startswith("file://"):
                    new_obj[k] = schema_dir_uri + v
                else:
                    new_obj[k] = v
            else:
                new_obj[k] = rewrite_refs(v, schema_dir_uri)
        return new_obj
    elif isinstance(obj, list):
        return [rewrite_refs(i, schema_dir_uri) for i in obj]
    else:
        return obj


import os
import glob
import yaml
import json
from jsonschema import ValidationError
from jsonschema import Draft7Validator, RefResolver
import argparse
from dataclasses import dataclass
from app.cli import CommandContext

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schema")


def find_yaml_files(workspace_dir):
    pattern = os.path.join(workspace_dir, "**", "*.yml")
    return glob.glob(pattern, recursive=True)


def get_schema_name_from_filename(filename):
    # Example: crispus-attucks.Person.yml -> Person
    base = os.path.basename(filename)
    parts = base.split(".")
    if len(parts) >= 3:
        return parts[-2]
    return None


def load_schema(schema_name):
    schema_path = os.path.join(SCHEMA_DIR, f"{schema_name}.json")
    if not os.path.exists(schema_path):
        return None
    with open(schema_path, "r") as f:
        return json.load(f)


def build_schema_store():
    store = {}
    # Load top-level schemas
    for fname in os.listdir(SCHEMA_DIR):
        if fname.endswith(".json"):
            path = os.path.join(SCHEMA_DIR, fname)
            with open(path, "r") as f:
                schema = json.load(f)
                store[fname] = schema
                if "$id" in schema:
                    store[schema["$id"]] = schema
    # Load subtypes
    subtypes_dir = os.path.join(SCHEMA_DIR, "subtypes")
    if os.path.isdir(subtypes_dir):
        for fname in os.listdir(subtypes_dir):
            if fname.endswith(".json"):
                path = os.path.join(subtypes_dir, fname)
                with open(path, "r") as f:
                    schema = json.load(f)
                    store[f"subtypes/{fname}"] = schema
                    if "$id" in schema:
                        store[schema["$id"]] = schema
    return store


def validate_yaml_file(yaml_path, schema):
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    store = build_schema_store()
    schema_dir_uri = f"file://{os.path.abspath(SCHEMA_DIR)}/"
    # Add file URI keys for local resolution
    for k, v in list(store.items()):
        if k.endswith(".json"):
            store[schema_dir_uri + k] = rewrite_refs(v, schema_dir_uri)
    schema = rewrite_refs(schema, schema_dir_uri)
    resolver = RefResolver(base_uri=schema_dir_uri, referrer=schema, store=store)
    validator = Draft7Validator(schema, resolver=resolver)
    try:
        validator.validate(data)
        return True, None
    except ValidationError as e:
        return False, str(e)


def main(workspace_dir, console):
    yaml_files = find_yaml_files(workspace_dir)
    results = []
    for yaml_file in yaml_files:
        schema_name = get_schema_name_from_filename(yaml_file)
        if not schema_name:
            results.append((yaml_file, False, "Could not determine schema name"))
            continue

        schema = load_schema(schema_name)

        if not schema:
            results.append((yaml_file, False, f"Schema {schema_name} not found"))
            continue

        valid, error = validate_yaml_file(yaml_file, schema)
        results.append((yaml_file, valid, error))

    for yaml_file, valid, error in results:
        if valid:
            console.print(f"[green][OK][/green] {yaml_file}")
        else:
            console.print(f"\n[red][FAIL][/red] {yaml_file}:\n       {error}\n")


def build_parser(prog: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=prog, description="Validate YAML files against schemas"
    )
    return p


def run(ctx: CommandContext, ns: argparse.Namespace) -> int:
    main(ctx.workspace, ctx.console)
    return 0


@dataclass
class _Command:
    name: str = "validate"
    help: str = "Validate YAML files against schemas"
    build_parser = staticmethod(build_parser)
    run = staticmethod(run)


COMMAND = _Command()
