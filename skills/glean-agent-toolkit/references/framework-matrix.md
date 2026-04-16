# Framework Integration Matrix

> Verified against `glean-agent-toolkit` v0.5.0.

The toolkit exposes the same `@tool_spec`-decorated function across all frameworks. Adaptation happens at the call site via `.as_<framework>_tool()` or `get_tools("<framework>")`. This file is the operational glue — the exact lines you need to wire a tool into each framework's agent constructor.

For SDK semantics (decorator internals, `GleanContext` behavior, schema generation), use the `glean-agent-toolkit-guide` skill.

---

## OpenAI Agents SDK

**Pip extra:** `openai`
**Install:** `pip install "glean-agent-toolkit[openai]"`
**Imports:**
```python
import os
from agents import Agent, Runner
from glean.agent_toolkit.tools import search
```
**Wire a tool:**
```python
agent = Agent(
    name="KnowledgeAssistant",
    instructions="Help users find information from the company knowledge base.",
    tools=[search.as_openai_tool()],
)
```
**Or pull all built-ins at once:**
```python
from glean.agent_toolkit import get_tools
agent = Agent(name="…", instructions="…", tools=get_tools("openai"))
```
**Run:**
```python
result = Runner.run_sync(agent, "Find our Q4 planning documents")
print(result.final_output)
```
**Required env (in addition to Glean creds):** `OPENAI_API_KEY`.

---

## LangChain / LangGraph

**Pip extra:** `langchain`
**Install:** `pip install "glean-agent-toolkit[langchain]" langchain langchain-openai`
**Imports:**
```python
import os
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from glean.agent_toolkit.tools import search
```
**Wire a tool:**
```python
llm = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(llm, tools=[search.as_langchain_tool()])
```
**Run:**
```python
result = agent.invoke({"messages": [("user", "Find our Q4 planning documents")]})
print(result["messages"][-1].content)
```
**Required env:** `OPENAI_API_KEY` (or whichever provider you wire to LangChain).
**Note:** the upstream extra installs `langchain-core` only — pull in `langchain` / `langgraph` / a model provider package separately depending on your stack.

---

## Google ADK

**Pip extra:** `adk`
**Install:** `pip install "glean-agent-toolkit[adk]"`
**Imports:**
```python
import os
from google.adk.agents import Agent
from glean.agent_toolkit.tools import search
```
**Wire a tool:**
```python
root_agent = Agent(
    name="company_assistant",
    model="gemini-2.0-flash",
    description="Company assistant that searches the knowledge base.",
    instruction="You are a helpful company assistant. Use search to answer questions.",
    tools=[search.as_adk_tool()],
)
```
**Run:** ADK agents typically run via `adk web` or `adk run` from the project root. See ADK docs for the runner.
**Required env:** `GOOGLE_API_KEY` (or Vertex AI auth).

---

## CrewAI (out of scope for `/glean:init`)

The toolkit supports CrewAI via `.as_crewai_tool()` and `get_tools("crewai")`. We do **not** scaffold CrewAI projects via `/glean:init` (per scope decision), but the adapter still works — see the upstream `glean-agent-toolkit-guide` skill for usage.

---

## Tool-binding cheat sheet

| Framework | Single tool | All built-ins |
|-----------|-------------|---------------|
| OpenAI Agents SDK | `search.as_openai_tool()` | `get_tools("openai")` |
| LangChain | `search.as_langchain_tool()` | `get_tools("langchain")` |
| Google ADK | `search.as_adk_tool()` | `get_tools("adk")` |
| CrewAI | `search.as_crewai_tool()` | `get_tools("crewai")` |

## Common gotchas at the integration layer

1. **Pip name vs import name** — install `glean-agent-toolkit` (hyphens), import `glean.agent_toolkit` (dot + underscore). The hyphen/underscore swap is a frequent source of `ModuleNotFoundError`.
2. **Adapter call returns a NEW object each time** — bind once at module scope; don't re-create per request.
3. **`GleanContext` must be the first parameter and optional with `None` default** — otherwise the adapter exposes `ctx` in the JSON schema and the LLM tries to pass it.
4. **`get_tools(framework)` requires the matching extra** — `get_tools("langchain")` without `[langchain]` extra raises `ImportError`.
