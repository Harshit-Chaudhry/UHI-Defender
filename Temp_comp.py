import requests
import pandas as pd
import numpy as np
import folium
from folium import plugins
import yaml
import os
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns


def load_config(config_path: str) -> dict:
    with open(config_path, 'r') as config_file:
        return yaml.safe_load(config_file)


def create_directories(output_path: str):
    os.makedirs(output_path, exist_ok=True)


def get_coordinates_from_yaml(coordinates_path: str) -> list:
    with open(coordinates_path, 'r') as file:
        coordinates_data = yaml.safe_load(file)
        coordinates_list = []
        for aim_id, data in coordinates_data.items():
            coordinates_list.append({
                'aim_id': aim_id,
                'address': data.get('address'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timestamp': data.get('timestamp')
            })
        return coordinates_list


def get_historical_temperature(lat: float, lng: float) -> pd.DataFrame:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lng}"
        f"&start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}"
        f"&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
        f"relative_humidity_2m_mean,precipitation_sum"
        f"&timezone=auto"
    )

    response = requests.get(url)
    data = response.json()
    if 'daily' in data:
        daily = data['daily']
        return pd.DataFrame({
            'date': pd.to_datetime(daily['time']),
            'temperature_max': daily['temperature_2m_max'],
            'temperature_min': daily['temperature_2m_min'],
            'temperature_mean': daily['temperature_2m_mean'],
            'humidity': daily['relative_humidity_2m_mean'],
            'precipitation': daily['precipitation_sum']
        })


def create_heatmap(temperature_data: list, output_path: str) -> str:
    lats = [d['lat'] for d in temperature_data]
    lngs = [d['lng'] for d in temperature_data]
    center_lat = sum(lats) / len(lats)
    center_lng = sum(lngs) / len(lngs)

    m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
    heatmap_data = [[d['lat'], d['lng'], d['avg_temp']] for d in temperature_data]
    plugins.HeatMap(heatmap_data).add_to(m)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_path, f"temperature_heatmap_{timestamp}.html")
    m.save(file_path)
    return file_path


def save_temperature_data(all_data, detailed_data, output_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(os.path.join(output_path, f"temperature_summary_{timestamp}.json"), 'w') as f:
        json.dump(all_data, f, indent=2)

    for aim_id, df in detailed_data.items():
        location = next((d for d in all_data if d['aim_id'] == aim_id), {})
        df['aim_id'] = aim_id
        df['address'] = location.get('address', '')
        df['latitude'] = location.get('lat')
        df['longitude'] = location.get('lng')
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['season'] = df['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
        })

        df.to_csv(os.path.join(output_path, f"temperature_data_{aim_id}_{timestamp}.csv"), index=False)

    stats = []
    for aim_id, df in detailed_data.items():
        location = next((d for d in all_data if d['aim_id'] == aim_id), {})
        stats_dict = {
            'aim_id': aim_id,
            'address': location.get('address'),
            'latitude': location.get('lat'),
            'longitude': location.get('lng')
        }
        grouped = df.groupby('season').agg({
            'temperature_mean': ['mean', 'min', 'max'],
            'temperature_max': ['mean', 'min', 'max'],
            'temperature_min': ['mean', 'min', 'max'],
            'humidity': ['mean', 'min', 'max'],
            'precipitation': ['sum', 'mean', 'max']
        }).round(2)
        for season in grouped.index:
            for metric, stats_set in grouped.loc[season].items():
                stats_dict[f"{season.lower()}_{metric[0]}_{metric[1]}"] = stats_set
        stats.append(stats_dict)

    pd.DataFrame(stats).to_csv(os.path.join(output_path, f"temperature_statistics_{timestamp}.csv"), index=False)


def create_trend_plots(detailed_data: dict, output_path: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for aim_id, df in detailed_data.items():
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        df['season'] = df['month'].map({
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
        })

        fig = plt.figure(figsize=(20, 12))

        ax1 = plt.subplot(2, 2, 1)
        yearly = df.groupby('year').agg({
            'temperature_mean': ['mean', 'std'],
            'temperature_max': ['mean', 'std'],
            'temperature_min': ['mean', 'std']
        })
        for metric in ['temperature_mean', 'temperature_max', 'temperature_min']:
            mean = yearly[metric]['mean']
            std = yearly[metric]['std']
            ax1.plot(mean.index, mean.values, marker='o', label=metric)
            ax1.fill_between(mean.index, mean - 1.96 * std, mean + 1.96 * std, alpha=0.2)
        ax1.set_title('Yearly Temperature Trends')
        ax1.legend()
        ax1.grid(True)

        ax2 = plt.subplot(2, 2, 2)
        sns.violinplot(data=df, x='season', y='temperature_mean', ax=ax2)
        sns.boxplot(data=df, x='season', y='temperature_mean', ax=ax2, color='white')
        ax2.set_title('Seasonal Temperature Distribution')

        ax3 = plt.subplot(2, 2, 3)
        monthly = df.groupby(['year', 'month'])['temperature_mean'].mean().reset_index()
        for year in monthly['year'].unique():
            y_data = monthly[monthly['year'] == year]
            ax3.plot(y_data['month'], y_data['temperature_mean'], label=str(year))
            z = np.polyfit(y_data['month'], y_data['temperature_mean'], 1)
            ax3.plot(y_data['month'], np.poly1d(z)(y_data['month']), linestyle='--')
        ax3.set_title('Monthly Temperature Patterns by Year')
        ax3.legend()
        ax3.grid(True)

        ax4 = plt.subplot(2, 2, 4)
        pivot = df.pivot_table(values='temperature_mean', index='year', columns='month', aggfunc='mean')
        sns.heatmap(pivot, cmap=sns.diverging_palette(220, 10, as_cmap=True), ax=ax4, annot=True, fmt='.1f')
        ax4.set_title('Temperature Changes Heatmap')

        plt.tight_layout()
        plot_path = os.path.join(output_path, f"temperature_trends_{aim_id}_{timestamp}.png")
        plt.savefig(plot_path, dpi=300)
        plt.close()


def process_temperature_pipeline(config_path: str = 'config.yaml', coordinates_path: str = 'coordinates.yaml'):
    config = load_config(config_path)
    output_path = config.get('directories', {}).get('temperature_output', os.path.join('data', 'temperature_heatmaps'))
    create_directories(output_path)

    coordinates_list = get_coordinates_from_yaml(coordinates_path)
    temperature_data = []
    detailed_data = {}

    for coord in coordinates_list:
        lat, lng = coord['latitude'], coord['longitude']
        aim_id = coord['aim_id']
        df = get_historical_temperature(lat, lng)
        if df is not None:
            avg_temp = df['temperature_mean'].mean()
            temperature_data.append({
                'lat': lat,
                'lng': lng,
                'avg_temp': avg_temp,
                'aim_id': aim_id,
                'address': coord['address']
            })
            detailed_data[aim_id] = df

    if temperature_data:
        heatmap_file = create_heatmap(temperature_data, output_path)
        create_trend_plots(detailed_data, output_path)
        save_temperature_data(temperature_data, detailed_data, output_path)


if __name__ == '__main__':
    process_temperature_pipeline()
