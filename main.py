import asyncio
import httpx
from agents import Agent
from agents import Runner
from agents import WebSearchTool
from agents.mcp import MCPServerStdio
from agents.extensions.models.litellm_model import LitellmModel
from litellm import CustomLLM, completion, get_llm_provider
import litellm

class MyCustomLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        # Extract the parameters
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "")
        api_base = kwargs.get("api_base", "http://localhost:8822")
        
        # Make the actual HTTP request to your local LLM
        # Assuming it follows OpenAI-compatible format
        client = httpx.Client()
        try:
            response = client.post(
                f"{api_base}/v1/chat/completions",
                json={
                    "model": model.split("/")[-1] if "/" in model else model,
                    "messages": messages,
                },
                timeout=60.0
            )
            response.raise_for_status()
            
            # Convert the response to litellm.ModelResponse format
            response_json = response.json()
            
            # Return in LiteLLM format
            return litellm.ModelResponse(**response_json)
        finally:
            client.close()
    
    async def acompletion(self, *args, **kwargs) -> litellm.ModelResponse:
        # Extract the parameters
        messages = kwargs.get("messages", [])
        model = kwargs.get("model", "")
        api_base = kwargs.get("api_base", "http://localhost:8822")
        
        # Make the actual HTTP request to your local LLM
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{api_base}/v1/chat/completions",
                json={
                    "model": model.split("/")[-1] if "/" in model else model,
                    "messages": messages,
                },
                timeout=60.0
            )
            response.raise_for_status()
        
            # Convert the response to litellm.ModelResponse format
            response_json = response.json()
            
            # Return in LiteLLM format
            return litellm.ModelResponse(**response_json)
    
my_custom_llm = MyCustomLLM()

litellm.custom_provider_map = [ # 👈 KEY STEP - REGISTER HANDLER
        {"provider": "my-custom-llm", "custom_handler": my_custom_llm}
    ]
    

async def main():
    async with MCPServerStdio(
        name="Filesystem Server via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str("./")],
        },
    ) as server:
        math_tutor_agent = Agent(
            name="Tutor",
            handoff_description="Specialist tutor agent for questions",
            instructions="You provide help with homework problems. Explain your reasoning at each step and include examples",
            mcp_servers=[server],
            #tools=[WebSearchTool()],
            model=LitellmModel(base_url="http://localhost:8822", model="my-custom-llm/Qwen3-4B-4bit", api_key="...")
        )

        result = await Runner.run(math_tutor_agent, "Explain everything I need to know in order to understand holographic universe theory, saving several Markdown files about them, and then writing a final high-level explanatory report in the current directory.")
        print(result.final_output)



if __name__ == "__main__":
    asyncio.run(main())