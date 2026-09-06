import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import root_agent


session_service = InMemorySessionService()


runner = Runner(
    agent=root_agent,
    app_name="pulsetrade_ai",
    session_service=session_service
)


async def _run_agent(question):

    session = await session_service.create_session(
        app_name="pulsetrade_ai",
        user_id="streamlit_user"
    )


    content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=question
            )
        ]
    )


    response_text = ""


    async for event in runner.run_async(
        user_id="streamlit_user",
        session_id=session.id,
        new_message=content
    ):

        if event.is_final_response():

            response_text = (
                event.content
                .parts[0]
                .text
            )


    return response_text



def run_agent(question):

    return asyncio.run(
        _run_agent(question)
    )