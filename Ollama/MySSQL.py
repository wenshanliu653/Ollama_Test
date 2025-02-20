import mysql.connector

def test_mysql_connection():
    try:
        # 創建連接
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="new_db"
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"成功連接到 MySQL 服務器，版本: {db_info}")
            
            # 創建游標
            cursor = connection.cursor()
            
            # 執行查詢
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print("數據庫中的表格：")
            for table in tables:
                print(table[0])
                
    except mysql.connector.Error as e:
        print(f"MySQL 連接錯誤: {e}")
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL 連接已關閉")

if __name__ == "__main__":
    test_mysql_connection()