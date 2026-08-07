import json
import uuid
from databricks.sdk import WorkspaceClient
from databricks_openai import UCFunctionToolkit, DatabricksFunctionClient
from typing import Any, Optional, Iterator

import mlflow
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import ChatAgentMessage, ChatAgentResponse, ChatContext

# Get an OpenAI client configured to talk to Databricks model serving endpoints
# We'll use this to query an LLM in our agent
openai_client = WorkspaceClient().serving_endpoints.get_open_ai_client()

# The snippet below tries to pick the first LLM API available in your Databricks workspace
# from a set of candidates. You can override and simplify it
# to just specify LLM_ENDPOINT_NAME.
LLM_ENDPOINT_NAME = "databricks-claude-3-7-sonnet"

# Enable automatic tracing of LLM calls
mlflow.openai.autolog()


@mlflow.trace
def run_agent(content, system_prompt=None):
    """
    Send a user prompt to the LLM, and return a list of LLM response messages
    The LLM is allowed to call the code interpreter tool if needed, to respond to the user
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": content})
    
    response = openai_client.chat.completions.create(
        model=LLM_ENDPOINT_NAME,
        messages=messages,
    )
    msg = response.choices[0].message
    return [msg.to_dict()]


class QuickstartAgent(ChatAgent):
    def __init__(self):
        super().__init__()
        self.system_prompt = (
            "You are a sentiment analysis expert. Analyze text sentiment "
            "and respond with exactly one word: positive, neutral, or negative."
        )
    
    def predict(
        self,
        messages: list[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[dict[str, Any]] = None,
    ) -> ChatAgentResponse:
        message = messages[-1].content
        user_prompt = f"Analyze this phrase: {message}"
        raw_msgs = run_agent(
            content=user_prompt,
            system_prompt=self.system_prompt
        )
        out = []
        for m in raw_msgs:
            out.append(ChatAgentMessage(
                id=uuid.uuid4().hex,
                **m
            ))
        return ChatAgentResponse(messages=out)


AGENT = QuickstartAgent()
mlflow.models.set_model(AGENT)
