import chromadb
from sentence_transformers import SentenceTransformer
from app.features.ai import get_ai_response

# Initialize the ChromaDB client
client = chromadb.PersistentClient(path="file_vectors")
collection = client.get_or_create_collection(name="uploaded_files")

# Lazy load the embedding model
embedding_model = None

def get_embedding_model():
    """
    Loads the SentenceTransformer model if it hasn't been loaded yet.
    """
    global embedding_model
    if embedding_model is None:
        print("Loading embedding model...")
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded.")
    return embedding_model

def store_uploaded_file(file_path):
    """
    Reads a file, splits it into chunks, creates embeddings, and stores them.
    """
    try:
        model = get_embedding_model()
        # For a simple .txt file:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # For other files like .pdf or .docx, you'll need libraries
        # like PyPDF2 or python-docx to extract the text.

        # 1. Split the text into chunks
        chunks = text.split('\n\n') # A simple way to chunk by paragraphs

        # 2. Create embeddings for each chunk
        embeddings = model.encode(chunks).tolist()

        # 3. Store the chunks and embeddings in the database
        # We use the file_path and chunk index to create a unique ID
        for i, chunk in enumerate(chunks):
            collection.add(
                embeddings=[embeddings[i]],
                documents=[chunk],
                metadatas=[{"source": file_path}],
                ids=[f"{file_path}_{i}"]
            )
        
        return f"Successfully analyzed and stored {file_path}"
    except Exception as e:
        return f"Error analyzing file: {e}"

def query_uploaded_files(query):
    """
    Queries the vector database to find relevant chunks and get an AI response.
    """
    try:
        model = get_embedding_model()
        # 1. Create an embedding for the query
        query_embedding = model.encode(query).tolist()

        # 2. Find the 3 most relevant document chunks for the query
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        retrieved_chunks = results['documents'][0]
        
        if not retrieved_chunks:
            return "I couldn't find any relevant information in the uploaded files."

        # 3. Create a context for the AI
        context = "\n\n---\n\n".join(retrieved_chunks)
        
        # 4. Create a prompt for the AI
        prompt = f"""Based on the following information from the uploaded documents:

{context}

Please answer the following question: {query}"""

        final_answer = get_ai_response(prompt)
        
        return final_answer

    except Exception as e:
        return f"Error querying files: {e}"