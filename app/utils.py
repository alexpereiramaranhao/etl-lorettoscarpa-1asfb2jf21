from decimal import Decimal
import pandas as pd

def normalize_valor(df: pd.DataFrame) -> pd.DataFrame:
    df["valor"] = df["valor"].fillna("0")
    df["valor"] = (
        df["valor"]
        .astype(str)
        .str.replace(".", "", regex=False)   # remove milhar
        .str.replace(",", ".", regex=False)  # vírgula -> ponto
    )
    df["valor"] = df["valor"].apply(lambda x: Decimal(x))
    return df
