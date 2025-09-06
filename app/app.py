import streamlit as st
import pandas as pd
from db import get_engine
from sqlalchemy import NUMERIC
from etl import run_etl
from logger import get_logger

from utils import normalize_valor, gerar_hash

logger = get_logger(__name__)

st.set_page_config(page_title="Ingestão Financeira", page_icon="📊")

st.title("📊 Ingestão Financeira - MVP")
st.write("Faça upload da planilha mensal para carregar no banco e atualizar o DW.")

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Ler CSV (tratando decimal brasileiro)
        df = pd.read_csv(uploaded_file, sep=",", quotechar='"', decimal=",")

        df["valor"] = df["valor"].fillna("0")
        df["id_hash"] = df.apply(gerar_hash, axis=1)
        df = normalize_valor(df)

        st.success("✅ Arquivo carregado com sucesso!")
        st.write("Pré-visualização dos dados:")
        st.dataframe(df.head(10))

        if st.button("🚀 Processar e carregar no DW"):
            try:
                engine = get_engine()

                # Carregar staging
                df.to_sql("staging_lancamentos", engine, if_exists="replace", index=False, dtype={"valor": NUMERIC(15,2)})
                logger.info(f"{len(df)} registros inseridos em staging_lancamentos")
                st.info(f"📥 {len(df)} registros inseridos em staging_lancamentos")

                # Rodar ETL
                run_etl()

                st.success("✅ Dados carregados e DW atualizado com sucesso!")
                st.balloons()  # 🎉 efeito visual
            except Exception as e:
                logger.exception("Erro durante o ETL")
                st.error(f"❌ Ocorreu um erro no processamento ETL: {e}")

    except Exception as e:
        logger.exception("Erro ao carregar CSV")
        st.error(f"❌ Não foi possível carregar o arquivo: {e}")
