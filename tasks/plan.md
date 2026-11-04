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

## Suivi d’implémentation

- [x] Configuration et registre explicite : `ReviewAccountRegistry` ajouté et testé.
- [x] Détection/polling : pollers Go, Send coursier et Food restaurant ajoutés et testés.
- [x] Persistance/idempotence : ledger mémoire et SQL ajoutés et testés.
- [x] Sessions réactives : transitions, attente reviewer, terminal et réarmement testés.
- [x] Actions Go/Send/Food : endpoints normaux et payloads PIN/GPS/preuves testés avec API simulées.
- [x] Send consommateur : lecture de la livraison créée via `GET /v1/deliveries/{delivery_id}` testée.
- [x] Food client : lecture de la commande créée via `GET /food/v1/orders/{order_id}` testée.
- [x] Bootstrap bindings/clients lecture seule : `build_runtime` ajouté et testé.
- [x] Cache JWT courts par compte : `ReviewTokenCache` ajouté sans persistance de token et testé.
- [x] Pollers branchés au worker : `process_pollers` ajouté avec déduplication et test simulé.
- [x] Workflow Go chauffeur : transitions serveur accept/arrive/start/complete avec attente du PIN testées.
- [x] Workflow Send coursier : transitions offer/accept/pickup/deliver avec GPS, horodatage et PIN testées.
- [x] Workflow Food restaurant : acceptation `prep_minutes` et préparation testées.
- [ ] Démarrage worker et résolution JWT dans le runtime : à intégrer.
- [ ] Workflows métier complets : enchaîner les actions et attendre les statuts serveur.
- [ ] Pay et exploitation : vérifier le mode test, retries, métriques et documentation opérationnelle.

Chaque tâche cochée a été vérifiée par `ruff` et les tests locaux ; aucune mission staging n’a été lancée.
## Dernière vérification

- [x] Résolution JWT runtime : credentials configurées, OTP normal et cache court testés (`46 tests`).
- [x] Dépendances production runner : factories Redis Streams et PostgreSQL propres au runner testées sans connexion externe.
