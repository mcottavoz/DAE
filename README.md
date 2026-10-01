# DAE

La carte interactive est centrée sur La Rochelle et affiche
les DAE du fichier `src/Fichier_csv/geodae_larochelle.csv`. Les DAE situés hors
de la géométrie OSM du lieu demandé sont exclus. Les DAE proches sont
regroupés automatiquement lorsque la carte est dézoomée, puis se séparent en
zoomant.

La couche `Population (carreaux de 200 m)` peut être activée avec le bouton de
contrôle des couches. Elle utilise le fichier
`src/Fichier_csv/carreaux_200m_la_rochelle_coord.csv` et colore les carreaux
transparents selon la population estimée. Seuls les carrés entièrement compris
dans la géométrie OSM sont affichés; les carrés sans habitant sont barrés d'une
croix. La couche `Limite géométrique OSM` permet d'afficher le contour de la
zone utilisée pour ces filtres.

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Générer la carte
.venv/bin/activate

```bash
python3 -m src.main
```
## Pour lancer le serveur

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```


Le fichier `la_rochelle.html` peut ensuite être ouvert dans un navigateur. La
carte est navigable à la souris et permet de zoomer. Un autre fichier CSV peut
être utilisé avec `--dae-file chemin/vers/fichier.csv`.

Pour lancer les tests :

```bash
python3 -m unittest discover
```