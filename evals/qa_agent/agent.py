"""Evaluation target: the Q&A agent on its own, in chat mode."""

from app.agents import build_qa_agent

root_agent = build_qa_agent()
