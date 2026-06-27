# -*- coding: utf-8 -*-
"""
이 스크립트는 iHerb 비타민 D SQLite 데이터베이스의 스키마와 샘플 데이터를 파악하기 위해 작성된 탐색용 코드입니다.
"""
import sqlite3
import pandas as pd

def explore_db():
    conn = sqlite3.connect("iherb/data/iherb_vitamind.sqlite")
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    
    for table_tuple in tables:
        table = table_tuple[0]
        print(f"\n--- Table: {table} ---")
        
        # Schema
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(col)
            
        # Sample data
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5;", conn)
        print("Sample data:")
        print(df)
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        row_count = cursor.fetchone()[0]
        print(f"Row count: {row_count}")
        
    conn.close()

if __name__ == "__main__":
    explore_db()
