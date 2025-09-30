import streamlit as st
import pandas as pd
from db import get_engine
from sqlalchemy import NUMERIC
from etl import run_etl
from logger import get_logger

from utils import normalize_valor, gerar_hash

logger = get_logger(__name__)

st.set_page_config(page_title="Ingestão Financeira", page_icon="📊")

st.title("📊 Inserir dados Dashboard")
st.write("Faça upload da planilha mensal para carregar no banco e atualizar o DW.")

uploaded_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Ler CSV (tratando decimal brasileiro)
        df = pd.read_csv(uploaded_file, sep=",", quotechar='"', decimal=",")

        # Validar campos obrigatórios usando pandas
        campos_obrigatorios = ["Descrição", "Tipo", "Grupo", "Categoria", "Classificação", "Data", "Valor"]
        
        # Verificar se todos os campos obrigatórios existem
        campos_faltando = [campo for campo in campos_obrigatorios if campo not in df.columns]
        if campos_faltando:
            st.error(f"❌ Campos obrigatórios não encontrados: {', '.join(campos_faltando)}")
            st.stop()
        
        # Normalizar strings vazias e espaços para NaN usando pandas
        df_validacao = df[campos_obrigatorios].copy()
        df_validacao = df_validacao.replace('', pd.NA)  # Converte strings vazias para NA
        df_validacao = df_validacao.replace(r'^\s*$', pd.NA, regex=True)  # Converte strings só com espaços para NA

        # Usar pandas para encontrar registros com valores nulos
        registros_com_nulos = df_validacao.isnull().any(axis=1)
        
        if registros_com_nulos.any():
            indices_problemas = df_validacao[registros_com_nulos].index.tolist()
            st.error(f"🚫 Encontrados {len(indices_problemas)} registros com valores nulos!")
            
            st.write("**Registros com problemas:**")
            
            # Mostrar registros problemáticos
            df_problemas = df.iloc[indices_problemas]
            st.dataframe(df_problemas)
            
            # Usar pandas para mostrar quais campos estão nulos
            st.write("**Campos com valores nulos por registro:**")
            campos_nulos_por_registro = df_validacao[registros_com_nulos].isnull()
            
            for idx in indices_problemas:
                campos_nulos = campos_nulos_por_registro.loc[idx]
                campos_com_problema = campos_nulos[campos_nulos].index.tolist()
                if campos_com_problema:
                    st.write(f"Registro {idx + 1}: {', '.join(campos_com_problema)}")
            
            st.error(" Não é possível processar o arquivo com valores nulos. Corrija os dados e faça upload novamente.")
            st.stop()

        # Se chegou até aqui, não há valores nulos
        df["Valor"] = df["Valor"].fillna("0")
        df["id_hash"] = df.apply(gerar_hash, axis=1)
        df = normalize_valor(df)

        st.success("✅ Arquivo carregado com sucesso!")
        st.success("✅ Validação de campos obrigatórios: OK!")
        st.write("Pré-visualização dos dados:")
        st.dataframe(df.head(10))

        if st.button("Processar e carregar na base de dados", type="primary"):
            try:
                engine = get_engine()

                # Carregar staging
                df.to_sql("staging_lancamentos", engine, if_exists="replace", index=False, dtype={"Valor": NUMERIC(15,2)})
                logger.info(f"{len(df)} registros inseridos em staging_lancamentos")
                st.info(f"📥 {len(df)} registros inseridos em staging_lancamentos")

                run_etl()

                st.success("✅ Dados carregados e base de dados atualizado com sucesso!")
                st.balloons()  # 🎉 efeito visual
            except Exception as e:
                logger.exception("Erro durante o processamento")
                st.error(f"❌ Ocorreu um erro no processamento dos dados: {e}")

    except Exception as e:
        logger.exception("Erro ao carregar CSV")
        st.error(f"❌ Não foi possível carregar o arquivo: {e}")
