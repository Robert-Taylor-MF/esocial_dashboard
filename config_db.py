import pyodbc
import pandas as pd
import streamlit as st

# O @st.cache_resource garante que o Streamlit não fique abrindo uma nova 
# conexão com o banco toda vez que alguém clicar em um filtro.
@st.cache_resource
def get_connection():
    """
    Estabelece a conexão com o banco de dados CorporeRM.
    Substitua 'NOME_DO_SERVIDOR' pelo nome ou IP do servidor SQL.
    """
    try:
        conn_str = (
            "DRIVER={SQL Server};"
            "SERVER=129.200.19.30;"
            "DATABASE=CorporeRM;"
            # "Trusted_Connection=yes;" # Usa a autenticação do Windows (se aplicável)
            # Se precisar de usuário/senha, comente a linha acima e use as abaixo:
             "UID=sa;"
             "PWD=texpAr_1672#;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {e}")
        return None

# Função para executar a query e devolver um DataFrame do Pandas
@st.cache_data(ttl=600) # Faz cache dos dados por 10 minutos (600 segundos) para não sobrecarregar o banco
def load_data(query):
    conn = get_connection()
    if conn:
        df = pd.read_sql(query, conn)
        return df
    return pd.DataFrame()