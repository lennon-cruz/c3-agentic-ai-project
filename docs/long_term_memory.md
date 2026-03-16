## Long-Term Memory for AI Agents

This document explains the **concepts**, **architecture**, and **practical patterns** for adding long‑term memory to an AI agent using the abstractions already present in this codebase: `VectorStoreManager`, `VectorStore`, and the classes in `lib/memory.py`.

---

## 1. Mental Model: Short‑Term vs Long‑Term Memory

Modern LLM agents benefit from **two complementary memory systems**:

- **Short‑term memory**
  - Lives only for the **current conversation or run**.
  - Typically implemented as the **message history** you send to the LLM.
  - Gives the model local context (the last N turns) but is limited by token budget and is not persisted.

- **Long‑term memory**
  - Persists **across conversations and sessions**.
  - Stores more durable information, such as:
    - User preferences (“likes racing games on PlayStation”)
    - Important facts discovered earlier
    - Summaries of previous conversations
  - Implemented as a **vector store** so you can **semantically search** past memories.

The pattern is:

1. **Write**: when the agent learns something worth remembering, store a *memory fragment*.
2. **Read**: when a new query arrives, retrieve relevant fragments and feed them into the agent’s reasoning as additional context.

---

## 2. Building Blocks in This Codebase

Long‑term memory here is built on three layers:

1. **Vector store wrapper** (`lib/vector_db.py`)
2. **Memory models & API** (`lib/memory.py`)
3. **Agent integration** (how tools / prompts use the memory)

### 2.1 Vector Store Layer

The vector store wraps ChromaDB and OpenAI embeddings:

```12:197:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/vector_db.py
class VectorStore:
    def __init__(self, chroma_collection: ChromaCollection):
        self._collection = chroma_collection

    def add(self, item: Union[Document, Corpus, List[Document]]):
        ...
        self._collection.add(
            documents=item_dict["contents"],
            ids=item_dict["ids"],
            metadatas=item_dict["metadatas"]
        )

    def query(self, query_texts: str | List[str], n_results: int = 3,
              where: Optional[Dict[str, Any]] = None,
              where_document: Optional[Dict[str, Any]] = None) -> QueryResult:
        return self._collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=['documents', 'distances', 'metadatas']
        )
```

`VectorStoreManager` configures ChromaDB and the OpenAI embedding function:

```12:157:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/vector_db.py
class VectorStoreManager:
    def __init__(self, openai_api_key: str):
        self.chroma_client = chromadb.Client()
        self.embedding_function = self._create_embedding_function(openai_api_key)

    def get_or_create_store(self, store_name: str) -> VectorStore:
        chroma_collection = self.chroma_client.get_or_create_collection(
            name=store_name,
            embedding_function=self.embedding_function
        )
        return VectorStore(chroma_collection)
```

This layer is responsible for:

- Talking to ChromaDB
- Generating embeddings with OpenAI
- Exposing `add` and `query` methods over your documents.

### 2.2 Memory Abstractions

`lib/memory.py` defines how *memories* are represented and persisted on top of the vector store.

#### Short‑Term Memory

```12:16:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
@dataclass
class ShortTermMemory():
    """Manage the history of objects across multiple sessions"""
    sessions: Dict[str, List[Any]] = field(default_factory=lambda: {})
```

Short‑term memory stores arbitrary Python objects per `session_id` and is useful for:

- Tracking message histories
- Keeping intermediate agent states within a run

It does **not** persist across restarts by design.

#### Memory Fragments (Long‑Term)

```12:175:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
@dataclass
class MemoryFragment:
    content: str
    owner: str 
    namespace: str = "default"
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
```

- `content`: the actual text to remember.
- `owner`: which user/session this memory belongs to.
- `namespace`: logical grouping for memories (e.g., `"preferences"`, `"facts"`, `"session:123"`).
- `timestamp`: used for time‑based filtering.

Search results are wrapped in:

```12:183:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
@dataclass
class MemorySearchResult:
    fragments: List[MemoryFragment]
    metadata: Dict
```

`TimestampFilter` lets you constrain searches to recent or historical memories:

```12:197:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
@dataclass
class TimestampFilter:
    greater_than_value: int = None
    lower_than_value: int = None
```

#### LongTermMemory API

```12:211:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
class LongTermMemory:
    """
    Manages persistent memory storage and retrieval using vector embeddings.
    """
    def __init__(self, db: VectorStoreManager):
        self.vector_store = db.create_store("long_term_memory", force=True)
```

**Writing memory:**

```12:242:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
def register(self, memory_fragment: MemoryFragment, metadata: Optional[Dict[str, str]] = None):
    complete_metadata = {
        "owner": memory_fragment.owner,
        "namespace": memory_fragment.namespace,
        "timestamp": memory_fragment.timestamp,
    }
    if metadata:
        complete_metadata.update(metadata)

    self.vector_store.add(
        Document(
            content=memory_fragment.content,
            metadata=complete_metadata,
        )
    )
```

**Searching memory:**

```12:269:/Users/lennondejesuscruz/dev/udacity/c3-agentic-ai-project/lib/memory.py
def search(self, query_text: str, owner: str, limit: int = 3,
           timestamp_filter: Optional[TimestampFilter] = None, 
           namespace: Optional[str] = "default") -> MemorySearchResult:
    where = {
        "$and": [
            {"namespace": {"$eq": namespace}},
            {"owner": {"$eq": owner}},
            # optional timestamp conditions...
        ]
    }

    result: QueryResult = self.vector_store.query(
        query_texts=[query_text],
        n_results=limit,
        where=where
    )
    ...
    return MemorySearchResult(fragments=fragments, metadata=result_metadata)
```

This gives you a clean, high‑level API:

- `register(...)` → write a new memory fragment
- `search(...)` → find memories relevant to a new query

---

## 3. Common Interaction Patterns

Long‑term memory integration usually follows a **read → reason → write** flow.

### 3.1 Reading Memories Before Answering

When a new question arrives:

1. Identify the **owner** (e.g., logged‑in user or a logical session id).
2. Call `LongTermMemory.search(...)`:

   ```python
   memories = long_term_memory.search(
       query_text=user_query,
       owner="user_123",
       limit=3,
       namespace="default",
   )
   ```

3. Convert the top `MemoryFragment` objects into text to inject into the LLM context:

   ```python
   context_snippets = "\n".join(f"- {frag.content}" for frag in memories.fragments)
   ```

4. Add this context as a `SystemMessage` or an early `UserMessage` before the actual user query, so the LLM can condition on prior knowledge about the user or conversation.

### 3.2 Writing New Memories After Answering

Once the agent produces a response, you may want to store:

- New facts about the user (“User prefers strategy games on PC”)
- Derived knowledge that will be useful later (“Mortal Kombat X is not available on PS5”)

A simple pattern:

```python
fragment = MemoryFragment(
    content="User said they love racing games on PlayStation.",
    owner="user_123",
    namespace="preferences",
)
long_term_memory.register(fragment)
```

You can call this directly from your application code or expose it as a **tool** the agent can call (e.g., `store_memory(content, namespace)`).

### 3.3 Time‑Aware Retrieval

Using `TimestampFilter`, you can:

- Focus on **recent** memories to keep the context fresh.
- Or retrieve older memories for “history” views or summaries.

Example:

```python
from lib.memory import TimestampFilter
from datetime import datetime, timedelta

one_week_ago = int((datetime.now() - timedelta(days=7)).timestamp())

recent_only = TimestampFilter(greater_than_value=one_week_ago)

memories = long_term_memory.search(
    query_text="favorite games",
    owner="user_123",
    timestamp_filter=recent_only,
)
```

---

## 4. Integration Strategies with an Agent

There are two main ways to integrate long‑term memory into an agent’s lifecycle:

### 4.1 Tool‑Based Integration

Expose long‑term memory as **tools** the agent can call:

- `retrieve_memory(question: str, limit: int)`:
  - Calls `LongTermMemory.search(...)`
  - Returns a list of memory strings plus metadata
- `store_memory(content: str, namespace: str)`:
  - Wraps a `MemoryFragment` and calls `LongTermMemory.register(...)`

Advantages:

- Very explicit: the agent decides *when* to read or write memory.
- Easy to experiment with prompting (“Call retrieve_memory at the start if prior context might help”).

### 4.2 Automatic Injection in the LLM Step

You can also integrate long‑term memory at a lower level:

- Before each LLM call, automatically:
  1. Extract the current user question from short‑term memory.
  2. Use `LongTermMemory.search(...)` to find relevant fragments.
  3. Prepend a `SystemMessage` summarizing those fragments to the message list.

This pattern gives each LLM invocation **implicit access** to prior knowledge without requiring explicit tool calls in the prompt.

---

## 5. Design Considerations and Best Practices

- **What to store**
  - Prefer **concise, high‑signal summaries** over raw transcripts.
  - Store user preferences, important constraints, and key facts rather than every message.

- **When to store**
  - After user statements that express stable preferences (“I always play on PC”).
  - After the agent resolves a non‑obvious fact that will likely be reused.

- **Namespaces**
  - Use namespaces to keep different memory “types” organized:
    - `"preferences"` for user likes/dislikes
    - `"facts"` for durable world knowledge discovered at runtime
    - `"session:<id>"` for per‑session summaries

- **Privacy & scope**
  - Use the `owner` field to ensure memories do not leak between users.
  - Consider how long to retain memories and whether to support deletion.

- **Cost & performance**
  - Embedding and searching cost tokens and compute; don’t store everything.
  - Use metadata filters (`where`) and `TimestampFilter` to narrow searches.

---

## 6. Summary

The long‑term memory layer in this codebase consists of:

- A **vector store** abstraction (`VectorStore`, `VectorStoreManager`) backed by ChromaDB and OpenAI embeddings.
- A **memory model** (`MemoryFragment`, `MemorySearchResult`, `TimestampFilter`) that describes what is stored and how it is retrieved.
- A **high‑level API** (`LongTermMemory`) to:
  - `register(...)` new memories
  - `search(...)` for relevant memories given a query, owner, and optional time/namespace filters.

By combining these with either tool‑based or automatic integration patterns, you can build agents that **remember and reuse** important information across interactions, leading to more personalized, coherent, and capable behaviors over time.

