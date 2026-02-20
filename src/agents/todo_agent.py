"""
Enhanced AI Agent for Todo Chatbot
Integrates with MCP tools to perform task management operations with improved intent recognition and confirmation handling
"""

import os
from typing import Dict, Any, List
from openai import OpenAI
from pydantic import BaseModel


class ToolCall(BaseModel):
    """Represents a tool call from the AI agent"""
    name: str
    arguments: Dict[str, Any]


class TodoAgent:
    """AI Agent that manages todo tasks using MCP tools with enhanced intent recognition and confirmation handling"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = """
        You are a helpful assistant that manages todo tasks. You can create, read, update, and delete tasks using the provided tools. 
        Always confirm destructive actions like deleting tasks before proceeding.
        If a user asks about tasks without being specific, offer to show their current tasks.
        
        Pay close attention to user intent. For example:
        - Variations of "create/add/new" should map to create_task
        - Variations of "show/list/view/see" should map to get_tasks
        - Variations of "update/change/edit/modify" should map to update_task
        - Variations of "delete/remove/cancel" should map to delete_task
        - Variations of "complete/finish/done" should map to complete_task
        
        When a destructive action requires confirmation, the tool will return a response with 'requires_confirmation' set to True.
        In such cases, you should ask the user for confirmation before proceeding with the action.
        """
        
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Define the available tools for the AI agent
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task with a title and optional description",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The title of the task"
                            },
                            "description": {
                                "type": "string",
                                "description": "The description of the task"
                            },
                            "owner_id": {
                                "type": "string",
                                "description": "The ID of the user who owns the task"
                            }
                        },
                        "required": ["title", "owner_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_tasks",
                    "description": "Get all tasks for a user, optionally filtered by status",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner_id": {
                                "type": "string",
                                "description": "The ID of the user whose tasks to retrieve"
                            },
                            "status": {
                                "type": "string",
                                "description": "Filter tasks by status (completed, pending, or all)",
                                "enum": ["completed", "pending", "all"]
                            }
                        },
                        "required": ["owner_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_task",
                    "description": "Update an existing task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "The ID of the task to update"
                            },
                            "title": {
                                "type": "string",
                                "description": "The new title of the task"
                            },
                            "description": {
                                "type": "string",
                                "description": "The new description of the task"
                            },
                            "is_completed": {
                                "type": "boolean",
                                "description": "Whether the task is completed"
                            },
                            "owner_id": {
                                "type": "string",
                                "description": "The ID of the user who owns the task"
                            }
                        },
                        "required": ["id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task",
                    "description": "Delete a task by ID. This will prompt for confirmation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "The ID of the task to delete"
                            }
                        },
                        "required": ["id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "complete_task",
                    "description": "Mark a task as completed",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "The ID of the task to mark as completed"
                            }
                        },
                        "required": ["id"]
                    }
                }
            }
        ]
    
    def chat(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a chat interaction with the AI agent
        """
        # Use the default tools if none are provided
        if tools is None:
            tools = self.get_available_tools()
            
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",  # Using a more cost-effective model
            messages=[
                {"role": "system", "content": self.system_prompt},
            ] + messages,
            tools=tools,
            tool_choice="auto"
        )
        
        return response.choices[0].model_dump()