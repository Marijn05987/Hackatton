import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Haal data op via de API
start_date = int(pd.to_datetime('2025-01-01').timestamp())
end_date = int(pd.to_datetime('2025-03-24').timestamp())
response = requests.get(f'https://sensornet.nl/dataserver3/event/collection/nina_events/stream?conditions%5B0%5D%5B%5D=time&conditions%5B0%5D%5B%5D=%3E%3D&conditions%5B0%5D%5B%5D={start_date}&conditions%5B1%5D%5B%5D=time&conditions%5B1%5D%5B%5D=%3C&conditions%5B1%5D%5B%5D={end_date}&conditions%5B2%5D%5B%5D=label&conditions%5B2%5D%5B%5D=in&conditions%5B2%5D%5B%5D=21&conditions%5B2%5D%5B%5D=32&conditions%5B2%5D%5B%5D=33&conditions%5B2%5D%5B%5D=34&args%5B%5D=aalsmeer&args%5B%5D=schiphol&fields%5B%5D=time&fields%5B%5D=location_short&fields%5B%5D=location_long&fields%5B%5D=duration&fields%5B%5D=SEL&fields%5B%5D=SELd&fields%5B%5D=SELe&fields%5B%5D=SELn&fields%5B%5D=SELden&fields%5B%5D=SEL_dB&fields%5B%5D=lasmax_dB&fields%5B%5D=callsign&fields%5B%5D=type&fields%5B%5D=altitude&fields%5B%5D=distance&fields%5B%5D=winddirection&fields%5B%5D=windspeed&fields%5B%5D=label&fields%5B%5D=hex_s&fields%5B%5D=registration&fields%5B%5D=icao_type&fields%5B%5D=serial&fields%5B%5D=operator&fields%5B%5D=tags')
colnames = pd.DataFrame(response.json()['metadata'])
data = pd.DataFrame(response.json()['rows'])
data.columns = colnames.headers
data['time'] = pd.to_datetime(data['time'], unit='s')

# Stel vliegtuigcapaciteit per vliegtuigtype in (schatting)
vliegtuig_capaciteit = {
    'Boeing 737-800': {'passagiers': 189, 'vracht_ton': 20},  # Geschatte capaciteit
    'Embraer ERJ 170-200 STD': {'passagiers': 80, 'vracht_ton': 7},
    'Embraer ERJ 190-100 STD': {'passagiers': 98, 'vracht_ton': 8},
    'Embraer ERJ190-100STD': {'passagiers': 98, 'vracht_ton': 8},  # Zelfde type als de vorige, maar met andere naam
    'Boeing 737-700': {'passagiers': 130, 'vracht_ton': 17},
    'Airbus A320 214': {'passagiers': 180, 'vracht_ton': 20},
    'Boeing 777-300ER': {'passagiers': 396, 'vracht_ton': 60},
    'Boeing 737-900': {'passagiers': 220, 'vracht_ton': 25},
    'Boeing 777-200': {'passagiers': 314, 'vracht_ton': 50},
    'Airbus A319-111': {'passagiers': 156, 'vracht_ton': 16}
}

# Stel de load factor in (85% van de capaciteit is bezet)
load_factor = 0.85

# Bereken het geluid per passagier en per ton vracht voor elk vliegtuigtype
def bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor):
    results = []

    for _, row in data.iterrows():
        vliegtuig_type = row['type']
        if vliegtuig_type in vliegtuig_capaciteit:
            # Geluid in dB (SEL)
            sel_dB = row['SEL_dB']
            
            # Haal passagiers en vracht op voor het vliegtuigtype
            passagiers = vliegtuig_capaciteit[vliegtuig_type]['passagiers']
            vracht_ton = vliegtuig_capaciteit[vliegtuig_type]['vracht_ton']
            
            # Pas de load factor alleen toe op de passagierscapaciteit
            passagiers_bezet = passagiers * load_factor
            
            # Geluid per passagier
            geluid_per_passagier = sel_dB / passagiers_bezet if passagiers_bezet != 0 else np.nan
            
            # Geluid per ton vracht (zonder load factor)
            geluid_per_vracht = sel_dB / vracht_ton if vracht_ton != 0 else np.nan
            
            results.append({
                'vliegtuig_type': vliegtuig_type,
                'geluid_per_passagier': geluid_per_passagier,
                'geluid_per_vracht': geluid_per_vracht
            })

    return pd.DataFrame(results)

# Berekeningen uitvoeren met de load factor
resultaten = bereken_geluid_per_passagier_en_vracht(data, vliegtuig_capaciteit, load_factor)

# Sorteer de resultaten op geluid per passagier en per vracht
resultaten_sorted_passagier = resultaten.sort_values(by='geluid_per_passagier')
resultaten_sorted_vracht = resultaten.sort_values(by='geluid_per_vracht')

# Maak de grafieken
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Grafiek voor geluid per passagier
sns.barplot(x='vliegtuig_type', y='geluid_per_passagier', data=resultaten_sorted_passagier, palette='viridis', ax=axes[0])
axes[0].set_title('Geluid per Passagier per Vliegtuigtype (Met Load Factor)', fontsize=14)
axes[0].set_xlabel('Vliegtuigtype', fontsize=12)
axes[0].set_ylabel('Geluid per Passagier (dB)', fontsize=12)
axes[0].tick_params(axis='x', rotation=45)

# Grafiek voor geluid per ton vracht
sns.barplot(x='vliegtuig_type', y='geluid_per_vracht', data=resultaten_sorted_vracht, palette='viridis', ax=axes[1])
axes[1].set_title('Geluid per Ton Vracht per Vliegtuigtype (Zonder Load Factor bij Vracht)', fontsize=14)
axes[1].set_xlabel('Vliegtuigtype', fontsize=12)
axes[1].set_ylabel('Geluid per Ton Vracht (dB)', fontsize=12)
axes[1].tick_params(axis='x', rotation=45)

# Pas de layout aan zodat alles goed zichtbaar is
plt.tight_layout()

# Toon de grafiek
plt.show()
