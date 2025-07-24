import osmnx as ox
import folium
from folium.plugins import HeatMap
import requests
import json
import pandas as pd
import time
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from datetime import datetime
import os

def get_historical_avg_temperature(latitude, longitude, year, api_key):
    """
    Retrieves the average historical temperature for the given year for given coordinates.
    """
    base_url = "http://api.worldweatheronline.com/premium/v1/past-weather.ashx"
    today = datetime.now()
    start_date = f"{year}-{today.month:02d}-{today.day:02d}"
    end_date = start_date
    params = {
        "key": api_key,
        "q": f"{latitude},{longitude}",
        "format": "json",
        "date": start_date,
        "enddate": end_date,
        "tp": 24
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and 'weather' in data['data']:
            daily_temps = [float(day['avgtempC']) for day in data['data']['weather']]
            if daily_temps:
                return sum(daily_temps) / len(daily_temps)
            else:
                print(f"Warning: No historical temperature data for {latitude}, {longitude} in {year}.")
                return None
        else:
            print(f"Warning: Could not retrieve historical temperature data for {latitude}, {longitude}.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical temperature for {latitude}, {longitude}: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing historical temperature response for {latitude}, {longitude}: {e}")
        return None

def create_heatmap(place, polygon_coords, api_keys, api_limit_per_key, output_dir="heatmaps"):
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    polygon = Polygon([(lon, lat) for lat, lon in polygon_coords])
    G = ox.graph_from_place(place, network_type="drive")
    nodes = ox.graph_to_gdfs(G, nodes=True, edges=False)
    num_nodes = len(nodes)
    print(f"Total number of nodes: {num_nodes}")

    nodes_within_polygon = []
    for _, node in nodes.iterrows():
        point = Point(node['x'], node['y'])
        if polygon.contains(point):
            nodes_within_polygon.append(node)

    nodes_filtered = pd.DataFrame(nodes_within_polygon)
    num_nodes_in_polygon = len(nodes_filtered)
    print(f"Number of nodes within the polygon: {num_nodes_in_polygon}")

    sampled_nodes = pd.DataFrame()
    if num_nodes_in_polygon > 0:
        if num_nodes_in_polygon > api_limit_per_key:
            sampled_nodes = nodes_filtered.sample(n=api_limit_per_key, random_state=42)
            print(f"Sampling {api_limit_per_key} nodes within the polygon due to API limit per key.")
        else:
            sampled_nodes = nodes_filtered
            print("Number of nodes within the polygon is within API limit.")
    else:
        print("No nodes found within the specified polygon. Skipping temperature data collection and heatmap generation.")
        return

    all_temp_data = []
    for year, key in api_keys.items():
        heat_data_historical = []
        requests_made = 0
        print(f"\n--- Collecting data for year: {year} ---")

        if not sampled_nodes.empty:
            for index, node in sampled_nodes.iterrows():
                if requests_made < api_limit_per_key:
                    avg_temp = get_historical_avg_temperature(node['y'], node['x'], year, key)
                    if avg_temp is not None:
                        heat_data_historical.append([node['y'], node['x'], avg_temp])
                        all_temp_data.append({
                            'latitude': node['y'],
                            'longitude': node['x'],
                            'avg_temperature': avg_temp,
                            'year': year,
                            'api_key_used': key[-8:]
                        })
                    requests_made += 1
                    time.sleep(0.3)  # Be kind to the API
                else:
                    print(f"API limit reached for year {year} (key ending in: {key[-8:]}). Stopping data collection for this year.")
                    break

            csv_filename = os.path.join(output_dir, f"newcastle_{year}_avg_temperature_within_polygon_sampled.csv")
            df_historical = pd.DataFrame(all_temp_data)
            df_historical_year = df_historical[df_historical['year'] == year]
            df_historical_year.to_csv(csv_filename, index=False)
            print(f"Average temperature data for {year} saved as {csv_filename}")

            # Create JSON file per year
            json_filename = os.path.join(output_dir, f"heatmap_data_{year}.json")
            year_json = df_historical_year[['latitude', 'longitude', 'avg_temperature', 'year']].to_dict(orient='records')
            with open(json_filename, 'w') as f:
                json.dump(year_json, f, indent=2)
            print(f"JSON data for {year} saved to {json_filename}")

            if heat_data_historical:
                m_historical = folium.Map(location=[sampled_nodes['y'].mean(), sampled_nodes['x'].mean()], zoom_start=12,
                                        tiles="Satellite", attr="Map data © contributors")
                HeatMap(heat_data_historical, radius=12, blur=10, min_opacity=0.5).add_to(m_historical)

                map_filename_historical = os.path.join(output_dir, f"newcastle_{year}_avg_temperature_heatmap_within_polygon_sampled.html")
                m_historical.save(map_filename_historical)
                print(f"Average temperature heatmap for {year} saved as {map_filename_historical} using key ending in: {key[-8:]}")
            else:
                print(f"No average temperature data was collected for {year} within the polygon (key ending in: {key[-8:]}), so the heatmap was not created.")
        else:
            print("No nodes within the specified polygon to sample or get historical average temperature data for.")

    all_temp_df = pd.DataFrame(all_temp_data)
    all_temp_csv_filename = os.path.join(output_dir, "newcastle_all_years_avg_temperature_within_polygon_sampled.csv")
    all_temp_df.to_csv(all_temp_csv_filename, index=False)
    print(f"\nAll years' average temperature data saved to: {all_temp_csv_filename}")

    # Create the final combined JSON file.
    json_filename = os.path.join(output_dir, "heatmap_data_all_years.json")
    all_years_json = all_temp_df[['latitude', 'longitude', 'avg_temperature', 'year']].to_dict(orient='records')  # create json
    with open(json_filename, 'w') as f:
        json.dump(all_years_json, f, indent=2)
    print(f"Combined data for all years saved to {json_filename}")

    

if __name__ == "__main__":
    place = "Newcastle upon Tyne, UK"
    polygon_coords = [
        (55.05, -1.75),
        (55.00, -1.60),
        (54.95, -1.65),
        (54.98, -1.78)
    ]
    api_keys = {
        "2025": "[YOUR_API_KEY_HERE]",
        "2024": "[YOUR_API_KEY_HERE]",
        "2023": "[YOUR_API_KEY_HERE]",
        "2022": "[YOUR_API_KEY_HERE]",
        "2021": "[YOUR_API_KEY_HERE]"
    }
    api_limit_per_key =  1   #400 t0 500
    output_directory = "heatmaps"  #  You can change this if you want a different folder name

    create_heatmap(place, polygon_coords, api_keys, api_limit_per_key, output_directory)
