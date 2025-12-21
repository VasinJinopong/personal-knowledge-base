from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import json
import time

from src.chat.models import ChatHistory
from src.chat.schemas import SourceChunk, AnswerResponse
from src.vector_store.client import vector_store
from src.core.config import get_settings
from src.core.logging import logger, log_performance

settings = get_settings()

class ChatService:
    """Service for chat/Q&A operations"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0,
            openai_api_key =settings.OPENAI_API_KEY
        )
        
        self.qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """You are a helpful AI assisstant that answer question based on provided context
                 
                 Instructions:
                 1. Answer using ONLY the information from the provided context
                 2. If the context doesn't contain enough information, say "I don't have enough information to answer this question based on the provided documents
                 3. Be concise and direct
                 4. If you quote from context, indicate with source
                 5. If multiple sources provide information, synthesize them coherently
                 
                 Context:
                 {context}
                 """),
                
                ("human", "{question}")
            ]
        )
        
    def search_similar(self, query:str, k:int=3, document_ids : Optional[List[str]]= None) -> List[tuple]:
        """Search for similar chunks"""
        start_time = time.time()
        
        filter_dict = None
        if document_ids:
            filter_dict = {"document_id": {"$in": document_ids}}
        
        results = vector_store.search_similar(query=query, k=k, filter_dict=filter_dict)
        
        log_performance("search_similarity", time.time() - start_time, k=k)
        return results  
    
    def generate_answer(self, question:str, context: str) -> str:
        """Generate answer using LLM"""
        start_time = time.time()
        
        messages = self.qa_prompt.format_messages(context=context, question= question)
        response = self.llm.invoke(messages)
        answer = response.content
        
        log_performance("generate_answer", time.time() - start_time)
        return answer
    
    
    def assess_confidence(self,answer:str , sources_count: int) -> str:
        """Assess confidence level"""
        if "don't have enough information" in answer.lower():
            return "low"
        elif sources_count >= 3:
            return "high"
        elif sources_count >= 2:
            return "medium"
        
        else:
            return "low"
        
        
    def save_chat(self, question:str, answer: str, confidence: str, top_k: int, document_ids : Optional[List[str]], db:Session) -> ChatHistory:
        """Save chat to history"""
        chat = ChatHistory(
            question= question,
            answer = answer,
            confidence = confidence,
            top_k= top_k,
            document_ids=json.dumps(document_ids) if document_ids else None
            
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        logger.info(f"Chat saved: {chat.id}")
        return chat
    
    def ask_question(self, question:str, document_ids: Optional[List[str]], top_k:int, db:Session )-> AnswerResponse:
        """Main RAG workflow"""
        
        start_time = time.time()
        
        search_results = self.search_similar(query=question, k=top_k, document_ids=document_ids)
        
        sources = []
        context_parts = []
        
        for doc,score in search_results:
            source = SourceChunk(
                document_id = doc.metadata.get("document_id", ""),
                document_title=doc.metadata.get("title","Unknown"),
                chunk_index= doc.metadata.get("chunk_index"),
                content= doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                similarity_score=float(score)
            )
            sources.append(source)
            context_parts.append(f"[Source: {doc.metadata.get('title','Unknown')}]\n{doc.page_content}")
        
        context = "\n\n---\n\n".join(context_parts)    
            
        if not context_parts:
            answer = "I couldn't find any. relevant information in the documents to answer your question."
            confidence = "low"
            
        else:
            answer = self.generate_answer(question, context)
            confidence = self.assess_confidence(answer, len(sources))
            
        chat = self.save_chat(question,answer, confidence, top_k, document_ids, db)
        
        log_performance("ask_question", time.time() - start_time)
        
        return AnswerResponse(
            id = chat.id,
            question = question,
            answer = answer,
            sources= sources,
            confidence = confidence,
            created_at = chat.created_at
        )
        
    def get_chat_history(self, db:Session, limit: int = 50) -> List[ChatHistory]:
        """Get recent chat history"""
        return db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).limit(limit).all()
    
    def decompose_question(self,question: str) -> List[str]:
        """แยกคำถามเป็น sub-questions"""
        
        llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature= 0,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        prompt = ChatPromptTemplate.from_template("""
            Given a complex question, break it down into simpler sub-questions that can be answered independently.
            Each sub-question should focus on a specific aspect of the original question.

            Original Question: {question}

            Generate 2-4 sub-questions that together will help answer the original question.
            Return ONLY the sub-questions, one per line, without numbering or explanations.

            Sub-questions:""")
        
        chain = prompt | llm
        response = chain.invoke({"question" :question})
        
        # Parse sub-questions
        sub_questions = [
            q.strip()
            for q in response.content.strip().split('\n')
            if q.strip() and not q.strip().startswith('#')
        ]
        
        return sub_questions[:4] # Max 4 sub-question
    
    
    def search_sub_question(self, sub_question: str, top_k:int = 2) -> List[Dict]:
        """Search for a single sub-question"""
        
        try:
            # Use existing vector_store
            results = vector_store.search_similar(query=sub_question, k=top_k)
            
            # Format results
            chunks =[]
            for doc,score in results:
                
                # Threshold filter
                if score > 1.4:
                    logger.info(f"Skipping irrelevant chunk (score: {score:.2f})")
                    continue
                
                
                chunks.append({
                    "content": doc.page_content,
                    'metadata' : doc.metadata,
                    'score' : float(score)
                })
                
            return chunks
        
        except Exception as e:
            logger.error(f"Error searching sub-question: {e}")
            return []
        
    def multi_query_rag(
        self,
        question: str,
        top_k_per_query:int = 2
    ) -> Dict:
        """Multi-query RAG with question decomposition"""
        
        logger.info(f"Multi-query RAG for: {question}")
        
        
        # 1. Decompose question
        sub_questions = self.decompose_question(question)
        logger.info(f"Sub-questions: {sub_questions}")
        
        
        # 2. Search each sub-question
        all_chunks = []
        sub_results = {}
        
        for sub_q in sub_questions:
            chunks = self.search_sub_question(sub_q, top_k_per_query)
            all_chunks.extend(chunks)
            sub_results[sub_q] = chunks
            
        # 3. Remove duplicates (by content)
        seen_content = set()
        unique_chunks =[]    
        for chunk in all_chunks:
            content = chunk['content']
            if content not in seen_content:
                seen_content.add(content)
                unique_chunks.append(chunk)
            
        logger.info(f"Found {len(unique_chunks)} unique chunks from {len(sub_questions)} sub-questions")
        
        # 4. Synthesize answer
        if not unique_chunks:
            return {
                "answer" : "Not found information in any documents",
                "sources": [],
                "confidence" : 'none',
                "sub_questions" : sub_questions
            }
            
        # Create context
        context = "\n\n---\n\n".join([
            f"Source {i+1}:\n{chunk['content']}"
            for i, chunk in enumerate(unique_chunks)
        ])
        
        # Generate answer
        llm = ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.3,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        
        prompt = ChatPromptTemplate.from_template("""
                You are a helpful assistant that synthesizes information from multiple sources.

                Original Question: {question}

                Sub-questions analyzed:
                {sub_questions}

                Context from documents:
                {context}

                Instructions:
                1. Answer the original question by integrating information from ALL relevant sources
                2. Show connections between different pieces of information
                3. If sources complement each other, explain how
                4. Be comprehensive but concise
                5. Answer in Thai if the question is in Thai

                Answer:""")
        chain = prompt | llm
        response = chain.invoke({
            "question" : question,
            "sub_questions": "\n".join([f"- {sq}" for sq in sub_questions]),
            "context" : context
        })
        
        # Determine confidence
        confidence = self._calculate_confidence(len(unique_chunks), len(sub_questions))
        
        return {
            'answer' : response.content,
            'sources' : unique_chunks,
            'confidence': confidence,
            'sub_questions' : sub_questions
        }
        
    def _calculate_confidence(self,chunks_found:int, sub_questions:int) -> str:
        """Calculate confidence based on coverage"""
        
        coverage = chunks_found / (sub_questions*2) # Assuming 2 chunks per sub-questions
        
        if coverage >= 0.8:
            return 'high'
        elif coverage >= 0.5:
            return "medium"
        else:
            return "low"
                                                                
                        
        
    
    
chat_service = ChatService()