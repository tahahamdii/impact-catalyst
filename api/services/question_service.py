from pydantic import BaseModel
from fastapi import HTTPException
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from api.models.retriever import get_vector_retriever
from langchain_google_genai import ChatGoogleGenerativeAI, ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from api.models.get_database_collection import get_collections
import os
from dotenv import load_dotenv


load_dotenv()


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
embeddings_collection = get_collections().get('embeddings')


# Request model
class QuestionRequest(BaseModel):
    user_input: str

# Function to answer question
def process_question(user_input: str):
    if not user_input:
        raise HTTPException(status_code=400, detail="User input is required")
        
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2, api_key=GOOGLE_API_KEY)
    template = """
    Task: Answer the question using only the provided context: {context}.
    Context: The documents consist of reports, policies, and publications related to Climate Change and Gender Inequality.
    Instructions:
        Provide accurate, detailed answers strictly based on the given documents.
        Cite relevant references on the relationship between gender and climate change.
        Do not introduce information beyond the documents or make assumptions.
        If the query is unclear or lacks sufficient detail, ask for clarification before responding.
        Maintain a neutral tone in your answer.
        Avoid starting with phrases like "The provided text..."
    Question: {question}
    """
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )
    retriever = get_vector_retriever(embeddings_collection)
    rag_chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough()
        }
        | prompt_template
        | model
        | StrOutputParser()
    )
    answer = rag_chain.invoke(user_input)
    return answer
