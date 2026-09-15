import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config import (
    VECTOR_DB_DIR,
    EMBEDDING_MODEL,
    LLM_MODEL,
    FALLBACK_LLM_MODEL,
    TOP_K,
)

SYSTEM_PROMPT = """You are the official AI Knowledge Assistant for Tech Industries Pvt Ltd.

Your responsibility is to assist website visitors and employees by answering their questions accurately, politely, and in a clean, structured format (using clear headings, bold text, and bullet points) using ONLY the provided context below.

Domain Capabilities:
- Company Information & Products: Answer inquiries regarding induction motors (HT/LT), pumps (submersible, monoblock, centrifugal), engineering services, manufacturing facilities, quality certifications (BIS, ISO), and contact details.
- Corporate Policies & Entitlements: Answer questions regarding attendance, office timings, leaves (Privilege, Casual, Maternity, Bereavement), and travel reimbursement policies.

Rules:
1. Grounding: Do not use outside knowledge or invent facts. Answer strictly using the information in the provided context.
2. Section & Clause Continuity: In policy documents, numbered clauses (e.g. 4.1 through 4.9) belong to that section (e.g. Section 4: Privilege Leave). Resolve pronouns like 'It' or 'These leaves' accordingly.
3. Missing Info: If an answer cannot be found in the provided context, state:
   "I could not find this information in the company's website data or policy documents." If the query is a sales, product, or custom support inquiry, encourage them to contact info@techindustries.co.in or call +91 79 2584 0061.
4. Accuracy: Preserve all numbers, specifications, dates, allowances, and exceptions exactly as stated.
5. Citations: Cite the source document, page number, or website URL whenever available.
6. Formatting: Always structure answers with clear markdown headings (###), bold key terms, and bulleted lists.
7. Tone: Professional, welcoming, and helpful.

Context:
{context}

Recent Conversation History:
{chat_history}"""

REPHRASE_SYSTEM_PROMPT = """Given a conversation history and the latest user question which might reference context in the history, formulate a standalone search query that includes any necessary context (e.g. replacing pronouns like 'it', 'they', 'those' with the actual subject). Do NOT answer the question. Return ONLY the reformulated standalone question."""

# Words indicating a question depends on previous conversational context
CONTEXT_DEPENDENT_WORDS = {
    "it", "its", "they", "them", "their", "this", "that", "these", "those",
    "same", "also", "what about", "how about", "and", "why", "who", "when"
}


class RAGService:
    def __init__(
        self,
        vector_db_dir: Optional[Path] = None,
        embedding_model_name: str = EMBEDDING_MODEL,
        llm_model_name: str = LLM_MODEL,
        fallback_model_name: str = FALLBACK_LLM_MODEL,
        top_k: int = TOP_K,
    ):
        self.vector_db_dir = vector_db_dir or VECTOR_DB_DIR
        self.embedding_model_name = embedding_model_name
        self.llm_model_name = llm_model_name
        self.fallback_model_name = fallback_model_name
        self.top_k = top_k

        if not (self.vector_db_dir / "index.faiss").exists():
            print(f"[*] FAISS index not found at '{self.vector_db_dir}'. Automatically building index from documents and website...")
            try:
                from src.ingest import build_vector_store
                build_vector_store()
            except Exception as e:
                raise FileNotFoundError(
                    f"FAISS index not found at '{self.vector_db_dir}' and automatic build failed: {e}. "
                    "Please run `python -m src.ingest` first to create the index."
                )

        print(f"[*] Loading embeddings ({self.embedding_model_name})...")
        if "gemini" in self.embedding_model_name.lower() or self.embedding_model_name.startswith("models/"):
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            from src.config import gemini_key, google_key
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=self.embedding_model_name,
                google_api_key=gemini_key or google_key,
            )
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)

        print(f"[*] Loading persistent FAISS index from '{self.vector_db_dir}'...")
        self.vector_db = FAISS.load_local(
            str(self.vector_db_dir),
            self.embeddings,
            allow_dangerous_deserialization=True,
        )

        print(f"[*] Initializing primary LLM ({self.llm_model_name}) with fallback ({self.fallback_model_name})...")
        self.primary_llm = ChatGoogleGenerativeAI(
            model=self.llm_model_name,
            # temperature=0.1,
            max_retries=2,
        )
        self.fallback_llm = ChatGoogleGenerativeAI(
            model=self.fallback_model_name,
            temperature=0.1,
            max_retries=2,
        )
        # Automatic fallback on 429 rate limit or errors
        self.llm = self.primary_llm.with_fallbacks([self.fallback_llm])

        # Primary QA prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

        # Follow-up query contextualizer prompt
        self.rephrase_prompt = ChatPromptTemplate.from_messages([
            ("system", REPHRASE_SYSTEM_PROMPT),
            ("human", "Conversation History:\n{chat_history}\n\nLatest Question: {question}"),
        ])
        self.rephrase_chain = self.rephrase_prompt | self.llm | StrOutputParser()

        print("[+] RAG service ready with quota-resilient model routing.")

    def _needs_rephrasing(self, question: str, chat_history: Optional[str]) -> bool:
        """
        Check if the question needs an extra LLM call to rephrase, saving API quota.
        """
        if not chat_history or chat_history.strip() == "No previous conversation.":
            return False

        # If question is very short or contains pronouns referring to previous context
        tokens = set(re.findall(r"\b\w+\b", question.lower()))
        if len(tokens) <= 4 or bool(tokens & CONTEXT_DEPENDENT_WORDS):
            return True
        return False

    def query(
        self,
        question: str,
        chat_history: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query the RAG pipeline with quota-efficient query rewriting and source citations.
        """
        search_query = question

        # Only invoke rephrase chain if question actually depends on previous turns
        if self._needs_rephrasing(question, chat_history):
            try:
                reformulated = self.rephrase_chain.invoke({
                    "chat_history": chat_history,
                    "question": question,
                }).strip()
                if reformulated:
                    search_query = reformulated
            except Exception as e:
                print(f"[Warning] Rephrase skipped or failed: {e}")
                search_query = question

        k = top_k or self.top_k
        retrieved_docs = self.vector_db.similarity_search(search_query, k=k)

        # Build formatted context block
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            source = doc.metadata.get("source", "Unknown Source")
            page = doc.metadata.get("page_label", doc.metadata.get("page", "N/A"))
            context_parts.append(
                f"--- Reference [{i}] (Source: {source} | Page: {page}) ---\n{doc.page_content}"
            )

        context_str = "\n\n".join(context_parts)

        # Generate response using primary or fallback Gemini LLM
        try:
            answer = self.chain.invoke({
                "context": context_str,
                "chat_history": chat_history or "No previous conversation.",
                "question": question,
            })
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                answer = (
                    "⚠️ **API Rate Limit Notice:** The free-tier request limit was briefly reached. "
                    "Please wait ~20–30 seconds and ask your question again, or enable pay-as-you-go billing "
                    "in Google AI Studio for unlimited requests."
                )
            else:
                answer = f"An unexpected error occurred: {err_str}"

        # Structured sources for citations
        sources: List[Dict[str, Any]] = [
            {
                "source": doc.metadata.get("source", "Unknown Source"),
                "page": doc.metadata.get("page_label", doc.metadata.get("page", "N/A")),
                "snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            }
            for doc in retrieved_docs
        ]

        return {
            "question": question,
            "search_query": search_query,
            "answer": answer,
            "sources": sources,
        }


# Global singleton instance cache
_rag_instance: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Retrieve or initialize the singleton RAGService instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGService()
    return _rag_instance
