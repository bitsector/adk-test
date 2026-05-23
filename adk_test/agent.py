"""Minimal Google ADK agent for local experimentation."""

from __future__ import annotations

import os

from google.adk import Agent


def build_experiment_plan(goal: str) -> dict[str, list[str] | str]:
    """Return a concrete starter plan for an ADK experiment."""
    normalized_goal = goal.strip() or "prototype an agentic workflow"
    return {
        "goal": normalized_goal,
        "next_steps": [
            "Define a single user journey to prototype first.",
            "List the tools or APIs the agent should call during that journey.",
            "Add session state you want the agent to remember between turns.",
            "Run the agent in ADK Web, inspect tool calls, and tighten instructions.",
        ],
        "first_increment": f"Build a small conversation flow around: {normalized_goal}.",
    }


root_agent = Agent(
    name="adk_experiment_agent",
    model=os.getenv("ADK_MODEL", "gemini-2.5-flash"),
    instruction=(
        "You are a product-minded prototyping assistant helping the user "
        "experiment with Google's Agent Development Toolkit. Keep answers "
        "practical and concise. Use the build_experiment_plan tool whenever "
        "the user needs a concrete implementation plan."
    ),
    tools=[build_experiment_plan],
)
