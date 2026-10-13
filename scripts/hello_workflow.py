"""A tiny workflow to learn the primitives. No models, no network."""

import asyncio

from google.adk import Event
from google.adk.agents.context import Context
from google.adk.events import RequestInput
from google.adk.runners import InMemoryRunner
from google.adk.workflow import DEFAULT_ROUTE, JoinNode, Workflow
from google.genai import types


def classify(node_input: types.Content):
    text = node_input.parts[0].text.lower()
    route = "SMALL" if "small" in text else "BIG"
    return Event(output=text, route=route, state={"size": route})


def split(node_input: str):
    return node_input


async def count_words(node_input: str):
    await asyncio.sleep(0)  # yield to the event loop
    return len(node_input.split())


async def count_chars(node_input: str):
    await asyncio.sleep(0)
    return len(node_input)


def combine(node_input: dict, ctx: Context):
    return f"size={ctx.state.get('size')} stats={node_input}"


def ask(node_input: str):
    yield RequestInput(message=f"Publish '{node_input}'?", response_schema=str)


def finish(node_input: str):
    return f"human said: {node_input}"


join = JoinNode(name="stats")
hello = Workflow(
    name="hello",
    edges=[
        ("START", classify),
        (classify, {"SMALL": split, "BIG": ask, DEFAULT_ROUTE: ask}),
        (split, count_words, join),
        (split, count_chars, join),
        (join, combine),
        (ask, finish),
    ],
)


def user(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def reply(call, text: str) -> types.Content:
    response = types.FunctionResponse(
        id=call.id, name="adk_request_input", response={"result": text}
    )
    return types.Content(role="user", parts=[types.Part(function_response=response)])


async def run(workflow, message, runner=None, session=None):
    runner = runner or InMemoryRunner(agent=workflow, app_name="lab")
    session = session or await runner.session_service.create_session(
        app_name="lab", user_id="u"
    )
    events = [
        e
        async for e in runner.run_async(
            user_id="u", session_id=session.id, new_message=message
        )
    ]
    return runner, session, events


def pause_of(events):
    for event in events:
        for call in event.get_function_calls():
            if call.name == "adk_request_input":
                return call
    return None


async def main():
    _, _, events = await run(hello, user("a small note"))
    print("SMALL path outputs:", [e.output for e in events if e.output])

    runner, session, events = await run(hello, user("big announcement"))
    call = pause_of(events)
    print("BIG path paused with:", call.args.get("message"))
    _, _, events = await run(hello, reply(call, "yes"), runner, session)
    print("After the reply:", [e.output for e in events if e.output])


asyncio.run(main())
