# Policy Chatbot — University Policy Assistant

## Project Overview

This project is an AI-powered chatbot designed to help users query and understand university policies using natural language. The system allows users to ask questions about institutional policies (such as alcohol use, leave policies, conduct guidelines, etc.) and receive accurate, context-aware responses sourced directly from official policy documents.

The application is built around a **Retrieval-Augmented Generation (RAG)** architecture, combining semantic search with a large language model to ensure responses are both relevant and grounded in authoritative policy content. The chatbot also supports **conversation history**, enabling more natural, multi-turn interactions.

The system is delivered as a full-stack application, consisting of:
- a **React-based frontend** for user interaction
- a **FastAPI backend** that orchestrates retrieval, generation, and memory
- a **vector database** storing policy document embeddings
- a **persistent database** for chat history and session tracking

---

## High-Level Architecture

User (Frontend)
↓
React Chat Interface
↓
FastAPI Backend
↓
LangChain Agent
↓
(Two-Step) Retrieval → ChromaDB (Policy Embeddings)
↓
LLM (Answer Generation)
↓
Response + Sources
↓
Frontend Display


Conversation state and session history are stored separately to enable continuity across interactions.

---

## Project Workflow

### 1. User Interaction
Users interact with the system through a web-based chat interface. They can start new conversations, continue existing ones, and ask policy-related questions in plain English.

### 2. Request Handling
User messages are sent from the frontend to the FastAPI backend, where they are processed by a LangChain-powered agent.

### 3. Retrieval-Augmented Generation (RAG)

The chatbot uses a **two-step retrieval strategy**:

1. **Coarse Retrieval (File / Section Filtering)**  
   The system first identifies the most relevant policy documents or high-level sections based on semantic similarity.

2. **Fine-Grained Retrieval (Chunk-Level Search)**  
   Within the filtered documents, the system performs a second semantic search to locate the most relevant text chunks that directly address the user’s question.

All document chunks are stored as embeddings in **ChromaDB**, enabling fast and meaningful similarity search.

### 4. Answer Generation
The retrieved context is passed to a language model, which generates a response grounded strictly in the retrieved policy content. The final answer may also include references to the source documents for transparency.

### 5. Conversation Memory
Chat history and session metadata are stored in **Supabase**, allowing:
- multi-turn conversations
- session persistence
- context-aware follow-up questions

### 6. Response Delivery
The generated response is sent back to the frontend and rendered in a conversational, chat-style interface.

---

## Tech Stack

### Backend
- **Python**
- **FastAPI** – API layer and request orchestration
- **LangChain** – Agent logic, tool routing, and RAG pipeline
- **ChromaDB** – Vector database for semantic document storage
- **Supabase (PostgreSQL)** – Persistent chat history and session storage
- **AWS Bedrock / LLM Provider** – Language model inference

### Frontend
- **React**
- **Vite**
- **Tailwind CSS** – UI styling and layout
- **Custom Chat UI** – ChatGPT-inspired conversational interface

### Data & Embeddings
- Cleaned university policy documents
- Semantic chunking + embeddings
- Vector similarity search

---

## Key Features

- Natural language querying of university policies
- Two-step semantic retrieval for improved accuracy
- Source-grounded responses (RAG)
- Persistent conversation memory
- Modular, extensible agent + tool design
- Full-stack architecture suitable for real-world deployment

---

## Future Improvements

- **Improved UI/UX**
  - Chat history sidebar
  - Message streaming
  - Typing indicators and loading states

- **Enhanced Retrieval**
  - Metadata-based filtering (policy type, year, department)
  - Hybrid search (keyword + semantic)

- **User Accounts**
  - Authentication
  - Saved conversations per user

- **Evaluation & Monitoring**
  - Response quality metrics
  - Retrieval accuracy analysis
  - Logging and tracing (e.g., LangSmith)

- **Expanded Document Coverage**
  - Support for additional universities or departments
  - Automatic document ingestion pipelines

---

## Why This Project Matters

This project demonstrates real-world application of:
- Retrieval-Augmented Generation (RAG)
- Vector databases and semantic search
- AI agents and tool orchestration
- Full-stack system design

It is designed not just as a demo, but as a **scalable foundation** for enterprise or institutional knowledge assistants.
