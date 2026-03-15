# ChromaDB Explanation for RAG (SQL Perspective)

## 1. Mental Model: SQL vs Vector Databases

If you come from SQL databases, the biggest conceptual shift is how
queries work.

### SQL databases

Queries rely on **exact matches or structured filters**.

Example:

``` sql
SELECT *
FROM games
WHERE genre = 'Racing';
```

The database stores structured values and retrieves rows matching exact
conditions.

### ChromaDB (Vector Database)

Vector databases retrieve information based on **semantic similarity**.

Example query:

    "games about cars"

The system converts that sentence into a **vector embedding** and finds
documents whose vectors are closest in meaning.

------------------------------------------------------------------------

## 2. What ChromaDB Stores

A Chroma collection typically stores four elements:

  id   document    metadata          embedding
  ---- ----------- ----------------- -----------
  1    text/json   structured info   vector
  2    text/json   structured info   vector

Example JSON document:

``` json
{
  "Name": "Gran Turismo",
  "Platform": "PlayStation 1",
  "Genre": "Racing",
  "Publisher": "Sony Computer Entertainment",
  "Description": "A realistic racing simulator featuring a wide array of cars and tracks.",
  "YearOfRelease": 1997
}
```

Possible stored structure:

  id       document    metadata          embedding
  -------- ----------- ----------------- ----------------------
  game_1   JSON text   {platform: PS1}   \[0.19, -0.77, ...\]

Embeddings are generated from the text using an embedding model.

Pipeline:

    document
    ↓
    embedding model
    ↓
    vector
    ↓
    stored in vector index

------------------------------------------------------------------------

## 3. How Embeddings Work

Embeddings convert text into a numeric representation.

Example:

    "racing game with cars"

becomes something like:

    [0.12, -0.53, 0.77, ...]

Vectors representing similar concepts appear close in vector space.

Example similarity:

  Text            Similarity
  --------------- ------------
  racing game     very close
  car simulator   close
  football game   far

------------------------------------------------------------------------

## 4. How Chroma Retrieves Data

Query example:

``` python
collection.query(
    query_texts=["games about cars"],
    n_results=3
)
```

Internally:

    query text
    ↓
    embedding model
    ↓
    query vector
    ↓
    similarity search
    ↓
    nearest vectors

Typical similarity metrics:

-   cosine similarity
-   approximate nearest neighbor search

------------------------------------------------------------------------

## 5. SQL vs Vector Retrieval

### SQL

    WHERE genre = "Racing"

### Vector database

    Find documents semantically similar to:
    "car racing game"

SQL returns exact matches. Vector databases return **meaningfully
related results**.

Example:

Query:

    "car simulator"

SQL may return nothing.

Vector search might return:

    Gran Turismo

because the meaning matches.

------------------------------------------------------------------------

## 6. Why Vector Databases Are Useful for AI Agents

LLMs cannot read an entire dataset every time a user asks a question.

Instead the workflow becomes:

    User question
    ↓
    embedding
    ↓
    vector search
    ↓
    retrieve relevant docs
    ↓
    send context to LLM
    ↓
    generate answer

This architecture is called **Retrieval Augmented Generation (RAG)**.

Example:

User question:

    "What racing games exist on PS1?"

Pipeline:

    Agent
    ↓
    vector search
    ↓
    retrieve Gran Turismo document
    ↓
    send context to LLM
    ↓
    generate answer

------------------------------------------------------------------------

## 7. Why This Is Good for Agentic AI

Agents need **semantic memory**.

Example query:

    "What game lets you drive real cars?"

Should retrieve:

    Gran Turismo

Even if the phrasing is different.

Vector databases also handle **unstructured knowledge** well:

-   PDFs
-   JSON files
-   documentation
-   chat history
-   code

Traditional SQL databases are not designed for semantic similarity
across unstructured text.

------------------------------------------------------------------------

## 8. Metadata Filtering (SQL‑Like Queries)

ChromaDB also supports structured filtering.

Example:

``` python
collection.query(
    query_texts=["racing games"],
    where={"Platform": "PlayStation 1"}
)
```

Conceptually this behaves like:

    WHERE platform = 'PS1'
    AND semantic similarity

This combines:

    semantic search + structured filters

------------------------------------------------------------------------

## 9. Internal Structure of a Chroma Collection

Internally a collection contains:

    collection
     ├── embeddings
     ├── documents
     ├── metadata
     └── ids

Behind the scenes Chroma uses:

-   DuckDB
-   Parquet
-   HNSW vector indexes

These structures allow fast similarity search over high‑dimensional
vectors.

------------------------------------------------------------------------

## 10. Simple RAG Architecture

    documents
       ↓
    embedding model
       ↓
    vector embeddings
       ↓
    vector index (Chroma)
       ↓
    similarity search
       ↓
    retrieved documents
       ↓
    LLM context

------------------------------------------------------------------------

## 11. SQL vs Chroma Concept Mapping

  SQL Concept   Chroma Equivalent
  ------------- -------------------
  database      client
  table         collection
  row           document
  columns       metadata
  index         vector index
  query         similarity search

------------------------------------------------------------------------

## 12. Key Takeaway

SQL answers:

    What matches exactly?

Vector databases answer:

    What is semantically similar?

This difference is what enables **RAG systems and agent memory**.
