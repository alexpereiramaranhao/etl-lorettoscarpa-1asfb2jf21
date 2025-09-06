from decimal import Decimal
import pandas as pd
import hashlib

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

def gerar_hash(row):
    base = (
            str(row["Tipo"]).strip().lower() + "-" +
            str(row["Grupo"]).strip().lower() + "-" +
            str(row["Categoria"]).strip().lower() + "-" +
            str(row["data"]).strip() + "-" +
            str(row["Descrição"]).strip().lower() + "-" +
            str(row['valor'])
    )
    return hashlib.md5(base.encode("utf-8")).hexdigest()