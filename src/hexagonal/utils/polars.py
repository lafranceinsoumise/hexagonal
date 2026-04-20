import polars as pl


def polars_large_to_long(
    df: pl.DataFrame,
    fixed_columns: dict[str, pl.DataType | None],
    variable_columns: dict[str, pl.DataType | None],
):
    columns = df.columns

    assert (len(columns) - len(fixed_columns)) % len(variable_columns) == 0
    reps = (len(columns) - len(fixed_columns)) // len(variable_columns)

    df = df.with_row_index()

    offset_var = len(fixed_columns)
    stride_var = len(variable_columns)

    fixed_part = [
        pl.col(c).cast(typ).alias(name)
        for (name, typ), c in zip(
            fixed_columns.items(), columns[:offset_var], strict=True
        )
        if typ is not None
    ]
    var_parts = []

    for i in range(reps):
        var_part = [
            pl.col(c).cast(typ).alias(name)
            for (name, typ), c in zip(
                variable_columns.items(),
                columns[
                    offset_var + stride_var * i : offset_var + stride_var * (i + 1)
                ],
                strict=True,
            )
            if typ is not None
        ]
        var_parts.append(var_part)

    res = (
        pl.concat(
            [
                df.select("index", pl.lit(i).alias("rep"), *fixed_part, *var_part)
                for i, var_part in enumerate(var_parts)
            ]
        )
        .sort(["index", "rep"])
        .select(pl.all().exclude("index", "rep"))
    )

    return res
