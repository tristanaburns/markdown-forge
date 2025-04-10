"""
API documentation utility for Markdown Forge.
This module provides utilities for enhancing FastAPI's built-in API documentation.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

def custom_openapi(app: FastAPI, title: str, version: str, description: str) -> None:
    """
    Generate a custom OpenAPI schema for the FastAPI application.
    
    Args:
        app (FastAPI): FastAPI application
        title (str): API title
        version (str): API version
        description (str): API description
    """
    if app.openapi_schema:
        return
    
    openapi_schema = get_openapi(
        title=title,
        version=version,
        description=description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]
    
    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "files",
            "description": "File management operations",
        },
        {
            "name": "conversion",
            "description": "File conversion operations",
        },
        {
            "name": "auth",
            "description": "Authentication operations",
        },
        {
            "name": "projects",
            "description": "Project management operations",
        },
        {
            "name": "system",
            "description": "System operations",
        },
    ]
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "/",
            "description": "Local development server",
        },
        {
            "url": "https://api.markdownforge.example.com",
            "description": "Production server",
        },
    ]
    
    app.openapi_schema = openapi_schema

def generate_api_docs(app: FastAPI, output_dir: str) -> None:
    """
    Generate API documentation files.
    
    Args:
        app (FastAPI): FastAPI application
        output_dir (str): Output directory for documentation files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate OpenAPI schema
    openapi_schema = app.openapi_schema
    
    # Save OpenAPI schema as JSON
    with open(os.path.join(output_dir, "openapi.json"), "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    # Generate Markdown documentation
    generate_markdown_docs(openapi_schema, output_dir)

def generate_markdown_docs(openapi_schema: Dict[str, Any], output_dir: str) -> None:
    """
    Generate Markdown documentation from OpenAPI schema.
    
    Args:
        openapi_schema (Dict[str, Any]): OpenAPI schema
        output_dir (str): Output directory for documentation files
    """
    # Create API documentation directory
    api_docs_dir = os.path.join(output_dir, "api")
    os.makedirs(api_docs_dir, exist_ok=True)
    
    # Generate main README.md
    with open(os.path.join(api_docs_dir, "README.md"), "w") as f:
        f.write(f"# {openapi_schema['info']['title']} API Documentation\n\n")
        f.write(f"{openapi_schema['info']['description']}\n\n")
        f.write(f"Version: {openapi_schema['info']['version']}\n\n")
        
        # Add authentication information
        f.write("## Authentication\n\n")
        f.write("All API endpoints require authentication using JWT tokens.\n\n")
        f.write("Include the token in the Authorization header:\n\n")
        f.write("```\nAuthorization: Bearer <token>\n```\n\n")
        
        # Add endpoints overview
        f.write("## Endpoints\n\n")
        
        # Group endpoints by tag
        endpoints_by_tag = {}
        for path, path_item in openapi_schema["paths"].items():
            for method, operation in path_item.items():
                if method == "parameters":
                    continue
                
                tags = operation.get("tags", ["default"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                    })
        
        # Write endpoints by tag
        for tag, endpoints in endpoints_by_tag.items():
            f.write(f"### {tag.capitalize()}\n\n")
            
            for endpoint in endpoints:
                f.write(f"#### {endpoint['method']} {endpoint['path']}\n\n")
                f.write(f"{endpoint['summary']}\n\n")
                
                if endpoint['description']:
                    f.write(f"{endpoint['description']}\n\n")
                
                f.write("```\n")
                f.write(f"{endpoint['method']} {endpoint['path']}\n")
                f.write("```\n\n")
    
    # Generate documentation for each tag
    for tag in openapi_schema.get("tags", []):
        tag_name = tag["name"]
        tag_description = tag.get("description", "")
        
        with open(os.path.join(api_docs_dir, f"{tag_name}.md"), "w") as f:
            f.write(f"# {tag_name.capitalize()} API\n\n")
            f.write(f"{tag_description}\n\n")
            
            # Find all endpoints for this tag
            tag_endpoints = []
            for path, path_item in openapi_schema["paths"].items():
                for method, operation in path_item.items():
                    if method == "parameters":
                        continue
                    
                    if tag_name in operation.get("tags", []):
                        tag_endpoints.append({
                            "path": path,
                            "method": method.upper(),
                            "operation": operation,
                        })
            
            # Write detailed documentation for each endpoint
            for endpoint in tag_endpoints:
                operation = endpoint["operation"]
                
                f.write(f"## {operation.get('summary', '')}\n\n")
                f.write(f"{operation.get('description', '')}\n\n")
                
                f.write("### Endpoint\n\n")
                f.write("```\n")
                f.write(f"{endpoint['method']} {endpoint['path']}\n")
                f.write("```\n\n")
                
                # Request parameters
                if "parameters" in operation:
                    f.write("### Parameters\n\n")
                    f.write("| Name | In | Type | Required | Description |\n")
                    f.write("|------|----|------|----------|-------------|\n")
                    
                    for param in operation["parameters"]:
                        required = "Yes" if param.get("required", False) else "No"
                        f.write(f"| {param['name']} | {param['in']} | {param['schema']['type']} | {required} | {param.get('description', '')} |\n")
                    
                    f.write("\n")
                
                # Request body
                if "requestBody" in operation:
                    f.write("### Request Body\n\n")
                    
                    content = operation["requestBody"]["content"]
                    for content_type, schema in content.items():
                        f.write(f"**Content Type:** `{content_type}`\n\n")
                        
                        if "schema" in schema:
                            schema_ref = schema["schema"].get("$ref", "")
                            if schema_ref:
                                schema_name = schema_ref.split("/")[-1]
                                f.write(f"Schema: `{schema_name}`\n\n")
                            else:
                                f.write("```json\n")
                                f.write(json.dumps(schema["schema"], indent=2))
                                f.write("\n```\n\n")
                
                # Responses
                f.write("### Responses\n\n")
                f.write("| Status Code | Description |\n")
                f.write("|-------------|-------------|\n")
                
                for status_code, response in operation["responses"].items():
                    description = response.get("description", "")
                    f.write(f"| {status_code} | {description} |\n")
                
                f.write("\n")
                
                # Example responses
                for status_code, response in operation["responses"].items():
                    if "content" in response:
                        f.write(f"#### {status_code} Response\n\n")
                        
                        content = response["content"]
                        for content_type, schema in content.items():
                            f.write(f"**Content Type:** `{content_type}`\n\n")
                            
                            if "example" in schema:
                                f.write("```json\n")
                                f.write(json.dumps(schema["example"], indent=2))
                                f.write("\n```\n\n")
                            elif "schema" in schema:
                                schema_ref = schema["schema"].get("$ref", "")
                                if schema_ref:
                                    schema_name = schema_ref.split("/")[-1]
                                    f.write(f"Schema: `{schema_name}`\n\n")
                                else:
                                    f.write("```json\n")
                                    f.write(json.dumps(schema["schema"], indent=2))
                                    f.write("\n```\n\n")
                
                f.write("---\n\n") 