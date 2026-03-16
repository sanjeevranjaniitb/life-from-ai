import os
import logging
from langchain_community.document_loaders import PDFPlumberLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

logger = logging.getLogger("RAGEngine")

class RAGEngine:
    def __init__(self):
        self.vector_store = None
        self.llm = None
        self.embeddings = None
        self._initialize_models()

    def _initialize_models(self):
        logger.info("Loading Embedding Model...")
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        logger.info("Loading Local LLM (LaMini-T5-738M)...")
        model_id = "MBZUAI/LaMini-T5-738M"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id, torch_dtype=torch.float32)
        
        pipe = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=512,
            temperature=0.3,
            top_p=0.95,
            repetition_penalty=1.15
        )
        self.llm = HuggingFacePipeline(pipeline=pipe)
        logger.info("Models Loaded Successfully.")

    def ingest_pdf(self, pdf_path):
        logger.info(f"Ingesting PDF: {pdf_path}")
        try:
            loader = PDFPlumberLoader(pdf_path)
            documents = loader.load()
        except Exception as e:
            logger.warning(f"PDFPlumber failed: {e}. Trying PyPDFLoader.")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

        if not documents:
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)
        
        if not texts:
            return

        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        logger.info("Vector Store Created.")

    def answer_question(self, query, user_age=25):
        """Generates an answer tuned to the user's age."""
        if not self.vector_store:
            return "Please upload a PDF first."
            
        # Tune prompt style based on age
        age = int(user_age)
        if age < 12:
            style = "Explain it simply like I am a 10-year-old child. Use easy words and short sentences."
        elif age < 18:
            style = "Explain it clearly for a teenager. Be engaging but not too complex."
        else:
            style = "Explain it professionally and in detail for an adult."

        docs = self.vector_store.similarity_search(query, k=5)
        context = "\n".join([doc.page_content for doc in docs])
        
        prompt = f"""
        You are a helpful AI assistant. 
        User Context: The user is {age} years old. {style}
        
        Use the following context to answer the question.
        If you don't know the answer from the context, say that you cannot find the information.

        Context:
        {context}

        Question: {query}

        Answer:
        """
        response = self.llm.invoke(prompt)
        
        return response.strip()
