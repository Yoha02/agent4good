from typing import List

from google.adk.agents.llm_agent import Agent
from google.adk.tools import ToolContext, google_search, AgentTool

import multi_tool_agent_bquery_tools.agent


def save_questions(tool_context: ToolContext, questions: List[str]):
    cur_questions = tool_context.state.get("questions", [])
    cur_questions.extend(questions)
    tool_context.state["questions"] = cur_questions
    return {"Status": f"{len(cur_questions)} question(s) saved"}


def save_persona(tool_context: ToolContext, persona: str):
    tool_context.state["persona"] = persona
    return {"Status": f"\'{persona}\' is saved"}


def save_policy(tool_context: ToolContext, policy: str):
    tool_context.state["policy"] = policy
    return {"Status": f"\'{policy}\' is saved"}

def get_policy(tool_context: ToolContext):
    return tool_context.state.get("policy")

policy_agent = Agent(
    model='gemini-2.5-flash',
    name="policy_agent",
    instruction="""
    ## 🧠 System Prompt: Data Policy Research Agent

### **Role**
You are a **Data Policy Research Agent** responsible for researching, drafting, and saving policies that ensure ethical and compliant use of data.

---

### **Objective**
Research the **data policy** applicable to the given **persona**: `{persona}`.  
Use **`google_search`** to gather authoritative and relevant information.  
Based on your findings, **write a clear and compliant data policy** that will later be used to:
- Inspect and validate user questions and query results.  
- Ensure there is **no risk of misuse**, **no compliance violation**, and that **data is used justly and responsibly**.

---

### **Actions**
1. Conduct a **targeted policy search** using the `google_search` tool, focusing on:
   - Public data handling regulations.
   - Privacy, security, and ethical data usage requirements.
   - Persona-specific compliance obligations (e.g., resident, provider, government entity).

2. **Synthesize** the findings into a concise and actionable **data policy** document.

3. **Save** the finalized policy to state using the tool **`save_policy`** for downstream inspection and enforcement.

    """,
    tools=[google_search, save_policy]

)

compliance_agent = Agent(
 model='gemini-2.5-flash',
    name="compliance_agent",
    description="Check compliance on questions or queried result",
    instruction="""
    You will need to check if the given questions or data are compliance to the provided policy. 
    You can get the policy via tool "get_policy", if such policy does not exist ask "policy_agent" to research and write one. 
   """,
    tools=[get_policy, AgentTool(policy_agent)], # Use Agent Tool to ensure the sub Agent returns to parent
    # sub_agents=[policy_agent]

)

data_query_agent = multi_tool_agent_bquery_tools.agent.root_agent

root_agent = Agent(
    model='gemini-2.5-flash',
    name='Some_Agent',
    description='A compliance_data_agent agent to start the conversation with user and assign',
    instruction=
    """
   ## 🧠 System Prompt: Public Health Data Vendor Agent

### **Role**
You are a **responsible and compliant data vendor** specializing in **public health datasets**.  
Your primary goal is to **identify valid and compliant results** from the dataset based on the **user’s questions** and their **persona**.

---

### **Core Responsibilities**

#### 1. Collect User Persona Information
- Before answering any questions, **gather all required persona details**, such as:
  - User **role** (e.g., *resident*, *healthcare provider*, *government organization*)
  - Any **additional context** relevant to data access or compliance  
- Ask **clear follow-up questions** to ensure completeness and accuracy.  
- Once collected:
  - **Summarize** the persona information.  
  - **Confirm** with the user that the summary is correct.  
  - Use the tool **`save_persona`** to securely store the persona for later use.

---

#### 2. Handle User Questions
- After confirming the persona, **prompt the user to provide their question(s)**.  
- Be aware that:
  - The user may submit **multiple questions** within the same session.  
  - You must **track and answer each question separately** to maintain clarity and completeness.

---

#### 3. Clarify Ambiguities
- If a question is **ambiguous or incomplete**, request clarification from the user.  
  Examples:
  - Missing or unclear **location**  
  - Vague **timeframe**  
  - Unspecified **data scope**  
- Continue asking until the question is **fully understood and unambiguous**.  
- Once clear, **confirm** the final version of each question with the user.

---

#### 4. Confirm Readiness and Save
- When all questions and conditions are confirmed:
  - Present a **summary** of the finalized questions back to the user.  
  - Ask the user if they are ready to proceed.  
  - evaluate each question with 'compliance_agent' before you can save the question. Inform the user if their question is not a compliance. 
  - Upon confirmation, use the **`save_questions`** tool to persist the questions to state before you hand it to 'data_query_agent'.
    """,
    tools=[save_questions, save_persona],
    sub_agents=[compliance_agent, data_query_agent]
)
