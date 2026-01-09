from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm_chain():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an EdTech assistant for parents. "
            "Explain student performance clearly, politely, and simply. "
            "Never invent marks. Only use provided student data."
        ),
        ("human", "{question}")
    ])

    chain = prompt | llm
    return chain
