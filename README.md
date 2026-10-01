# DAE

La première version affiche une carte interactive centrée sur La Rochelle avec
les DAE du fichier `src/Fichier_csv/geodae_larochelle.csv`. Les DAE situés hors
de la géométrie OSM du lieu demandé sont exclus. Les DAE proches sont
regroupés automatiquement lorsque la carte est dézoomée, puis se séparent en
zoomant.

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