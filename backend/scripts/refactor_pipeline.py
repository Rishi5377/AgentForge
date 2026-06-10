import os

path = r'C:\Users\lenovo\Downloads\AgentForge\backend\workflows\pipeline.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import1 = "from tenacity import retry, stop_after_attempt, wait_exponential\nfrom langgraph.prebuilt import create_react_agent"
text = text.replace("from langgraph.prebuilt import create_react_agent", import1)

old_agent = '''def create_single_shot_agent(model, tools, prompt_func):
    model_with_tools = model.bind_tools(tools)
    
    async def agent_node(state: GraphState, config: RunnableConfig):
        system_prompt = prompt_func(state)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please implement the required files using the provided tools. Ensure your tool calls are properly formatted without any syntax errors.")
        ]
        
        response = await model_with_tools.ainvoke(messages, config)
        print(f"Agent response tool calls: {response.tool_calls}")
        if not response.tool_calls:
            print(f"Agent response content: {response.content}")
        
        if response.tool_calls:
            for tc in response.tool_calls:
                tool_name = tc["name"]
                args = tc["args"]
                tool_instance = next((t for t in tools if t.name == tool_name), None)
                if tool_instance:
                    await tool_instance.ainvoke(args, config=config)
                    
        return {"messages": [response]}
        
    return agent_node'''

new_agent = '''def create_react_loop_agent(model, tools, prompt_func):
    react_graph = create_react_agent(model, tools)
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=30))
    async def invoke_with_retry(messages, config):
        return await react_graph.ainvoke({"messages": messages}, config)

    async def agent_node(state: GraphState, config: RunnableConfig):
        system_prompt = prompt_func(state)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Please implement the required files using the provided tools. You can use tools multiple times to fix any mistakes.")
        ]
        
        result = await invoke_with_retry(messages, config)
        return {"messages": result["messages"][-1:]}
        
    return agent_node'''

text = text.replace(old_agent, new_agent)

text = text.replace("create_single_shot_agent", "create_react_loop_agent")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("pipeline.py rewritten successfully!")
