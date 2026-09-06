import streamlit as st

from utils.response_formatter import format_response
from runner import run_agent

st.set_page_config(
    page_title="PulseTrade AI",
    page_icon="📈",
    layout="wide"
)


# -----------------------------
# Header
# -----------------------------

st.title("📈 PulseTrade AI")

st.caption(
    "AI-powered intraday market intelligence assistant"
)


st.markdown(
"""
### 👋 Welcome Trader

Ask me anything about the market.
"""
)


# -----------------------------
# Suggested Questions
# -----------------------------

st.subheader("💡 Try asking")


suggestions = [

    "Find stocks trading above VWAP",

    "Find stocks with RSI below 30",

    "Show stocks with MACD bullish crossover",

    "Find high volume breakout stocks",

    "Analyze RELIANCE technical indicators",

    "Compare HDFC vs ICICI",

    "Show today's top gainers",

    "What are today's breakout stocks?"

]


cols = st.columns(3)


for index, question in enumerate(suggestions):

    if cols[index % 3].button(
        question,
        use_container_width=True
    ):

        st.session_state.selected_question = question



# -----------------------------
# Chat History
# -----------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []



for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


        if "table" in message:

            st.dataframe(
                message["table"],
                use_container_width=True
            )

# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:

    st.header("⚙️ Agent Info")


    st.markdown(
    """
    **🤖 Model**

    Gemini 2.5 Flash


    **📚 Data Source**

    PulseTrade Semantic Layer


    **🔍 Available Analysis**

    ✓ Current Market State  
    ✓ Intraday Behaviour  
    ✓ Trading Signals  
    ✓ Stock Ranking  
    ✓ Daily History  
    ✓ Intraday History  
    ✓ Stock Comparison  

    """
    )


    st.divider()


    st.caption(
        "Powered by Google ADK + Gemini"
    )

# -----------------------------
# Input
# -----------------------------

question = st.chat_input(
    "Ask PulseTrade AI..."
)


if "selected_question" in st.session_state:

    question = st.session_state.selected_question

    del st.session_state.selected_question



if question:


    st.session_state.messages.append(
        {
            "role":"user",
            "content":question
        }
    )


    with st.chat_message("user"):

        st.write(question)



    with st.chat_message("assistant"):


        with st.spinner(
            "🔎 Analyzing market data..."
        ):


            # Replace this with ADK runner

            result = run_agent(question)


            response = format_response(
                result,
                question
            )


            st.markdown(
                response["text"]
            )


            if response["table"] is not None:

                st.dataframe(
                    response["table"],
                    use_container_width=True
                )


            st.session_state.messages.append(
                {
                    "role":"assistant",
                    "content":response["text"],
                    "table":response["table"]
                }
            )