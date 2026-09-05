import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agent.agent import root_agent


async def main():

    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name="pulsetrade",
        session_service=session_service
    )


    session = await session_service.create_session(
        app_name="pulsetrade",
        user_id="test_user"
    )


    response = runner.run(
        user_id="test_user",
        session_id=session.id,
        new_message={
            "role": "user",
            "parts": [
                {
                    "text": "Which stocks have RSI below 30?"
                }
            ]
        }
    )


    async for event in response:
        if event.content:
            print(event.content)


asyncio.run(main())