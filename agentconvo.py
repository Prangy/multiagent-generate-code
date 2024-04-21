from typing import Callable, Dict, Any, Sequence
import functools
import operator
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
import os


# Initialize model with your OpenAI API key
os.environ["OPENAI_API_KEY"] = "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"
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "laanggraph practice"
os.environ["LANGCHAIN_API_KEY"] = "ls__8aff57aa62a54fea8768ad921350e898"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

# Initialize GPT model
llm = ChatOpenAI(model="gpt-4-turbo-preview")

# Define custom tools
@tool("openai_tool", return_direct=False)
def openai_tool(prompt: str) -> str:
    """Generates text based on the given prompt using GPT model."""
    response = llm.send(prompt)
    return response

tools = [openai_tool]


# Base Agent class
class BaseAgent:
    def __init__(self, llm: ChatOpenAI, tools: list, system_prompt: str):
        self.llm = llm
        self.tools = tools
        self.system_prompt = system_prompt

    def create_executor(self) -> AgentExecutor:
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        executor = AgentExecutor(agent=agent, tools=self.tools)
        return executor

    def create_node(self, name: str) -> Callable:
        raise NotImplementedError


# Specific Agent classes
class ProgrammerAgent(BaseAgent):
    def create_node(self, name: str) -> Callable:
        agent = self.create_executor()
        return functools.partial(agent_node, agent=agent, name=name)

class TesterAgent(BaseAgent):
    def create_node(self, name: str) -> Callable:
        agent = self.create_executor()
        return functools.partial(agent_node, agent=agent, name=name)

class DebuggerAgent(BaseAgent):
    def create_node(self, name: str) -> Callable:
        agent = self.create_executor()
        return functools.partial(agent_node, agent=agent, name=name)

class ExecutorAgent(BaseAgent):
    def create_node(self, name: str) -> Callable:
        agent = self.create_executor()
        return functools.partial(agent_node, agent=agent, name=name)

# Agent Factory
class AgentFactory:
    agent_types = {
        "Programmer": ProgrammerAgent,
        "Tester": TesterAgent,
        "Debugger": DebuggerAgent,
        "Executor": ExecutorAgent,
    }

    @staticmethod
    def get_agent(agent_type: str, llm: ChatOpenAI, tools: List[Callable], system_prompt: str) -> BaseAgent:
        agent_class = AgentFactory.agent_types.get(agent_type)
        if not agent_class:
            raise ValueError(f"Agent type {agent_type} not recognized.")
        return agent_class(llm, tools, system_prompt)

# Helper functions
# Helper functions
def agent_node(state, agent, name):
    while True:
        # Prompt user for input specific to each agent's role
        if name == "Programmer":
            user_input = input("Enter your suggestion for Programmer (press Enter to skip): ")
        elif name == "Tester":
            user_input = input("Enter your suggestion for Tester (press Enter to skip): ")
        elif name == "Debugger":
            user_input = input("Enter your suggestion  for Debugger (press Enter to skip): ")
        elif name == "Executor":
            user_input = input("Enter your suggestion for Executor (press Enter to skip): ")

        # Check if user input is provided
        if user_input.strip():
            state['user_input'] = user_input
            result = agent.invoke(state)
        else:
            # If user didn't provide input, proceed without modifying state
            result = agent.invoke(state)
        
        # Perform agent-user interaction here
        # For example, you can print the output of the agent's processing and prompt the user for feedback or further input
        print("Agent's Output:")
        print(result["output"])

        while True:
            # Ask the user if the output is satisfactory
            feedback = input("Was the agent's output satisfactory? (yes/no): ").lower()

            # Process user feedback
            if feedback == "yes":
                # If user is satisfied, proceed to the next agent
                state['messages'] = [HumanMessage(content=result["output"], name=name)]
                next_agent = state.get("next", None)
                if next_agent:
                    return {"messages": [HumanMessage(content=result["output"], name=name)], "next": next_agent}
                else:
                    return {"messages": [HumanMessage(content=result["output"], name=name)]}
            elif feedback == "no":
                    break  # Exit the inner loop
            else:
                print("Invalid feedback. Please enter 'yes' or 'no'.")
                # Continue the inner loop for another iteration

        # Continue the outer loop for another iteration


# Agent State and Workflow Setup
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# Define the workflow creation function
def create_workflow(llm: ChatOpenAI, tools: List):
        # Define system prompts for each agent
    programmer_system_prompt = '''**Role**: You are an expert software python programmer. You need to develop and generate python code.
    **Task**: As a programmer, you are required to complete the function. Use a Chain-of-Thought approach to break
    down the problem, create pseudocode, and then write the code in Python language. Ensure that your code is
    efficient, readable, and well-commented.
    **Instructions**:
    1. **Understand and Clarify**: Make sure you understand the task.
    2. **Algorithm/Method Selection**: Decide on the most efficient way.
    3. **Pseudocode Creation**: Write down the steps you will follow in pseudocode.
    4. **Code Generation**: Translate your pseudocode into executable Python code.'''

    tester_system_prompt = '''**Role**: As a tester, your task is to create Basic and Simple test cases based on provided Requirement and Python Code. 
    These test cases should encompass Basic, Edge scenarios to ensure the code's robustness, reliability, and scalability.
    **1. Basic Test Cases**:
    - **Objective**: Basic and Small scale test cases to validate basic functioning 
    **2. Edge Test Cases**:
    - **Objective**: To evaluate the function's behavior under extreme or unusual conditions.
    **Instructions**:
    - Implement a comprehensive set of test cases based on requirements.
    - Pay special attention to edge cases as they often reveal hidden bugs.
    - Only Generate Basics and Edge cases which are small
    - Avoid generating Large scale and Medium scale test case. Focus only small, basic test-cases.'''

    debugger_system_prompt = """You are expert in Python Debugging. You have to analysis Given Code and Error and generate code that handles the error
    *Instructions*:
    - Make sure to generate error free code
    - Generated code is able to handle the error."""

    executor_system_prompt = """You have to add testing layer in the *Python Code* that can help to execute the code. You need to pass only Provided Input as argument and validate if the Given Expected Output is matched.
    *Instruction*:
    - Make sure to return the error if the assertion fails
    - Generate the code that can be execute
    Python Code to execute:"""

    # Create agents using the factory pattern
    programmer_agent = AgentFactory.get_agent("Programmer", llm, tools, programmer_system_prompt)
    tester_agent = AgentFactory.get_agent("Tester", llm, tools, tester_system_prompt)
    debugger_agent = AgentFactory.get_agent("Debugger", llm, tools, debugger_system_prompt)
    executor_agent = AgentFactory.get_agent("Executor", llm, tools, executor_system_prompt)

    # Create nodes for each agent
    programmer_node = programmer_agent.create_node("Programmer")
    tester_node = tester_agent.create_node("Tester")
    debugger_node = debugger_agent.create_node("Debugger")
    executor_node = executor_agent.create_node("Executor")

    # Define the agent state, edges, and graph
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]

    workflow = StateGraph(AgentState)
    workflow.add_node("Programmer", programmer_node)
    workflow.add_node("Tester", tester_node)
    workflow.add_node("Debugger", debugger_node)
    workflow.add_node("Executor", executor_node)

    workflow.set_entry_point("Programmer")
    workflow.add_edge("Programmer", "Tester")
    workflow.add_edge("Debugger", "Executor")
    workflow.add_edge("Tester", "Executor")

    # Define the conditional function
    def decide_to_end(state):
        if 'errors' in state and state['errors']:
            return 'Debugger'
        else:
            return 'end'

    # Now, let's add conditional edges based on the flow of the process
    workflow.add_conditional_edges(
        "Executor",
        decide_to_end,
        {
            "end": END,
            "Debugger": "Debugger",
        },
    )

    # Compile and run the graph
    graph = workflow.compile()

    # Accept user input for human message content
    content = input("Enter the question you want to ask: ")

    # Run the graph
    for s in graph.stream({
        "messages": [HumanMessage(content=content)]
    }):
        if "__end__" not in s:
            print(s)
            print("----")
create_workflow(llm, tools)


