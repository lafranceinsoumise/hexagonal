import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd


def load_iris_contours(iris_path: str, departement: str | None = None) -> gpd.GeoDataFrame:
    iris_contours = gpd.read_file(iris_path)
    
    if departement:
        iris_contours = iris_contours[
            iris_contours["code_insee"].str.startswith(departement, na=False)
        ].copy()
    
    iris_contours = iris_contours.rename(columns={"code_iris": "CODE_IRIS", "nom_iris": "NOM_IRIS"})

    # Ensure it is in the target metric projection EPSG:2154
    if iris_contours.crs is None or iris_contours.crs.to_epsg() != 2154:
        iris_contours = iris_contours.to_crs("EPSG:2154")
        
    return iris_contours


def load_bureau_polygons(bureau_path: str) -> gpd.GeoDataFrame:
    if bureau_path.endswith(".parquet"):
        bureau_polygons = gpd.read_parquet(bureau_path)
    else:
        bureau_polygons = gpd.read_file(bureau_path)
        
    if bureau_polygons.crs is None or bureau_polygons.crs.to_epsg() != 2154:
        bureau_polygons = bureau_polygons.to_crs("EPSG:2154")
        
    return bureau_polygons


def extract_intersection_areas(
    bureau_path: str, iris_path: str, filter_departement: str | None = None
) -> pd.DataFrame:
    bureau_df = load_bureau_polygons(bureau_path)
    iris_df = load_iris_contours(iris_path, filter_departement)

    bureau_df = bureau_df.dropna(
        subset=["nomCommune", "numeroBureauVote"]
    )
    bureau_df["Code Bureau de Vote Departement"] = (
        bureau_df["nomCommune"]
        + "-"
        + bureau_df["numeroBureauVote"].str.lstrip("0")
    )
    
    if filter_departement:
        bureau_df = bureau_df[
            bureau_df["codeDepartement"] == filter_departement
        ].copy()

    bureau_polygons = bureau_df[["Code Bureau de Vote Departement", "geometry"]].copy()

    # Ensure geometries are valid and calculate total area
    bureau_polygons["geometry"] = bureau_polygons["geometry"].buffer(0)
    bureau_polygons["bureau_area"] = bureau_polygons.geometry.area

    # Geometrically intersect our created Bureau polygons with the existing IRIS polygons
    intersections = gpd.overlay(bureau_polygons, iris_df, how="intersection")

    intersections["intersection_area"] = intersections.geometry.area
    intersections["relative_area"] = (
        intersections["intersection_area"] / intersections["bureau_area"]
    )

    results = intersections[
        ["Code Bureau de Vote Departement", "CODE_IRIS", "NOM_IRIS", "relative_area"]
    ].copy()

    results = results.sort_values(
        by=["Code Bureau de Vote Departement", "relative_area"], ascending=[True, False]
    )

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate bureau de vote and IRIS intersections.")
    parser.add_argument("--bureau", required=True, help="Path to the bureau de vote geometries file (GeoJSON or Parquet)")
    parser.add_argument("--iris", default="data/01_raw/ign/iris-metropole.gpkg", help="Path to the IRIS geometries file")
    parser.add_argument("--output", default="exports/bureau_iris_relative_areas.csv", help="Path to write the results CSV")
    parser.add_argument("--departement", default=None, help="Optional department code to filter (e.g. 41)")
    args = parser.parse_args()

    results = extract_intersection_areas(
        bureau_path=args.bureau,
        iris_path=args.iris,
        filter_departement=args.departement
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path, index=False)


if __name__ == "__main__":
    main()
