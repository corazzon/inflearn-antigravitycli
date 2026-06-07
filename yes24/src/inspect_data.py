import pandas as pd

# 데이터 로드
df = pd.read_csv("yes24/data/yes24_bestsellers.csv")

print("--- Data Info ---")
df.info()

print("\n--- Columns ---")
print(df.columns)

print("\n--- Missing Values ---")
print(df.isnull().sum())

print("\n--- Sample Data ---")
print(df.head(2))
