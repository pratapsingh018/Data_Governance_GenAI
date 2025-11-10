import pandas as pd
import sqlite3

# URLs and schema
COLS = ["age","workclass","fnlwgt","education","education_num",
        "marital_status","occupation","relationship","race","sex",
        "capital_gain","capital_loss","hours_per_week","native_country","income"]

URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"

def main():
    print("Downloading UCI Adult Income dataset...")
    df = pd.read_csv(URL, header=None, names=COLS, na_values=" ?", skipinitialspace=True)

    with sqlite3.connect("governance.db") as conn:
        df.to_sql("adult_income", conn, if_exists="replace", index=False)

    print(f"Loaded {len(df)} rows into governance.db → adult_income")

if __name__ == "__main__":
    main()