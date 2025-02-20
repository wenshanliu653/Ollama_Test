from ollama_python_test import OllamaSQLQueryTool

def main():
    # 初始化 SQL 查詢工具
    try:
        sql_tool = OllamaSQLQueryTool(
            host="localhost",
            user="root",
            password="12345678",  # 請更改為您的密碼
            database="new_db"     # 請更改為您的數據庫名
        )
        
        print("歡迎使用數據庫查詢助手！")
        print("輸入 'exit' 來退出程序")
        
        while True:
            # 獲取用戶輸入
            question = input("\n請輸入您的問題: ").strip()
            
            # 檢查是否退出
            if question.lower() in ['exit']:
                print("感謝使用！再見！")
                break
            
            # 如果輸入為空，繼續下一輪
            if not question:
                print("請輸入有效的問題！")
                continue
            
            # 獲取答案
            try:
                result = sql_tool.query(question)
                
                # 打印結果
                print("\n=== 查詢結果 ===")
                if 'error' in result:
                    print(f"錯誤: {result['error']}")
                else:
                    print(f"答案: {result['answer']}")
                    print(f"\nSQL查詢: {result['sql_query']}")
                    print("\n相關上下文:")
                    print(result['relevant_context'])
                
            except Exception as e:
                print(f"查詢過程中發生錯誤: {str(e)}")
                
    except Exception as e:
        print(f"程序初始化錯誤: {str(e)}")

if __name__ == "__main__":
    main()