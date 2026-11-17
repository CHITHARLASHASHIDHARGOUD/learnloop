import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from helpers.gemini_utils import (
    DEFAULT_GEMINI_MODEL,
    GeminiRestEmbeddings,
    configure_gemini
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "faiss_index")

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    return text

def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    return chunks

def get_vector_store(chunks):
    embeddings = GeminiRestEmbeddings()
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    os.makedirs(INDEX_PATH, exist_ok=True)
    vector_store.save_local(INDEX_PATH)

def get_conversational_chain():
    key = configure_gemini()
    prompt_template = """Answer the question as detailed as possible from the provided context. Make sure to provide all the details.
If the answer is not in the provided context, just say: "answer is not available in the context", do not provide the wrong answer.

Context:
{context}

Question:
{question}

Answer:
"""
    model = ChatGoogleGenerativeAI(
        model=DEFAULT_GEMINI_MODEL,
        temperature=0.3,
        google_api_key=key,
        transport="rest"
    )
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
    return chain

def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "Upload your PDF files in the sidebar and ask me any question!"}
    ]

def user_input(user_question):
    if not os.path.exists(INDEX_PATH) or not os.path.exists(os.path.join(INDEX_PATH, "index.faiss")):
        return {"output_text": "Please upload and process at least one PDF file from the sidebar first."}

    embeddings = GeminiRestEmbeddings()

    try:
        new_db = FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain.invoke({"input_documents": docs, "question": user_question})
        return response
    except Exception as e:
        return {"output_text": f"Error answering question: {e}"}

def PDF_CHAT():
    configure_gemini()

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader(
            "Upload your PDF Files and Click on the Submit & Process Button",
            type=["pdf"],
            accept_multiple_files=True
        )

        if st.button("Submit & Process"):
            if not pdf_docs:
                st.warning("Please upload at least one PDF file first.")
            else:
                with st.spinner("Processing PDF files..."):
                    raw_text = get_pdf_text(pdf_docs)
                    if not raw_text.strip():
                        st.error("No extractable text found in the uploaded PDF(s).")
                    else:
                        text_chunks = get_text_chunks(raw_text)
                        get_vector_store(text_chunks)
                        st.success("PDF processed successfully! You can now ask questions.")

    st.title("Chat with PDF files using Gemini 🤖")
    st.write("Welcome to PDF Chat! Upload course materials or documents and ask questions.")
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Upload your PDF files in the sidebar and ask me any question!"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if prompt := st.chat_input("Ask a question about the uploaded document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

    if st.session_state.messages and st.session_state.messages[-1]["role"] != "assistant":
        last_question = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = user_input(last_question)
                full_response = response.get('output_text', '')
                st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    PDF_CHAT()
