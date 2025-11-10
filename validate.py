import sqlite3, yaml, os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings


schema = DataFrameSchema({
    "age": Column(int, Check.in_range(17, 90), nullable=False),
    "hours_per_week": Column(int, Check.in_range(1, 99), nullable=False),
    "sex": Column(str, Check.isin([" Male", " Female"]), nullable=False)
}, coerce=True)

def main():
    conn = sqlite3.connect("governance.db")
    df = pd.read_sql("SELECT * FROM adult_income", conn)
    run_id = str(uuid.uuid4())
    try:
        schema.validate(df, lazy=True)
        print("All validation checks passed.")
    except pa.errors.SchemaErrors as err:
        print(f"  {len(err.failure_cases)} validation failures detected.")
        conn.execute("""CREATE TABLE IF NOT EXISTS validation_logs
                        (run_id TEXT, ts TEXT, column_name TEXT, row_index INT, value TEXT, message TEXT);""")
        for _, row in err.failure_cases.iterrows():
            conn.execute("INSERT INTO validation_logs VALUES (?,?,?,?,?,?)", (
                run_id, datetime.utcnow().isoformat(),
                row["column"], int(row["index"]), str(df.iloc[int(row["index"])][row["column"]]),
                row["failure_case"]
            ))
        conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
