# ---- Connection to ADLS Gen2 ----
storage_account = ""
account_key     = ""

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    account_key
)

def path(container, sub=""):
    return f"abfss://{container}@{storage_account}.dfs.core.windows.net/{sub}"

from pyspark.sql import functions as F
from pyspark.sql.window import Window

silver = spark.read.format("delta").load(path("silver", "spotify_tracks"))

# ---- Dimensions (surrogate keys via row_number) ----
dim_genre = (silver.select("track_genre").distinct()
    .withColumn("genre_key", F.row_number().over(Window.orderBy("track_genre"))))

dim_artist = (silver.select("primary_artist").distinct()
    .withColumn("artist_key", F.row_number().over(Window.orderBy("primary_artist"))))

dim_album = (silver.select("album_name").distinct()
    .withColumn("album_key", F.row_number().over(Window.orderBy("album_name"))))

dim_track = (silver.select("track_id", "track_name", "explicit", "key", "mode", "time_signature")
    .distinct()
    .withColumn("track_key", F.row_number().over(Window.orderBy("track_id", "track_name"))))

# COMMAND ----------

# ---- Fact table (grain = track x genre) ----
fact = (silver
    .join(dim_track.select("track_id", "track_name", "track_key"), ["track_id", "track_name"])
    .join(dim_genre, "track_genre")
    .join(dim_artist, "primary_artist")
    .join(dim_album, "album_name")
    .select("track_key", "genre_key", "artist_key", "album_key",
            "popularity", "duration_ms", "duration_min", "danceability", "energy",
            "loudness", "speechiness", "acousticness", "instrumentalness",
            "liveness", "valence", "tempo", "load_date"))


# ---- Write GOLD as Parquet (one folder per table) ----
gold_tables = [
    ("dim_genre", dim_genre),
    ("dim_artist", dim_artist),
    ("dim_album", dim_album),
    ("dim_track", dim_track),
    ("fact_track_popularity", fact),
]

for name, df in gold_tables:
    df.write.mode("overwrite").parquet(path("gold", name))
    print(f"{name}: {df.count()} rows")

print("Gold layer complete.")
