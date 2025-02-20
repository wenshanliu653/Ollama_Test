from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
import os

# 設置 Google API 密鑰
os.environ["GOOGLE_API_KEY"] = "AIzaSyAQRSfsC8HJCRX7rAbLQC2eKqO0HpQUB1g"

class GeminiSQLQueryTool:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.db = SQLDatabase(self.engine)
        
        # 使用 Gemini
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0
        )
        
        # 創建自定義的 SQL 生成鏈
        template = """根據以下問題生成 SQL 查詢。
        僅返回 SQL 查詢，不要有任何解釋。
        數據庫架構信息：
        {schema}
        
        問題：{question}
        SQL 查詢："""
        
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["schema", "question"]
        )
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def query(self, question):
        try:
            # 獲取數據庫架構
            schema = self.db.get_table_info()
            
            # 生成 SQL 查詢
            sql_query = self.chain.invoke({
                "schema": schema,
                "question": question
            })
            
            # 清理和驗證 SQL 查詢
            sql_query = sql_query.strip().rstrip(';')
            
            # 執行查詢
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = [dict(row) for row in result]
                
            return {
                'answer': rows,
                'sql_query': sql_query
            }
            
        except Exception as e:
            return {'error': str(e)}

# 使用示例
if __name__ == "__main__":
    db_url = "mysql+pymysql://root:12345678@localhost:3306/new_db"
    sql_tool = GeminiSQLQueryTool(db_url)
    
    # 測試查詢
    result = sql_tool.query("How many orders are currently have?")
    print("SQL Query:", result.get('sql_query'))
    print("Result:", result.get('answer'))