-- 1. Database to hold the Gold views
CREATE DATABASE spotify_gold;
GO
USE spotify_gold;
GO

-- 2. Master key (one-time; required before creating a credential)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = '';
GO

-- 3. Credential so the data source reads storage via the
--    workspace Managed Identity (works for any caller / Power BI)
CREATE DATABASE SCOPED CREDENTIAL synapse_mi
WITH IDENTITY = 'Managed Identity';
GO

-- 4. External data source pointing at the Gold container
CREATE EXTERNAL DATA SOURCE gold_ds
WITH (
    LOCATION   = 'https://<storage_account>.dfs.core.windows.net/gold',
    CREDENTIAL = synapse_mi
);
GO

-- 5. Views over the Gold Parquet folders
CREATE OR ALTER VIEW dim_genre AS
SELECT * FROM OPENROWSET(BULK 'dim_genre/', DATA_SOURCE = 'gold_ds', FORMAT = 'PARQUET') AS r;
GO

CREATE OR ALTER VIEW dim_artist AS
SELECT * FROM OPENROWSET(BULK 'dim_artist/', DATA_SOURCE = 'gold_ds', FORMAT = 'PARQUET') AS r;
GO

CREATE OR ALTER VIEW dim_album AS
SELECT * FROM OPENROWSET(BULK 'dim_album/', DATA_SOURCE = 'gold_ds', FORMAT = 'PARQUET') AS r;
GO

CREATE OR ALTER VIEW dim_track AS
SELECT * FROM OPENROWSET(BULK 'dim_track/', DATA_SOURCE = 'gold_ds', FORMAT = 'PARQUET') AS r;
GO

CREATE OR ALTER VIEW fact_track_popularity AS
SELECT * FROM OPENROWSET(BULK 'fact_track_popularity/', DATA_SOURCE = 'gold_ds', FORMAT = 'PARQUET') AS r;
GO
