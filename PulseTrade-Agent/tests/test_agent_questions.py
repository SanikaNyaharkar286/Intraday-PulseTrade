import asyncio

from agent.agent_runner import ask_agent


async def run_test():

    questions = [

        "What is the current market state?",

        "Which stocks showed breakout signals?",

        "Which stocks are holding above VWAP?",

        "Show me top momentum stocks",

        "Analyze RELIANCE intraday behavior",

        "Show RELIANCE historical performance"

    ]


    for question in questions:

        print("\n")
        print("=" * 80)
        print("QUESTION:")
        print(question)
        print("=" * 80)


        response = await ask_agent(
            question
        )


        print(response)



asyncio.run(run_test())
