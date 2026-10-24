"""Quality flywheel skeleton. Fill in the two TODOs from the SDK docs."""

import os

from vertexai import Client

client = Client(project=os.environ["PROJECT_ID"], location=os.environ["REGION"])

# TODO 1: build my_agent_info and my_agent for your Q&A agent. See the
# "Evaluate your agents" page and the SDK reference for AgentInfo.
my_agent_info = ...
my_agent = ...

# 1. Generate synthetic multi-turn scenarios from the agent's own setup.
eval_dataset = client.evals.generate_conversation_scenarios(
    agent_info=my_agent_info,
    config={
        "count": 5,
        "generation_instruction": "Scenarios where a user asks about invoices, POs, and "
        "vendors, and sometimes asks the agent to approve or "
        "pay something it cannot.",
    },
)

# 2. Run the agent against a simulated user to capture traces.
traces = client.evals.run_inference(
    agent=my_agent,
    src=eval_dataset,
    config={"user_simulator_config": {"max_turn": 5}},
)

# 3. Score whole conversations with multi-turn AutoRaters.
eval_result = client.evals.evaluate(
    traces=traces,
    metrics=["MULTI_TURN_TASK_SUCCESS", "MULTI_TURN_TOOL_USE_QUALITY"],
)

# 4. Group failures into clusters of the same kind of problem.
loss_clusters = client.evals.generate_loss_clusters(eval_result=eval_result)
print(loss_clusters)
