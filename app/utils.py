from decimal import Decimal
import pandas as pd
import hashlib

def normalize_valor(df: pd.DataFrame) -> pd.DataFrame:
    df["Valor"] = df["Valor"].fillna("0")
    df["Valor"] = (
        df["Valor"]
        .astype(str)
        .str.replace(".", "", regex=False)   # remove milhar
        .str.replace(",", ".", regex=False)  # vírgula -> ponto
    )
    df["Valor"] = df["Valor"].apply(lambda x: Decimal(x))
    return df

def gerar_hash(row):
    base = (
            str(row["Tipo"]).strip().lower() + "-" +
            str(row["Grupo"]).strip().lower() + "-" +
            str(row["Categoria"]).strip().lower() + "-" +
            str(row["Data"]).strip() + "-" +
            str(row["Descrição"]).strip().lower() + "-" +
            str(row['Valor'])
    )
    return hashlib.md5(base.encode("utf-8")).hexdigest()