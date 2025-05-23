import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

# This will become dynamic later with agentscope router
def build_prompt(prompt: str) -> str:
    system_prompt = "You are a due diligence analyst. Respond concisely with investor-relevant insights."
    return f"{system_prompt}\n\nUser: {prompt}\nAI:"

async def run_agent_handler(data):
    try:
        prompt = data.get("prompt")
        deal_id = data.get("deal_id", "unknown")

        if not prompt:
            return {"error": "Missing prompt"}

        final_prompt = build_prompt(prompt)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful M&A diligence assistant."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.4
        )

        result = response['choices'][0]['message']['content']

        return {
            "status": "ok",
            "deal_id": deal_id,
            "agent_output": result
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

