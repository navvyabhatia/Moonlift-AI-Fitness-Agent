# AI Gym Agent - Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AI Gym Agent System                                   │
│                           (Streamlit Web App)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Frontend Layer                                     │
│                           (Streamlit UI Components)                            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Business Logic                                     │
│                            (app.py - Main Controller)                          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   LLM Service   │ │  Vector Store   │ │  Data Models    │
│   (src/llm.py)  │ │(src/vector_store│ │ (src/models.py) │
│                 │ │      .py)       │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                    │                   │                   │
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Ollama API    │ │   ChromaDB      │ │  Pydantic       │
│  (Local LLM)    │ │  (Vector Store)  │ │   Validation    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Detailed Component Architecture

### 1. Frontend Layer (Streamlit UI)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              STREAMLIT UI LAYER                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Login/Signup  │ │   Quick Inputs   │ │  Chat Interface │
│                 │ │                 │ │                 │
│ • Nickname      │ │ • Feeling       │ │ • Messages      │
│ • New User      │ │ • Cycle Phase   │ │ • History       │
│ • Returning     │ │ • Duration      │ │ • Feedback      │
│                 │ │ • Constraints   │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 2. Business Logic Layer (app.py)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MAIN CONTROLLER                                    │
│                                (app.py)                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Session Mgmt    │ │ User Input      │ │ Response        │
│                 │ │ Processing      │ │ Generation      │
│ • Login State   │ │ • Validation    │ │ • LLM Calls     │
│ • Preferences   │ │ • Context       │ │ • Storage       │
│ • History       │ │ • Constraints   │ │ • Display       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 3. LLM Service Layer (src/llm.py)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              LLM SERVICE                                       │
│                              (src/llm.py)                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ System Prompt   │ │ User Prompt     │ │ Response        │
│                 │ │ Builder         │ │ Parser          │
│ • Instructions  │ │ • Context       │ │ • Validation    │
│ • Constraints   │ │ • History       │ │ • Structuring   │
│ • Examples      │ │ • Preferences   │ │ • Error Handle  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              OLLAMA API                                        │
│                         (Local LLM Service)                                   │
│                                                                                 │
│ • Model: llama3.1:8b                                                         │
│ • Endpoint: http://localhost:11434                                            │
│ • Function: Generate workout recommendations                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Vector Store Layer (src/vector_store.py)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VECTOR STORE                                       │
│                          (src/vector_store.py)                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ User Context    │ │ Workout History │ │ Conversation    │
│ Collection      │ │ Collection      │ │ Collection      │
│                 │ │                 │ │                 │
│ • Preferences   │ │ • Plans         │ │ • Q&A           │
│ • User ID       │ │ • Exercises     │ │ • Feedback      │
│ • Onboarding    │ │ • Dates         │ │ • Timestamps    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CHROMADB                                           │
│                         (Vector Database)                                      │
│                                                                                 │
│ • Collections: 3 (users, workouts, conversations)                             │
│ • Embeddings: Text similarity search                                          │
│ • Storage: Local disk                                                          │
│ • Function: Semantic search and retrieval                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5. Data Models Layer (src/models.py)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA MODELS                                        │
│                            (src/models.py)                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Daily Context  │ │ Workout History │ │ Conversation    │
│                 │ │                 │ │                 │
│ • Time          │ │ • Date          │ │ • Role          │
│ • Energy        │ │ • Workout Plan  │ │ • Content       │
│ • Soreness      │ │ • Exercises     │ │ • Timestamp     │
│ • Cycle Phase   │ │ • Duration      │ │ • Workout Gen   │
│ • Constraints   │ │ • Feeling       │ │                 │
│ • Goal          │ │ • Cycle Phase   │ │                 │
│ • User ID       │ │ • User Feeling  │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                          │
└─────────────────────────────────────────────────────────────────────────────────┘

1. USER INPUT FLOW:
   User → Streamlit UI → Validation → Context Building → LLM Prompt

2. LLM PROCESSING FLOW:
   Context → Prompt Builder → Ollama API → Response Parser → Structured Output

3. STORAGE FLOW:
   Response → Vector Store → ChromaDB → Semantic Indexing

4. RETRIEVAL FLOW:
   User Query → Vector Search → Relevant History → Context Enrichment

5. DISPLAY FLOW:
   Structured Response → Streamlit Components → User Interface
```

## Integration Points

### External Services:
```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Streamlit     │ ──────────────► │     Ollama      │
│     App         │                │   (Local LLM)   │
└─────────────────┘                └─────────────────┘

┌─────────────────┐    Python SDK  ┌─────────────────┐
│   Vector Store  │ ──────────────► │    ChromaDB     │
│     Service     │                │  (Vector DB)    │
└─────────────────┘                └─────────────────┘
```

### File Storage:
```
┌─────────────────┐    File I/O    ┌─────────────────┐
│   Session Data  │ ──────────────► │  Local Files    │
│                 │                │                 │
│ • Preferences   │                │ • JSON files    │
│ • History       │                │ • User data     │
│ • Cache         │                │ • Configs       │
└─────────────────┘                └─────────────────┘
```

## Technology Stack

### Frontend:
- **Streamlit**: Web framework for Python
- **Components**: Chat interface, forms, buttons, columns

### Backend:
- **Python**: Core programming language
- **Pydantic**: Data validation and serialization
- **ChromaDB**: Vector database for semantic search

### AI/ML:
- **Ollama**: Local LLM service
- **llama3.1:8b**: Language model for recommendations
- **Embeddings**: Text similarity and search

### Data Storage:
- **ChromaDB Collections**: Users, Workouts, Conversations
- **JSON Files**: Session state, preferences, history
- **Local File System**: Persistent storage

## Security & Privacy

### Data Protection:
- **Local Storage**: All data stored locally
- **No Cloud Dependencies**: User data never leaves local machine
- **Session Isolation**: User-specific data separation

### Authentication:
- **Nickname-based**: Simple identifier system
- **Session Management**: Streamlit session state
- **No Passwords**: Simplified user experience

## Scalability Considerations

### Current Limitations:
- **Single User**: Designed for individual use
- **Local Storage**: Limited by disk space
- **Memory Usage**: Session state limitations

### Future Enhancements:
- **Multi-user Support**: User management system
- **Cloud Storage**: Remote database options
- **API Layer**: RESTful service architecture
- **Microservices**: Component separation

## Monitoring & Debugging

### Logging:
- **Console Output**: Error messages and status
- **Session Tracking**: User interaction logging
- **Performance Metrics**: Response time monitoring

### Error Handling:
- **Graceful Degradation**: Fallback behaviors
- **User Feedback**: Clear error messages
- **Recovery Mechanisms**: Automatic retry logic

This architecture provides a solid foundation for the AI Gym Agent with clear separation of concerns, modular design, and room for future enhancements.
