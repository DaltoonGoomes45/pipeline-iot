
-- VIEW 1: Media de temperatura por ambiente
CREATE OR REPLACE VIEW avg_temp_por_dispositivo AS
SELECT
    dispositivo,
    ROUND(AVG(temperatura)::numeric, 2) AS avg_temp,
    COUNT(*) AS total_leituras
FROM temperature_readings
GROUP BY dispositivo;


-- VIEW 2: Quantidade de leituras por hora
CREATE OR REPLACE VIEW leituras_por_hora AS
SELECT
    EXTRACT(HOUR FROM data_leitura)::integer AS hora,
    COUNT(*) AS contagem
FROM temperature_readings
GROUP BY EXTRACT(HOUR FROM data_leitura);


-- VIEW 3: Temperaturas maximas e minimas por dia
CREATE OR REPLACE VIEW temp_max_min_por_dia AS
SELECT
    data_leitura::date AS data,
    MAX(temperatura) AS temp_max,
    MIN(temperatura) AS temp_min,
    ROUND(AVG(temperatura)::numeric, 2) AS temp_media
FROM temperature_readings
GROUP BY data_leitura::date;
