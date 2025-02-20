from langchain_community.llms import Ollama
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase  # 更新 import 以符合新版 LangChain
from sqlalchemy import create_engine

# ✅ 設定本地 SQL 資料庫（這裡以 MySQL 為例）
db_url = "mysql+pymysql://root:12345678@localhost:3306/new_db"
engine = create_engine(db_url)
db = SQLDatabase(engine)

# ✅ 使用 Ollama 並確保它只回應 SQL 查詢
llm = Ollama(
    model="llama2",
    base_url="http://localhost:11434",  # 添加 Ollama 服務的 URL
    temperature=0,  # 降低温度以获得更确定的响应
)

# ✅ 設定 prompt，強制 LLM 只輸出 SQL 查詢
db_chain = SQLDatabaseChain.from_llm(
    llm=llm,
    db=db,
    verbose=True,
    return_intermediate_steps=True,
    return_direct=True,  # 改为 True 以直接返回查询结果
    use_query_checker=True,  # 添加查询检查器
)

# 創建一個封裝 SQL 查詢功能的類
class OllamaSQLQueryTool:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.db = SQLDatabase(self.engine)
        self.llm = Ollama(
            model="llama2",
            base_url="http://localhost:11434",
            temperature=0,
        )
        self.db_chain = SQLDatabaseChain.from_llm(
            llm=self.llm,
            db=self.db,
            verbose=True,
            return_intermediate_steps=True,
            return_direct=True,
            use_query_checker=True,
        )
    
    def query(self, question):
        try:
            response = self.db_chain(question)
            result = {
                'answer': response['result'],
                'sql_query': response['intermediate_steps'][0] if 'intermediate_steps' in response else None
            }
            return result
        except Exception as e:
            return {'error': str(e)}

# 使用示例
if __name__ == "__main__":
    db_url = "mysql+pymysql://root:12345678@localhost:3306/new_db"
    sql_tool = OllamaSQLQueryTool(db_url)
    
    # 測試查詢
    result = sql_tool.query("How many orders are currently have?")
    print(result)