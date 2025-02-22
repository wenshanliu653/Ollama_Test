from langchain_community.llms import Ollama
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS # 向量存儲 DB
from langchain.chains import ConversationalRetrievalChain
import mysql.connector
from mysql.connector import Error
import os
from time import sleep
import re

class OllamaSQLQueryTool:
    def __init__(self, host, user, password, database):
        # 修改數據庫配置
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '12345678',
            'database': 'new_db',
            'auth_plugin': 'mysql_native_password'  # 添加認證插件
        }
        
        # 先測試連接
        self.connection = self._create_connection()
        if not self.connection:
            raise Exception("無法連接到數據庫")
        
        # 使用正確的 URL 格式
        db_url = f"mysql+mysqlconnector://{user}:{password}@{host}/{database}?auth_plugin=mysql_native_password"
        try:
            self.db = SQLDatabase.from_uri(db_url)
        except Exception as e:
            print(f"SQLDatabase 初始化錯誤: {e}")
            raise e
        
        # 初始化 Ollama
        self.llm = Ollama(
            model="llama3.2",
            base_url="http://localhost:11434",
            temperature=0,
            # 新增參數測試 準確度
            top_p=0.1,     # 降低採樣範圍
            top_k=10,      # 限制候選詞數量
            num_ctx=4096,  # 增加上下文窗口
            repeat_penalty=1.2,  # 增加重複懲
        )
        
        # 初始化嵌入模型 (英文問題可以)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # 初始化向量存储
        self.vector_store = None
        self.initialize_vector_store()
        
        # 創建混合查詢鏈
        self.db_chain = self.create_hybrid_chain()

    # 連接初始化方法, 測試連接
    def _create_connection(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            if connection.is_connected():
                db_info = connection.get_server_info()
                print(f"成功連接到 MySQL 服務器版本: {db_info}")
                return connection
        except Error as e:
            print(f"MySQL 連接錯誤: {e}")
            print("請檢查以下內容：")
            print("1. MySQL 服務是否運行")
            print("2. 用戶名和密碼是否正確")
            print("3. 數據庫是否存在")
            return None

    # 向量存儲初始化方法：
    def initialize_vector_store(self):
        try:
            cursor = self.connection.cursor()
            
            # 獲取所有表格信息
            tables_info = []
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            ## 獲取表註釋
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                columns_info = []
                for column in columns:
                    col_name = column[0]
                    col_type = column[1]
                    columns_info.append(f"{col_name} ({col_type})")
                
                table_description = f"Table '{table_name}' contains columns: {', '.join(columns_info)}"
                tables_info.append(table_description)
            
            cursor.close()
            
            # 創建向量存储
            if os.path.exists("faiss_index"):
                try:
                    self.vector_store = FAISS.load_local("faiss_index", self.embeddings)
                except Exception as e:
                    print(f"加載向量索引錯誤: {e}")
                    self.vector_store = FAISS.from_texts(tables_info, self.embeddings)
                    self.vector_store.save_local("faiss_index")
            else:
                self.vector_store = FAISS.from_texts(tables_info, self.embeddings)
                self.vector_store.save_local("faiss_index")
                
        except Error as e:
            print(f"初始化向量存储錯誤: {e}")
            raise e

    def create_hybrid_chain(self):
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 2}
        )
        
        return SQLDatabaseChain.from_llm(
            llm=self.llm,
            db=self.db,
            verbose=True,
            return_intermediate_steps=True,
            return_direct=True,
            use_query_checker=True
        )

    def query(self, question):
            try:
                relevant_docs = self.vector_store.similarity_search(question, k=3)
                context = "\n".join([doc.page_content for doc in relevant_docs]) 
                # 提示工程 :提高準確度
                enhanced_question = f"""基於以下數據庫結構信息： 
    {context} 

    請幫我將這個問題轉換為 SQL 查詢："{question}"

    請注意： 
    1. 使用準確的表名和列名
    2. 考慮表之間的關係
    3. 確保 SQL 語法正確
    4. 如果需要聯接表，請使用適當的 JOIN 語句
    5. 如果涉及統計，請使用正確的聚合函數
    

    重要：請直接返回 SQL 查詢語句，不要包含任何其他文字說明。
    """
                
                response = self.db_chain(enhanced_question)
                
                # 修改這部分來處理結果
                if 'intermediate_steps' in response:
                    # 從 response 中提取 SQL 查詢
                    if isinstance(response['intermediate_steps'], list) and len(response['intermediate_steps']) >= 1:
                        sql_query = str(response['intermediate_steps'][0])  # 確保轉換為字符串
                    else:
                        sql_query = "無法獲取 SQL 查詢"
                        
                    # 步驟1: 取得原始 SQL 結果
                    try:
                        with self.connection.cursor() as cursor:
                            cursor.execute(sql_query)
                            raw_result = cursor.fetchall()  # 獲取所有結果
                            print(f"原始 SQL 結果: {raw_result}")  # 印出原始格式
                            
                            # 步驟2: 從原始結果中提取數字
                            sql_result = raw_result[0][0] if raw_result and raw_result[0] else None
                            print(f"提取的數字: {sql_result}")  # 印出提取的數字
                            
                    except Exception as e:
                        print(f"SQL 驗證錯誤: {e}")
                        sql_query = f"SQL 錯誤: {str(e)}"
                        sql_result = None
                
                result = {
                    'answer': sql_result,
                    'sql_query': sql_query,
                    'relevant_context': context
                }
                return result
                
            except Exception as e:
                return {'error': str(e)}

    def _clean_sql_query(self, sql_query):
        """清理 SQL 查询，提取出純 SQL 語句"""
        try:
            # 使用正則表達式找出 SELECT 語句
            pattern = r'SELECT\s+.*?;'
            matches = re.findall(pattern, sql_query, re.IGNORECASE | re.DOTALL)
            
            if matches:
                # 返回找到的最後一個完整 SQL 語句
                return matches[-1].strip()
            else:
                # 如果沒有找到完整的 SELECT 語句，返回原始錯誤
                return "無法提取有效的 SQL 查詢"
                
        except Exception as e:
            print(f"SQL 清理錯誤: {e}")
            return sql_query.strip()

    def __del__(self):
            try:
                if hasattr(self, 'connection') and self.connection:  # 首先檢查 connection 是否存在且不為 None
                    if self.connection.is_connected():  # 然後再檢查是否已連接
                        self.connection.close()
                        print("MySQL 連接已關閉")
            except Exception as e:
                print(f"關閉連接時發生錯誤: {e}")

# 使用示例
if __name__ == "__main__":
    try:
        # 使用正確的連接信息
        sql_tool = OllamaSQLQueryTool(
            host="localhost",
            user="root",          # 確保這是您的 MySQL 用戶名
            password="12345678",  # 確保這是您的實際密碼
            database="new_db"     # 確保這個數據庫已經存在
        )
        
        # 測試查詢
        result = sql_tool.query("How many orders are there?")  # Ans:2823
        print(result)

        sleep(10)
        # 測試查詢
        result2 = sql_tool.query(f"How many orders are from customer 'Land of Toys Inc.'?") # 49
        print(result2)

        # 測試查詢
        #result3 = sql_tool.query("How many orders are there?")
        #print(result3)
        
    except Exception as e:
        print(f"程序錯誤: {e}")