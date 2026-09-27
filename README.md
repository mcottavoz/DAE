# DAE

La première version affiche une carte interactive centrée sur La Rochelle avec un
5 DAE placés aléatoirement dans les limites de la commune. Les DAE proches sont
regroupés automatiquement lorsque la carte est dézoomée, puis se séparent en
zoomant.

## Installation

```bash
python3 -m pip install -r requirements.txt
```

## Générer la carte

```bash
python3 -m src.main
```
## Pour lancer le serveur

```bash
python3 -m http.server 8000 --bind 0.0.0.0
```


Le fichier `la_rochelle.html` peut ensuite être ouvert dans un navigateur. La
carte est navigable à la souris et permet de zoomer ; `--seed 42` permet de
reproduire la position des DAE de démonstration. Le nombre de DAE peut être
modifié avec `--count 4` ou `--count 5`.

Pour lancer les tests :

```bash
python3 -m unittest discover
```