import asyncio

from agent.agent_runner import ask_agent


async def main():

    response = await ask_agent(
        "Show me stocks with breakout signals"
    )

    print(response)


asyncio.run(main())