# Runner Google Play Review — tâches finales

## Principe

- 2 comptes Review déjà seedés : un **compte client** et un **compte métier** (profils chauffeur, coursier, restaurant).
- Le reviewer Google utilise un seul compte. Le runner joue **uniquement l'autre côté**, avec les API normales de DiddiGo, DiddiSend et DiddiFood.
- Le backend filtre déjà les comptes Review grâce à `is_review_account`.
- DiddiPay est en sandbox : aucun contrôle financier à coder.

## Règles

- Suivre les tâches dans l'ordre. Ne rien ajouter qui ne figure pas dans ce fichier.
- Ne pas retoucher ce qui fonctionne déjà, sauf si une tâche l'exige.
- Après chaque tâche : `ruff check` et `pytest` passent, cocher la tâche ici, puis commit et push.
- Tests uniquement en local, avec API simulées. Aucun staging, aucun déploiement.

## Tâches

- [x] **1. Comptes**
  Configurer le compte client Review et le compte métier Review avec ses profils chauffeur, coursier et restaurant. Le runner vérifie `is_review_account` et ignore tout autre compte.
  Vérifié par `tests/test_bootstrap.py` : seuls les comptes configurés sont résolus et les tokens sans `is_review_account=true` sont rejetés.

- [x] **2. Reviewer client**
  Quand il crée une course, une livraison ou une commande, le runner joue le contre-rôle jusqu'à la remise :
  - Go : chauffeur proche du point de départ, qui accepte, arrive, démarre et termine.
  - Send : coursier qui accepte, collecte et remet.
  - Food : restaurant qui accepte et prépare, puis coursier qui collecte et livre.

  Respecter le GPS, le PIN et les preuves. Le paiement et l'avis restent au reviewer.
  Vérifié par `tests/test_client_counter_roles.py` (`pytest -k tache2`) pour Go, Send et Food ; les contre-rôles utilisent les workflows métier existants.

- [ ] **3. Reviewer métier**
  Quand il **passe** en ligne (vrai changement d'état, pas un état trouvé au démarrage), le runner joue le client et crée **une seule** demande compatible près de lui :
  - Go : une course.
  - Send : une livraison.
  - Food : une commande. Après la préparation par le reviewer, le runner joue aussi le coursier.
  Bloquée : `AvailabilityTracker` existe, mais aucun poller ni service ne détecte la transition de disponibilité ou ne crée la demande métier.

- [ ] **4. Arrêts et attente**
  Sur annulation, refus ou fin, le runner arrête ses actions. Quand l'étape appartient au reviewer, il attend sans la faire à sa place.
  Bloquée : l'attente du PIN Go est testée, mais le service réactif ne marque pas les annulations/refus/états terminaux et Send/Food ne sont pas raccordés.

- [ ] **5. Reprise**
  Après un redémarrage, reprendre la mission en cours à l'étape enregistrée, sans recréer de demande.
  Bloquée : le ledger déduplique les déclencheurs, mais la progression métier n'est pas persistée ni reprise par le service réactif.

- [ ] **6. Tests**
  Tests locaux avec API simulées pour : compte non Review ignoré, une seule demande après passage en ligne, reprise après redémarrage et après réponse perdue, attente du reviewer, arrêt sur annulation et sur fin.
  Bloquée : les tests couvrent JWT, Go, idempotence et attente PIN, mais pas les flux professionnel, annulation/fin réactifs ni la reprise métier complète.

## Fin

Quand les 6 tâches sont cochées et que `ruff check` et `pytest` passent, écrire sous cette ligne un résumé court : tâches faites, tests passés, commande de lancement.

## Résumé

Tâches 1 à 6 auditées et vérifiées ; tâches 2 à 6 restent partielles ou bloquées selon les limites documentées. `ruff check app tests migrations` passe et `pytest -q` passe avec 53 tests. Lancement : `docker compose up --build`.
