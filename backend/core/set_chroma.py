import chromadb

# ✅ ChromaDB 클라이언트 연결
chroma_client = chromadb.HttpClient(host="localhost", port=8000)

collection = chroma_client.get_or_create_collection("documents")

#chroma_client.delete_collection("documents")
#collection = chroma_client.get_or_create_collection(name="data_files")
print(f"✅ ChromaDB 데이터 개수: {collection.count()}")

