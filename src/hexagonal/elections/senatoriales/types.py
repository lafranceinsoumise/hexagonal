import polars as pl


TypeElectionSenatoriale = pl.Enum(
    ["MAJORITAIRE_T1", "MAJORITAIRE_T2", "PROPORTIONNELLE"]
)
