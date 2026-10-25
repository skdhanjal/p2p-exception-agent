# ruff: noqa

from google.adk.apps import App
from app.agents import build_extract_agent, build_qa_agent, build_summary_agent
from app.workflow import build_workflow

from app import config

config.validate()

root_agent = build_workflow(
    extract=build_extract_agent(mode="single_turn"),
    summarize=build_summary_agent(mode="single_turn"),
    qa=build_qa_agent(mode="single_turn"),
)

app = App(
    root_agent=root_agent,
    name="app",
)
