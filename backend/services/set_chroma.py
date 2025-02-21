import chromadb

chroma_client = chromadb.HttpClient(host="localhost", port=8000)
print(chroma_client.list_collections())

collection = chroma_client.create_collection(name="new_collection") # 새로운 컬렉션 만들기
print(chroma_client.list_collections()) # 컬렉션 리스트 출력


# 컬렉션 삭제 - chroma_client.delete_collection(name="") 
# 컬렉션 확인 - collection = chroma_client.get_collection("new_collection"), collection.peek()
