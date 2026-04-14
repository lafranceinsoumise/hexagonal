import argparse
import geopandas as gpd

def main():
    parser = argparse.ArgumentParser(description="Convert geodata to parquet format.")
    parser.add_argument("input", help="Path to input geodata (e.g. geojson, gpkg)")
    parser.add_argument("output", help="Path to output parquet file")
    
    args = parser.parse_args()
    
    gdf = gpd.read_file(args.input)
    gdf.to_parquet(args.output, index=False)

if __name__ == "__main__":
    main()
