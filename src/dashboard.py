
from pathlib import Path
import os

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Configuracao da pagina
st.set_page_config(
    page_title="Dashboard IoT",
    page_icon="🌡️",
    layout="wide"
)

# Localizar o arquivo .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL nao encontrada no arquivo .env")
    st.stop()


# Conexao com PostgreSQL
@st.cache_resource
def conectar_banco():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


# Consultar as views SQL
@st.cache_data(ttl=60)
def carregar_dados(nome_view):
    views_permitidas = {
        "avg_temp_por_dispositivo",
        "leituras_por_hora",
        "temp_max_min_por_dia"
    }

    if nome_view not in views_permitidas:
        raise ValueError("View SQL nao permitida")

    engine = conectar_banco()

    with engine.connect() as conexao:
        df = pd.read_sql_query(
            text(f"SELECT * FROM {nome_view}"),
            conexao
        )

    return df


# Cabecalho do dashboard
st.title("🌡️ Dashboard de Temperaturas IoT")

st.markdown(
    "Monitoramento e analise de temperaturas "
    "registradas por sensores IoT, utilizando "
    "Python, Docker, PostgreSQL e Streamlit."
)

st.divider()


# Carregar os dados
try:
    df_media = carregar_dados(
        "avg_temp_por_dispositivo"
    )

    df_horas = carregar_dados(
        "leituras_por_hora"
    )

    df_dias = carregar_dados(
        "temp_max_min_por_dia"
    )

except Exception as erro:
    st.error("Erro ao conectar ao PostgreSQL.")
    st.exception(erro)
    st.stop()


if df_media.empty:
    st.warning("Nao existem leituras no banco.")
    st.stop()


# Indicadores principais
medias = dict(
    zip(df_media["dispositivo"], df_media["avg_temp"])
)

total_leituras = int(
    df_media["total_leituras"].sum()
)

media_interna = medias.get("In", 0)
media_externa = medias.get("Out", 0)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total de leituras",
        f"{total_leituras:,}".replace(",", ".")
    )

with col2:
    st.metric(
        "Temperatura media interna",
        f"{media_interna:.2f} °C"
    )

with col3:
    st.metric(
        "Temperatura media externa",
        f"{media_externa:.2f} °C"
    )

st.divider()


# GRAFICO 1
st.subheader(
    "1. Temperatura Media por Ambiente"
)

df_media["ambiente"] = df_media["dispositivo"].replace({
    "In": "Interno",
    "Out": "Externo"
})

fig1 = px.bar(
    df_media,
    x="ambiente",
    y="avg_temp",
    color="ambiente",
    text="avg_temp",
    labels={
        "ambiente": "Ambiente",
        "avg_temp": "Temperatura media (°C)"
    },
    title="Comparacao entre ambientes"
)

fig1.update_traces(
    texttemplate="%{y:.2f} °C",
    textposition="outside"
)

fig1.update_layout(
    showlegend=False,
    yaxis_range=[0, 45]
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.info(
    "Este grafico compara as temperaturas medias "
    "registradas em ambientes internos e externos."
)


# GRAFICO 2
st.subheader(
    "2. Quantidade de Leituras por Hora"
)

df_horas = df_horas.sort_values("hora")

fig2 = px.line(
    df_horas,
    x="hora",
    y="contagem",
    markers=True,
    labels={
        "hora": "Hora do dia",
        "contagem": "Quantidade de leituras"
    },
    title="Distribuicao horaria das leituras IoT"
)

fig2.update_xaxes(dtick=1)

st.plotly_chart(
    fig2,
    use_container_width=True
)

st.info(
    "Este grafico permite identificar os horarios "
    "com maior e menor volume de registros."
)


# GRAFICO 3
st.subheader(
    "3. Temperaturas Maximas e Minimas por Dia"
)

df_dias["data"] = pd.to_datetime(df_dias["data"])
df_dias = df_dias.sort_values("data")

fig3 = px.line(
    df_dias,
    x="data",
    y=["temp_max", "temp_min", "temp_media"],
    labels={
        "data": "Data",
        "value": "Temperatura (°C)",
        "variable": "Indicador"
    },
    title="Evolucao diaria das temperaturas"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

st.info(
    "Este grafico mostra os valores maximos, "
    "minimos e medios de temperatura por dia."
)


# Tabela de dados
st.divider()

st.subheader("Dados Consolidados")

st.dataframe(
    df_dias,
    use_container_width=True,
    hide_index=True
)

st.caption(
    "Fonte: Temperature Readings IoT Devices - Kaggle. "
    "Dados historicos processados com Python e PostgreSQL."
)
