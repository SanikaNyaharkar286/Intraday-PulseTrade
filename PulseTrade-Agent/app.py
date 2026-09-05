import streamlit as st

from utils.response_formatter import format_response


st.set_page_config(
    page_title="PulseTrade AI",
    page_icon="📈",
    layout="wide"
)


st.title("📈 PulseTrade AI")

st.caption(
    "AI-powered stock market analysis assistant"
)


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if "table" in message:
            st.dataframe(
                message["table"],
                use_container_width=True
            )


question = st.chat_input(
    "Ask about stocks, signals, trends..."
)


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
            "Analyzing market data..."
        ):

            # ADK runner call comes here

            result = {
                "symbol":"TEST"
            }


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