import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Laad je data (gebruik hier je eigen dataset)
# Bijvoorbeeld: data = pd.read_csv('je_data.csv')
# Hier gaan we ervan uit dat de dataset al in de 'data' DataFrame zit

# Vliegtuig capaciteit mapping
vliegtuig_capaciteit_passagiersaantal = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16},
    'Boeing 787-9': {'passagiers': 296, 'vracht_ton': 45},
    'Airbus A320 214SL': {'passagiers': 180, 'vracht_ton': 20},
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

