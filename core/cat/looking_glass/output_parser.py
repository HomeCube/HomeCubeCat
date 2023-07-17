import re
from pydantic import BaseModel
from cat.mad_hatter.mad_hatter import MadHatter
from langchain.agents import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from typing import List, Union


class ToolOutputParser(AgentOutputParser, BaseModel):

    class Config:
        extra = "allow"  # Allow extra attributes

    def __init__(self, mad_hatter: MadHatter, **data):
        super().__init__(**data)
        self.mad_hatter = mad_hatter

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        self.mad_hatter.execute_hook("after_tool_used", action)
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)