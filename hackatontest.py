import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json

# Cache de gegevensophaal functie om onnodige herhalingen van verzoeken te voorkomen
@st.cache_data
def fetch_data(start_date, end_date):
    url = f'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D={start_date}&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D={end_date}&conditions%5B2%5D%5B%5D=label&conditions%5B2%5D%5B%5D=in&conditions%5B2%5D%5B%5D=21&conditions%5B2%5D%5B%5D=32&conditions%5B2%5D%5B%5D=33&conditions%5B2%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags'
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Zorgt ervoor dat een HTTP-fout een uitzondering veroorzaakt
        colnames = pd.DataFrame(response.json()['metadata'])
        data = pd.DataFrame(response.json()['rows'])
        data.columns = colnames.headers
        data['time'] = pd.to_datetime(data['time'], unit='s')
        return data
    except requests.exceptions.RequestException as e:
        st.error(f"Er is een probleem met het ophalen van de gegevens van de API: {e}")
        if e.response is not None:
            st.write(f"Foutdetails: {e.response.text}")  # Toon gedetailleerde foutmelding
        st.stop()  # Stop de app als er een probleem is bij het ophalen van de gegevens
    except Exception as e:
        st.error(f"Er is een onverwachte fout opgetreden: {e}")
        st.stop()  # Stop de app als er een onverwachte fout is

# Cache de berekeningen van geluid per passagier en vracht
@st.cache_data
def bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor):
    results = []

    for _, row in data.iterrows():
        vliegtuig_type = row['type']
        if vliegtuig_type in vliegtuig_capaciteit:
            sel_dB = row['SEL_dB']
            passagiers = vliegtuig_capaciteit[vliegtuig_type]['passagiers']
            vracht_ton = vliegtuig_capaciteit[vliegtuig_type]['vracht_ton']
            
            passagiers_bezet = passagiers * load_factor
            geluid_per_passagier = sel_dB / passagiers_bezet if passagiers_bezet != 0 else np.nan
            geluid_per_vracht = sel_dB / vracht_ton if vracht_ton != 0 else np.nan
            
            results.append({
                'vliegtuig_type': vliegtuig_type,
                'geluid_per_passagier': geluid_per_passagier,
                'geluid_per_vracht': geluid_per_vracht
            })

    return pd.DataFrame(results)

# Stel vliegtuigcapaciteit in
vliegtuig_capaciteit = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ 190-100 STD': {'passagiers': 98, 'vracht_ton': 8},
    'Embraer ERJ190-100STD': {'passagiers': 98, 'vracht_ton': 8},
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16}
}

# Stel de load factor in (85% van de capaciteit)
load_factor = 0.85

# Streamlit UI
st.title('Geluid per Passagier en Vracht per Vliegtuigtype')
st.markdown('Dit applicatie berekent en toont het geluid per passagier en per ton vracht voor verschillende vliegtuigtypes, gebaseerd op gegevens uit de luchtvaart.')

# Date Range input van gebruiker
start_date_input = st.date_input("Start Date", pd.to_datetime('2025-01-01'))
end_date_input = st.date_input("End Date", pd.to_datetime('2025-03-24'))

# Converteer de datums naar UNIX-tijdstempels
start_date = int(pd.to_datetime(start_date_input).timestamp())
end_date = int(pd.to_datetime(end_date_input).timestamp())

# Haal de gegevens op
data = fetch_data(start_date, end_date)

# Voer de berekeningen uit
resultaten = bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor)

# Sorteer de resultaten
resultaten_sorted_passagier = resultaten.sort_values(by='geluid_per_passagier')
resultaten_sorted_vracht = resultaten.sort_values(by='geluid_per_vracht')

# Toon de resultaten als tabellen
st.subheader('Geluid per Passagier per Vliegtuigtype')
st.write(resultaten_sorted_passagier)

st.subheader('Geluid per Ton Vracht per Vliegtuigtype')
st.write(resultaten_sorted_vracht)

# Maak de grafieken
st.subheader('Grafieken')

# Maak de grafieken
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Geluid per Passagier
sns.barplot(x='vliegtuig_type', y='geluid_per_passagier', data=resultaten_sorted_passagier, palette='viridis', ax=axes[0])
axes[0].set_title('Geluid per Passagier per Vliegtuigtype (Met Load Factor)', fontsize=14)
axes[0].set_xlabel('Vliegtuigtype', fontsize=12)
axes[0].set_ylabel('Geluid per Passagier (dB)', fontsize=12)
axes[0].tick_params(axis='x', rotation=45)

# Geluid per Ton Vracht
sns.barplot(x='vliegtuig_type', y='geluid_per_vracht', data=resultaten_sorted_vracht, palette='viridis', ax=axes[1])
axes[1].set_title('Geluid per Ton Vracht per Vliegtuigtype (Zonder Load Factor bij Vracht)', fontsize=14)
axes[1].set_xlabel('Vliegtuigtype', fontsize=12)
axes[1].set_ylabel('Geluid per Ton Vracht (dB)', fontsize=12)
axes[1].tick_params(axis='x', rotation=45)

# Pas de lay-out aan voor betere zichtbaarheid
plt.tight_layout()

# Toon de grafiek in Streamlit
st.pyplot(fig)
