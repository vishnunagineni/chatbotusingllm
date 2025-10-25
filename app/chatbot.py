import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from tavily import TavilyClient

#Make sure .env file exists
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
tavely_api_key = os.getenv("TAVILY_API_KEY")

if not groq_api_key or not tavely_api_key:
    st.error("⚠️ Please add your API keys to a .env file.")
    st.stop()

#Home Page for Chatbot
st.set_page_config(page_title="Groq Chatbot with Web Search", page_icon="🤖", layout="centered")
st.title("🤖 Groq LLaMA Chatbot with Web Search Fallback")
st.caption("Ask questions. If Groq doesn't know, it searches the web for answers.")

#Initialize Groq LLM
llm = ChatGroq(model = "openai/gpt-oss-120b",temperature = 0.7,api_key=groq_api_key)

#Chat Memory History
memory = InMemoryChatMessageHistory()

#Web search client
search_client = TavilyClient(api_key=tavely_api_key)

#Creating Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system","You are a helpful AI assistant. If you don't know the answer or response, say 'I don't know."),
    MessagesPlaceholder(variable_name = "chat_history"),
    ("human","{input}")
])



# ChatHistory Session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input
user_input = st.chat_input("Type your message here...")

def ask_with_web_fallback(question: str) -> str:
    # Step 1: Ask Groq LLM
    # Fill the prompt with user input and chat history
    formatted_prompt = prompt.format(
        input=question,
        chat_history=st.session_state.chat_history  # list of HumanMessage/AIMessage
    )
    print(formatted_prompt)
    # Invoke LLM with the fully formatted string
    response = llm.invoke(formatted_prompt)
    answer_text = response.content if hasattr(response, "content") else str(response)
    print(answer_text)
    # Step 2: Detect LLM "I don't know" responses
    if "i don't know" in answer_text.lower() or "I'm a large language model" in answer_text.lower():
        # Step 3: Web search with Tavily
        search_results = search_client.search(query=question, num_results=5)
        combined_text = "\n".join(
            res.get("content", res) if isinstance(res, dict) else res
            for res in search_results
        )
        
        # Step 4: LLM synthesizes final answer from search results
        synthesis_prompt = (
            f"User question: {question}\n\n"
            f"Web search results:\n{combined_text}\n\n"
            "Provide a concise, accurate answer based on these sources."
        )
        final_response = llm.invoke(synthesis_prompt)
        answer_text = final_response.content if hasattr(final_response, "content") else str(final_response)

    # Update chat memory
    st.session_state.chat_history.append(HumanMessage(content=question))
    st.session_state.chat_history.append(AIMessage(content=answer_text))

    return answer_text

# Handle user input
if user_input:
    st.chat_message("user").write(user_input)
    with st.spinner("Thinking..."):
        ai_response = ask_with_web_fallback(user_input)
        st.chat_message("assistant").write(ai_response)

# Optional: show full conversation
with st.expander("💬 Conversation History"):
    for msg in st.session_state.chat_history:
        if isinstance(msg, HumanMessage):
            st.markdown(f"**🧑 You:** {msg.content}")
        elif isinstance(msg, AIMessage):
            st.markdown(f"**🤖 Groq:** {msg.content}")