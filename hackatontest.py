import requests
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# Haal de data op via de API
start_date = int(pd.to_datetime('2025-01-01').timestamp())
end_date = int(pd.to_datetime('2025-03-24').timestamp())

response = requests.get(f'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D={start_date}&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D={end_date}&conditions%5B2%5D%5B%5D=label&conditions%5B2%5D%5B%5D=in&conditions%5B2%5D%5B%5D=21&conditions%5B2%5D%5B%5D=32&conditions%5B2%5D%5B%5D=33&conditions%5B2%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags')

colnames = pd.DataFrame(response.json()['metadata'])
data = pd.DataFrame(response.json()['rows'])
data.columns = colnames.headers
data['time'] = pd.to_datetime(data['time'], unit='s')

# Correcte vliegtuig capaciteit mapping
vliegtuig_capaciteit_passagiersaantal = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ 190-100 STD': {'passagiers': 98, 'vracht_ton': 8},
    'Embraer ERJ190-100STD': {'passagiers': 98, 'vracht_ton': 8},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16},
    'Boeing 787-9': {'passagiers': 296, 'vracht_ton': 45},
    'Canadair CL-600-2B19 CRJ-200LR': {'passagiers': 50, 'vracht_ton': 4},
    'Airbus A320 214SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus A319 111': {'passagiers': 156, 'vracht_ton': 16},
    'Airbus A320-214SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-203': {'passagiers': 277, 'vracht_ton': 45},
    'Boeing 787 8': {'passagiers': 242, 'vracht_ton': 40},
    'Airbus A320 232SL': {'passagiers': 180, 'vracht_ton': 20},
    'Airbus SAS A330-303': {'passagiers': 277, 'vracht_ton': 45},
    'Boeing 737-8MAX': {'passagiers': 210, 'vracht_ton': 25},
    'Airbus A321-232': {'passagiers': 220, 'vracht_ton': 30}
}

# Functie om passagierscapaciteit in categorieën te verdelen
def categorize_passenger_capacity(passenger_count):
    if 180 <= passenger_count <= 200:
        return '180-200'
    elif 200 < passenger_count <= 250:
        return '200-250'
    elif 250 < passenger_count <= 300:
        return '250-300'
    elif 300 < passenger_count <= 400:
        return '300-400'
    else:
        return 'Other'

# Filter de relevante kolommen
data_filtered = data[['type', 'SEL_dB']]  # Enkel vliegtuigtype en SEL_dB

# Voeg een nieuwe kolom 'passenger_category' toe op basis van het vliegtuigtype
data_filtered['passenger_category'] = data_filtered['type'].apply(
    lambda x: categorize_passenger_capacity(vliegtuig_capaciteit_passagiersaantal.get(x, {}).get('passagiers', 0))
)

# Groepeer de data op passagierscategorie en vliegtuigtype, en bereken de gemiddelde SEL_dB
grouped_data = data_filtered.groupby(['passenger_category', 'type']).agg(
    mean_decibel=('SEL_dB', 'mean')
).reset_index()

# Plotting
fig, ax = plt.subplots(figsize=(12, 6))

# Maak de grafiek voor de verschillende passagierscategorieën
for category in grouped_data['passenger_category'].unique():
    category_data = grouped_data[grouped_data['passenger_category'] == category]
    ax.bar(category_data['type'], category_data['mean_decibel'], label=category)

ax.set_xlabel('Vliegtuig Type')
ax.set_ylabel('Gemiddeld Decibel Niveau (SEL_dB)')
ax.set_title('Gemiddelde Decibel Niveaus per Vliegtuig Type en Passagierscategorie')
ax.legend(title='Passagierscategorie', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Toon de plot in Streamlit
st.pyplot(fig)


