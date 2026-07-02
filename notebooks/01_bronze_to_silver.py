# ---- Connection to ADLS Gen2 ----
storage_account = ""   
account_key     = ""    

spark.conf.set(
    f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
    account_key
)

def path(container, sub=""):
    return f"abfss://{container}@{storage_account}.dfs.core.windows.net/{sub}"

# COMMAND ----------

from pyspark.sql import functions as F

# ---- Read RAW CSV from Bronze (ADF Copy lands it here: landing container -> bronze container) ----
# The escape/multiLine options handle song & album names that contain commas or quotes, which would otherwise shift the columns.
raw = (spark.read
       .option("header", True)
       .option("inferSchema", True)
       .option("escape", '"')
       .option("multiLine", True)
       .csv(path("bronze", "spotify/dataset.csv")))

cols = ["track_id", "artists", "album_name", "track_name", "popularity",
        "duration_ms", "explicit", "danceability", "energy", "key", "loudness",
        "mode", "speechiness", "acousticness", "instrumentalness", "liveness",
        "valence", "tempo", "time_signature", "track_genre"]
raw = raw.select(*cols)

# ---- Clean -> Silver ----
silver = (raw
    .na.drop(subset=["track_id", "track_name", "track_genre"])
    # a track_id repeats across genres; grain = track x genre
    .dropDuplicates(["track_id", "track_genre"])
    .withColumn("explicit", F.col("explicit").cast("boolean"))
    # multiple artists are ';' separated -> keep the primary (first) artist
    .withColumn("primary_artist", F.trim(F.split("artists", ";").getItem(0)))
    .withColumn("duration_min", F.round(F.col("duration_ms") / 60000, 2))
    # watermark column to support incremental / audit patterns
    .withColumn("load_date", F.current_date()))

silver.write.format("delta").mode("overwrite").save(path("silver", "spotify_tracks"))

print("Silver written. Rows:", silver.count())
