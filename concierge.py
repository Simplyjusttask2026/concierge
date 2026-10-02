import os, time
# Keys come from environment variables (set on Render) - safe!

from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, LLM
import crewai.llm as _crew_llm_mod
from composio import Composio
from composio_crewai import CrewAIProvider

# ====== FIX: CrewAI adds 'cache_breakpoint' markers for prompt caching,
# but litellm passes them to Groq, which rejects them. Patch CrewAI's
# message formatter to strip the marker for non-caching providers. ======
_orig_fmt = _crew_llm_mod.LLM._format_messages_for_provider

def _fmt_no_cache_breakpoint(self, messages):
    if messages:
        messages = [
            {k: v for k, v in m.items() if k != "cache_breakpoint"}
            for m in messages
        ]
    return _orig_fmt(self, messages)

_crew_llm_mod.LLM._format_messages_for_provider = _fmt_no_cache_breakpoint

# ====== EDIT THIS: tell the concierge about your business ======
BUSINESS_INFO = """
You are the friendly concierge for Simply Just Task, a service that helps
businesses organize and automate their tasks using monday.com.
Be warm, concise, and helpful. If you do not know something, say so and
offer to take a message.
"""

llm = LLM(model="groq/openai/gpt-oss-120b")
composio = Composio(provider=CrewAIProvider())
tools = composio.tools.get(user_id="default", tools=[
    "MONDAY_LIST_BOARDS",
    "MONDAY_LIST_BOARD_ITEMS",
    "MONDAY_LIST_ITEMS",
])

agent = Agent(
    role="Website Concierge",
    goal="Answer guest questions helpfully and warmly",
    backstory=BUSINESS_INFO,
    tools=tools,
    llm=llm,
    verbose=True,
)

app = Flask(__name__)
CORS(app)

@app.route("/api/chat", methods=["POST"])
def chat():
    message = request.json.get("message", "").strip()
    if not message:
        return jsonify({"reply": "Please type a message! :)"})
    task = Task(description="A website guest asks: " + message,
                expected_output="A short, friendly, helpful reply (2-3 sentences)",
                agent=agent)
    for attempt in range(4):
        try:
            result = Crew(agents=[agent], tasks=[task]).kickoff()
            return jsonify({"reply": str(result)})
        except Exception as e:
            if "rate_limit" in str(e).lower():
                time.sleep(45)
            else:
                return jsonify({"reply": "Oops, I hiccuped! Try again?"})

@app.route("/")
def home():
    return "Concierge is alive!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
