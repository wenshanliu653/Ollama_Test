from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

def test_vector_db():
    try:
        # 測試嵌入模型
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        print("嵌入模型加載成功！")
        
        # 測試創建向量存儲
        test_texts = ["這是一個測試文本"]
        vector_store = FAISS.from_texts(test_texts, embeddings)
        print("FAISS 向量存儲創建成功！")
        
        # 測試保存和加載
        if not os.path.exists("test_faiss"):
            os.makedirs("test_faiss")
        vector_store.save_local("test_faiss")
        print("向量存儲保存成功！")
        
        loaded_vectorstore = FAISS.load_local("test_faiss", embeddings)
        print("向量存儲加載成功！")
        
    except Exception as e:
        print(f"向量數據庫錯誤: {str(e)}")

# 在主程序中調用
if __name__ == "__main__":
    test_vector_db()