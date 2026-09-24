import osmnx as ox

# 1. Récupérer le réseau routier de La Rochelle
G = ox.graph_from_place("La Rochelle, France", network_type="drive")

# 2. Définir le point à marquer
# Option A : coordonnées connues (latitude, longitude)
lat, lon = 46.1603, -1.1511  # ex : Vieux-Port de La Rochelle

# Option B : géocoder une adresse pour obtenir les coordonnées automatiquement
# lat, lon = ox.geocode("Vieux-Port, La Rochelle, France")

# 3. Tracer le graphe SANS l'afficher tout de suite (show=False)
fig, ax = ox.plot_graph(G, show=False, close=False)

# 4. Ajouter la croix rouge par-dessus (attention : x=longitude, y=latitude)
ax.scatter(lon, lat, c="red", marker="x", s=30, linewidths=3, zorder=5)

# 5. Sauvegarder l'image finale
fig.savefig("la_rochelle.png", dpi=300, bbox_inches="tight")