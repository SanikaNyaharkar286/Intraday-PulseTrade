from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent.agent import root_agent


APP_NAME = "pulsetrade_ai"


session_service = InMemorySessionService()


runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


async def ask_agent(
    user_message: str,
    user_id: str = "streamlit_user",
):

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
    )


    content = types.Content(
        role="user",
        parts=[
            types.Part(
                text=user_message
            )
        ],
    )


    final_response = ""


    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=content,
    ):

        if event.is_final_response():

            final_response = (
                event.content
                .parts[0]
                .text
            )


    return final_response