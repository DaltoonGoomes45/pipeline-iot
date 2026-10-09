
from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Diretorio principal do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carregar configuracoes do arquivo .env
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
CSV_PATH = BASE_DIR / "data" / "IOT-temp.csv"


def processar_dados():
    print("Lendo dados dos sensores IoT...")

    # Carregar o conjunto de dados
    df = pd.read_csv(CSV_PATH)

    total_original = len(df)

    # Padronizar os nomes das colunas
    df = df.rename(columns={
        "id": "reading_id",
        "room_id/id": "room_id",
        "noted_date": "data_leitura",
        "temp": "temperatura",
        "out/in": "dispositivo"
    })

    # Selecionar colunas relevantes
    df = df[
        [
            "reading_id",
            "room_id",
            "data_leitura",
            "temperatura",
            "dispositivo"
        ]
    ].copy()

    # Converter datas para formato datetime
    df["data_leitura"] = pd.to_datetime(
        df["data_leitura"],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    )

    # Converter temperaturas para numeros
    df["temperatura"] = pd.to_numeric(
        df["temperatura"],
        errors="coerce"
    )

    # Padronizar identificadores e tipos de sensor
    df["reading_id"] = (
        df["reading_id"].astype("string").str.strip()
    )

    df["dispositivo"] = (
        df["dispositivo"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Remover registros invalidos
    df = df.dropna(
        subset=[
            "reading_id",
            "data_leitura",
            "temperatura",
            "dispositivo"
        ]
    )

    df = df[df["reading_id"] != ""]

    # Manter somente ambientes internos e externos
    df = df[df["dispositivo"].isin(["In", "Out"])]

    # Remover registros duplicados pelo identificador
    df = df.drop_duplicates(subset=["reading_id"])

    print(f"Registros originais: {total_original}")
    print(f"Registros validos: {len(df)}")
    print(f"Registros descartados: {total_original - len(df)}")

    return df


def salvar_postgresql(df):
    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL nao configurada no arquivo .env"
        )

    print("Conectando ao PostgreSQL...")

    engine = create_engine(DATABASE_URL)

    with engine.begin() as conn:

        # Criar tabela caso ainda nao exista
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS temperature_readings (
                reading_id TEXT PRIMARY KEY,
                room_id TEXT,
                data_leitura TIMESTAMP NOT NULL,
                temperatura DOUBLE PRECISION NOT NULL,
                dispositivo TEXT NOT NULL
            )
        """))

        # Limpar registros antigos antes da nova carga
        conn.execute(text(
            "TRUNCATE TABLE temperature_readings"
        ))

        # Inserir os dados processados
        df.to_sql(
            "temperature_readings",
            con=conn,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi"
        )

        # Conferir quantidade armazenada
        total = conn.execute(text(
            "SELECT COUNT(*) FROM temperature_readings"
        )).scalar_one()

    print("Dados inseridos com sucesso!")
    print(f"Total no PostgreSQL: {total}")


def main():
    print("=== PIPELINE DE DADOS IOT ===")

    df = processar_dados()
    salvar_postgresql(df)

    print("Pipeline finalizado!")


if __name__ == "__main__":
    main()
