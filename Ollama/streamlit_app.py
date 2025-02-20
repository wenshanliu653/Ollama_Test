# 執行 cmd: streamlit run streamlit_app.py

import streamlit as st
from ollama_python_test import OllamaSQLQueryTool

def initialize_sql_tool():
    """初始化 SQL 查詢工具"""
    if 'sql_tool' not in st.session_state:
        try:
            st.session_state.sql_tool = OllamaSQLQueryTool(
                host="localhost",
                user="root",
                password="12345678",  # 請更改為您的密碼
                database="new_db"     # 請更改為您的數據庫名
            )
        except Exception as e:
            st.error(f"數據庫連接錯誤: {str(e)}")
            return False
    return True

def main():
    st.title("💬 數據庫智能查詢助手")
    st.write("請輸入您的問題，我會幫您查詢數據庫。")

    # 初始化聊天歷史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # 初始化 SQL 工具
    if not initialize_sql_tool():
        return

    # 用戶輸入
    question = st.text_input("在此輸入您的問題:", key="user_input")

    if st.button("發送問題"):
        if not question:
            st.warning("請輸入問題！")
            return

        with st.spinner('正在查詢中...'):
            try:
                # 獲取答案
                result = st.session_state.sql_tool.query(question)
                
                # 添加到聊天歷史
                st.session_state.chat_history.append({
                    "question": question,
                    "result": result
                })
            except Exception as e:
                st.error(f"查詢錯誤: {str(e)}")

    # 顯示聊天歷史
    for chat in reversed(st.session_state.chat_history):
        with st.container():
            st.write("---")
            st.write("🤔 問題:", chat["question"])
            
            result = chat["result"]
            if 'error' in result:
                st.error(f"錯誤: {result['error']}")
            else:
                st.write("✨ 答案:", result['answer'])
                
                # 使用 expander 來顯示 SQL 查詢和上下文
                with st.expander("查看 SQL 查詢"):
                    st.code(result['sql_query'], language="sql")
                
                with st.expander("查看相關上下文"):
                    st.write(result['relevant_context'])

if __name__ == "__main__":
    main()