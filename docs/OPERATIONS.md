# Exploitation

## Lancement local

```powershell
$env:PYTHONPATH='.'
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

Les tests se lancent avec :

```powershell
ruff check app tests migrations
$env:PYTHONPATH='.'; pytest -q
```

## Configuration

Dans Portainer, fournir `RUNNER_SERVICE_TOKEN` et `REVIEW_ACCOUNTS_JSON` comme
variables secrètes. Chaque compte doit être explicitement associé à un rôle et
à un contre-rôle. Les OTP ne doivent jamais apparaître dans les logs.

Le runner utilise Redis Streams pour la file et PostgreSQL pour l’état propre du
runner. Il ne lit aucune base Go, Send ou Food.

## Reprise et réarmement

Après redémarrage, le ledger et les sessions persistés empêchent la répétition
d’une action déjà engagée. Une session terminale ne se réarme qu’à partir d’un
nouveau déclenchement explicite ; une disponibilité déjà active au démarrage ne
crée pas de mission.

## Diagnostic

- `401` : credential de service ou JWT Review invalide.
- `409` : état métier non compatible ou doublon ; relire l’état serveur avant retry.
- `5xx`/timeout : retry borné puis recherche de la ressource par son identifiant.
- Pay non confirmé en mode test : opération financière refusée.

Les recettes Google Play réelles nécessitent un driver mobile externe implémentant
`app.e2e.GooglePlayDriver`. Les tests du runner sont locaux et utilisent des API
simulées.
