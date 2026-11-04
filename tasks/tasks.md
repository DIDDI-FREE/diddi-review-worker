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

- [ ] **2. Reviewer client**
  Quand il crée une course, une livraison ou une commande, le runner joue le contre-rôle jusqu'à la remise :
  - Go : chauffeur proche du point de départ, qui accepte, arrive, démarre et termine.
  - Send : coursier qui accepte, collecte et remet.
  - Food : restaurant qui accepte et prépare, puis coursier qui collecte et livre.

  Respecter le GPS, le PIN et les preuves. Le paiement et l'avis restent au reviewer.

- [ ] **3. Reviewer métier**
  Quand il **passe** en ligne (vrai changement d'état, pas un état trouvé au démarrage), le runner joue le client et crée **une seule** demande compatible près de lui :
  - Go : une course.
  - Send : une livraison.
  - Food : une commande. Après la préparation par le reviewer, le runner joue aussi le coursier.

- [ ] **4. Arrêts et attente**
  Sur annulation, refus ou fin, le runner arrête ses actions. Quand l'étape appartient au reviewer, il attend sans la faire à sa place.

- [ ] **5. Reprise**
  Après un redémarrage, reprendre la mission en cours à l'étape enregistrée, sans recréer de demande.

- [ ] **6. Tests**
  Tests locaux avec API simulées pour : compte non Review ignoré, une seule demande après passage en ligne, reprise après redémarrage et après réponse perdue, attente du reviewer, arrêt sur annulation et sur fin.

## Fin

Quand les 6 tâches sont cochées et que `ruff check` et `pytest` passent, écrire sous cette ligne un résumé court : tâches faites, tests passés, commande de lancement.
