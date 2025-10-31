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
        client_session_timeout_seconds=60.0,  # Allow time for server initialization
    ) as filesystem_server:
        async with MCPServerStdio(
            name="PDF Indexer",
            params={
                "command": "/Users/annhoward/openai_agents_10_23_25/env/bin/python3",
                "args": ["/Users/annhoward/openai_agents_10_23_25/semantic_chunked_pdf_rag.py"],
            },
            client_session_timeout_seconds=60.0,  # Longer timeout for RAG server initialization
        ) as pdf_indexer_server:
            math_tutor_agent = Agent(
                name="Tutor",
                handoff_description="Specialist tutor agent for questions",
                instructions="You provide help with homework problems. Explain your reasoning at each step and include examples",
                mcp_servers=[filesystem_server, pdf_indexer_server],
                tools=[WebSearchTool()],
                model="gpt-5"
            )

            result = await Runner.run(math_tutor_agent, "List all the papers in the database.")
            print(result.final_output)



if __name__ == "__main__":
    asyncio.run(main())