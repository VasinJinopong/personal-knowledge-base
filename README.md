# 🤖 Advanced RAG System

A production-ready Retrieval-Augmented Generation (RAG) system with multi-query decomposition, built with FastAPI, PostgreSQL, ChromaDB, and OpenAI.

## ✨ Key Features

### 🧠 Multi-Query RAG (Advanced)
- **Question Decomposition**: Automatically breaks down complex questions into sub-questions
- **Multi-Source Integration**: Searches and synthesizes information from multiple document chunks
- **Intelligent Answer Synthesis**: Generates comprehensive answers by connecting insights across sources
- **Sub-Question Tracking**: Shows the reasoning path used to answer complex queries

**Example Workflow:**
```
User: "How can I become an excellent backend developer?"

System:
1. Decomposes into sub-questions:
   - "What programming languages for backend?"
   - "What skills are required?"
   - "Best practices for learning?"
   
2. Searches each sub-question independently

3. Synthesizes integrated answer covering:
   - Technical skills (Python, databases, APIs)
   - Learning strategies (projects, documentation)
   - Personal development (discipline, consistency)
```

### 🎯 Basic RAG
- Single-query semantic search
- Direct source retrieval
- Fast response time (~1-2 seconds)

### 🔒 Security
- API Key authentication
- Rate limiting (per endpoint)
- File validation (type, size, content)
- CORS configuration

### 📄 Document Processing
- **Supported formats**: PDF, DOCX, TXT
- **Automatic chunking**: Smart text splitting with overlap
- **Metadata tracking**: Document ID, title, page numbers, timestamps
- **Vector embeddings**: OpenAI text-embedding-3-small

### 💾 Data Storage
- **PostgreSQL**: Document metadata and chat history
- **ChromaDB**: Vector embeddings for semantic search
- **Persistent volumes**: File storage across deployments

## 🏗️ Architecture
```
┌─────────────┐
│   Client    │
│ (Telegram/  │
│  Swagger)   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         FastAPI Backend             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   Multi-Query RAG Engine     │  │
│  │                              │  │
│  │  1. Question Decomposition   │  │
│  │  2. Parallel Search          │  │
│  │  3. Deduplication            │  │
│  │  4. Answer Synthesis         │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │      Basic RAG Engine        │  │
│  │                              │  │
│  │  1. Semantic Search          │  │
│  │  2. Context Retrieval        │  │
│  │  3. Answer Generation        │  │
│  └──────────────────────────────┘  │
└────┬────────────────────┬──────────┘
     │                    │
     ▼                    ▼
┌──────────┐      ┌──────────────┐
│PostgreSQL│      │   ChromaDB   │
│          │      │              │
│Metadata  │      │Vector Store  │
│History   │      │Embeddings    │
└──────────┘      └──────────────┘
```

## 🚀 Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (SQLAlchemy ORM)
- **Vector Store**: ChromaDB
- **AI/ML**: OpenAI GPT-3.5-turbo, text-embedding-3-small
- **Document Processing**: LangChain, PyPDF2, python-docx
- **Authentication**: Custom API Key middleware
- **Rate Limiting**: SlowAPI
- **Deployment**: Docker, Railway

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- OpenAI API Key

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/advanced-rag-system.git
cd advanced-rag-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

Example `.env`:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rag_db

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-3.5-turbo

# Security
API_KEY=your-secret-key-here

# Storage
UPLOAD_DIR=/app/data/uploads
CHROMA_PERSIST_DIR=/app/data/chroma_db
```

5. **Start PostgreSQL**
```bash
docker-compose up -d
```

6. **Run the application**
```bash
python -m src.main
```

7. **Access Swagger UI**
```
http://localhost:8000/docs
```

## 🔧 API Usage

### Authentication
All endpoints (except `/docs`, `/health`) require API key authentication:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/...
```

### Upload Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "description=Important research paper"
```

### Ask Question (Multi-Query RAG)
```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask?use_multi_query=true" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How can I become an excellent backend developer?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "id": "uuid",
  "question": "How can I become an excellent backend developer?",
  "answer": "To become an excellent backend developer, you need...",
  "sub_questions": [
    "What programming languages are used in backend development?",
    "What are the key skills required?",
    "What are best practices for learning?"
  ],
  "sources": [
    {
      "document_id": "uuid",
      "document_title": "Backend Development Guide",
      "content": "...",
      "similarity_score": 0.85
    }
  ],
  "confidence": "high",
  "created_at": "2025-12-21T12:00:00Z"
}
```

### Ask Question (Basic RAG)
```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask?use_multi_query=false" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is FastAPI?",
    "top_k": 3
  }'
```

### List Documents
```bash
curl -X GET "http://localhost:8000/api/v1/documents/documents" \
  -H "X-API-Key: your-api-key"
```

### Get Chat History
```bash
curl -X GET "http://localhost:8000/api/v1/chat/history?limit=10" \
  -H "X-API-Key: your-api-key"
```

## 🐳 Docker Deployment

### Build and Run
```bash
docker build -t advanced-rag-system .
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e OPENAI_API_KEY="sk-..." \
  -e API_KEY="your-key" \
  advanced-rag-system
```

### Docker Compose
```bash
docker-compose up -d
```

## ☁️ Railway Deployment

1. **Connect GitHub repository**
2. **Add PostgreSQL service**
3. **Configure environment variables**
4. **Add Volume for persistent storage**
   - Mount path: `/app/data`
5. **Deploy automatically on git push**

## 📊 Performance

### Multi-Query RAG
- **Response time**: 3-5 seconds
- **Sub-questions**: 2-4 per query
- **Chunks per sub-question**: 2 (configurable)
- **Total context**: ~8 chunks average

### Basic RAG
- **Response time**: 1-2 seconds
- **Chunks retrieved**: 3 (configurable via `top_k`)

## 🧪 Testing

### Run Tests
```bash
pytest tests/
```

### Manual Testing
Use Swagger UI at `/docs` for interactive testing

## 📝 Project Structure
```
advanced-rag-system/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── chat/
│   │   ├── router.py          # Chat endpoints
│   │   ├── service.py         # Multi-query & basic RAG logic
│   │   ├── models.py          # Database models
│   │   └── schemas.py         # Pydantic schemas
│   ├── documents/
│   │   ├── router.py          # Document endpoints
│   │   ├── service.py         # Upload & processing logic
│   │   └── models.py          # Document models
│   ├── vector_store/
│   │   └── client.py          # ChromaDB client
│   └── core/
│       ├── config.py          # Configuration
│       ├── logging.py         # Logging setup
│       └── rate_limit.py      # Rate limiting
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Local development setup
└── README.md                  # This file
```

## 🔬 Advanced RAG Concepts

### Question Decomposition
The system uses LLM to break complex questions into simpler sub-questions:
```python
Original: "How to become excellent at backend development?"

Decomposed:
1. "What are the core technical skills?"
2. "What learning strategies are effective?"
3. "What personal habits support growth?"
```

### Multi-Source Synthesis
Instead of just retrieving similar chunks, the system:
1. Searches each sub-question independently
2. Deduplicates results
3. Synthesizes a coherent answer that connects all sources

### Benefits over Basic RAG
- **Better coverage**: Explores multiple aspects of the question
- **Deeper insights**: Connects information across documents
- **Transparent reasoning**: Shows sub-questions used

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT and embedding models
- LangChain for RAG framework
- FastAPI for the excellent web framework
- ChromaDB for vector storage

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, LangChain, and OpenAI**
