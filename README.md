# Attendance Manager (ZKTeco + Access)

Application Python pour extraire les présences depuis Microsoft Access (ATT2000.mdb) et dispositifs ZKTeco, puis exporter en CSV.

## Démarrage rapide

1. Créer l'environnement et installer:
```bash
pip install -r requirements.txt
```
2. Copier et éditer la configuration:
```bash
copy config.ini.template config.ini
```
3. Lancer l'extraction Access → CSV:
```bash
python main.py
```

Le CSV est généré dans `./exports/`.

## Configuration
Voir `config.ini.template` pour les sections `ACCESS_DB`, `CSV_EXPORT`, `ZKTECO_DEVICES`, `LOGGING`.
