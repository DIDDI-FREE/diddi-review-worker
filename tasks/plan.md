# Plan d’implémentation — Runner réactif Google Play Review

## Objectif

Accompagner les actions réelles du reviewer Google Play et piloter uniquement les contre-rôles Review via les APIs normales de Go, Send et Food.

## Déjà réalisé

- Registre explicite reviewer/contre-rôle.
- Pollers Go, Send coursier et Food restaurant.
- Déduplication mémoire et SQL.
- Worker réactif et machine d’état de session.
- Adapters Go, Send et Food avec payloads PIN/GPS/preuves connus.
- 31 tests locaux.

## Étapes restantes

### 1. Bootstrap

- Charger `REVIEW_ACCOUNTS_JSON`.
- Créer clients HTTP et pollers par produit.
- Obtenir des JWT courts DiddiFreeID.
- Refuser tout compte non associé ou sans `is_review_account=true`.

### 2. Détection

- Go : nouvelle course et transition chauffeur indisponible → disponible.
- Send : nouvelle offre coursier.
- Food : nouvelle commande restaurant.
- Mémoriser les états observés et ignorer les états présents au démarrage.

### 3. Persistance

- Persister session, déclencheur, ressource, étape et actions engagées.
- Utiliser PostgreSQL pour l’état durable du runner.
- Utiliser Redis Streams pour file et verrou de traitement.
- Reprendre une session active après redémarrage.

### 4. Workflow Go

- Chauffeur Review : accepter, GPS, arriver, démarrer avec le PIN reviewer, terminer.
- Chauffeur reviewer : créer une seule demande après transition réelle.
- Ne jamais exécuter l’action métier du reviewer.

### 5. Workflow Send

- Coursier Review : accepter, GPS, collecter, remettre avec PIN et preuves.
- Arrêter sur refus, annulation ou état terminal.
- Bloquer le parcours consommateur si aucun signal public de nouvelle livraison n’existe.

### 6. Workflow Food

- Restaurant Review : accepter avec `prep_minutes`, marquer prête.
- Coursier Send : collecter et livrer selon le contrat Send.
- Bloquer la notation restaurant tant qu’aucun contrat n’existe.

### 7. Paiement et fiabilité

- Confirmer DiddiPay en mode test par lecture non destructive.
- Mode non confirmé = aucune action financière.
- Retries bornés ; après timeout, rechercher la ressource avant répétition.
- Classer les erreurs terminales et empêcher les doubles traitements.

### 8. Exploitation

- Documenter lancement, Portainer, réarmement et reprise.
- Ajouter métriques, corrélation et diagnostics.
- Documenter les parcours réellement validés.

## Ordre d’exécution

`bootstrap → détection → persistance → Go → Send → Food → Pay → exploitation`

## Blocages connus

- Pas de listing public confirmé pour une nouvelle livraison Send côté consommateur.
- Pas de listing public confirmé pour une nouvelle commande Food côté client.
- Un driver mobile Google Play externe reste nécessaire.
- La recette staging E2E nécessite une autorisation explicite.

## Vérification

```powershell
ruff check app tests migrations
$env:PYTHONPATH='.'; pytest -q
```
