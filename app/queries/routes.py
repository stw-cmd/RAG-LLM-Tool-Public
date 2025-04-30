# app/queries/routes.py
import os
import logging
import warnings

from flask import (
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required, current_user
from pydantic import PydanticDeprecatedSince211

from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.schema import Document as LC_Document
from langchain_openai import ChatOpenAI
# PDF loader
from langchain_community.document_loaders import PyPDFLoader

from app.extensions import db
from app.models import QueryHistory, UploadedDocument
from app.utils import update_user_vectorstore
from . import query_bp

# Suppress the ChromaDB / Pydantic deprecation warning
warnings.filterwarnings(
    "ignore",
    category=PydanticDeprecatedSince211,
    message="Accessing this attribute on the instance is deprecated.*"
)

# Silence overly verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("app.utils").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# PromptTemplate forcing the model to use only retrieved context
QA_TEMPLATE = """
You are a question-answering assistant. Use *only* the information in the context below to answer.
If the answer is not contained in the context, respond exactly with "I don't know."

Context:
{context}

Question:
{question}

Answer:"""

QA_PROMPT = PromptTemplate(
    template=QA_TEMPLATE,
    input_variables=["context", "question"]
)

@query_bp.route("/query", methods=["POST"])
@login_required
def process_query():
    # Get and validate the question
    question = request.form.get("question", "").strip()
    if not question:
        flash("No question provided.")
        return redirect(url_for("dashboard"))

    # Re-load all of the user's documents from disk, handling PDFs separately
    docs = []
    user_docs = UploadedDocument.query.filter_by(user_id=current_user.id).all()
    for doc in user_docs:
        path = os.path.join("uploads", str(current_user.id), doc.filename)
        if not os.path.exists(path):
            continue
        try:
            if doc.filename.lower().endswith('.pdf'):
                # Use PyPDFLoader for PDFs
                loader = PyPDFLoader(path)
                pages = loader.load()
                for page in pages:
                    docs.append(
                        LC_Document(
                            page_content=page.page_content,
                            metadata={**page.metadata, "filename": doc.filename}
                        )
                    )
            else:
                # Read plain text or scraped .txt files
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                if text:
                    docs.append(
                        LC_Document(
                            page_content=text,
                            metadata={"filename": doc.filename}
                        )
                    )
        except Exception as e:
            logger.error("Error reading %s: %s", path, e)

    # Rebuild the vector store for this user
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from chromadb.config import Settings

    embeddings = OpenAIEmbeddings(
        openai_api_key=current_app.config.get("OPENAI_API_KEY")
    )
    vectorstore = update_user_vectorstore(
        current_user.id,
        docs,
        embeddings,
        Chroma,
        Settings
    )

    # Initialise ChatOpenAI for gpt-4o-mini (this can be replaced with other OpenAI models)
    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0,
        openai_api_key=current_app.config["OPENAI_API_KEY"]
    )

    # Configure the retriever to fetch top 3 most relevant chunks
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # Build the RetrievalQA chain using our custom prompt
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )

    try:
        # Use the new invoke() interface instead of deprecated run()
        result = qa_chain.invoke({"query": question})
        # Extraction: if result is a dict, pull out the "result" key; else assume it's a string
        answer = result.get("result") if isinstance(result, dict) else result
    except Exception as e:
        logger.error("Error during QA: %s", e)
        flash("Error processing your query. Please try again.")
        return redirect(url_for("dashboard"))

    # Save the Q&A to user history
    record = QueryHistory(
        question=question,
        answer=answer,
        user_id=current_user.id
    )
    try:
        db.session.add(record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error("Error saving query: %s", e)
        flash("Error saving your query.")
        return redirect(url_for("dashboard"))

    flash("Query processed!")
    return redirect(url_for("dashboard"))

@query_bp.route("/delete_query/<int:query_id>", methods=["POST"])
@login_required
def delete_query(query_id):
    # Load the query history record
    q = QueryHistory.query.get_or_404(query_id)
    # Ensure the user owns this query
    if q.user_id != current_user.id:
        flash("Unauthorized access.")
        return redirect(url_for("dashboard"))
    # Delete the record
    try:
        db.session.delete(q)
        db.session.commit()
        flash("Query deleted successfully!")
    except Exception as e:
        db.session.rollback()
        logger.error("Error deleting query: %s", e)
        flash("Error deleting query.")
    return redirect(url_for("dashboard"))
