# Contract audit — 04-11-2026

Audit read-only des dépôts locaux `diddi-free-id`, `diddi-go`, `diddi-send` et
`diddi-food`. Aucun code métier n’a été modifié.

## Findings

### DiddiFreeID

- Les access tokens sont des JWT RS256 vérifiables via `/.well-known/jwks.json`.
- Le claim `is_review_account` est émis par DiddiFreeID, strictement booléen et
  rejeté s’il est malformé.
- Les nouveaux comptes sont non-review par défaut.
- L’activation review est une mutation admin auditée :
  `PATCH /admin/users/{user_id}/review-account`.
- Un compte review peut utiliser un OTP statique configuré côté serveur ; le code
  est sélectionné par UUID dans `REVIEW_STATIC_OTP_CODES_JSON`, avec rate limit et
  verrouillage. Ce mécanisme est un détail de provisioning/exécution, pas un token
  permanent.
- Conséquence runner : il faut un `DiddiFreeIDAuthAdapter` qui obtient des access
  tokens courts et vérifie localement issuer, audience, expiration, signature et
  `is_review_account is True`. Le runner ne doit pas appeler la route admin.

### DiddiGo

- Mutation de notation : `POST /{ride_id}/rating`.
- Le rôle du notant est déduit du propriétaire de la course et du rôle JWT ; le
  runner ne peut pas injecter librement `passenger` ou `driver`.
- La course doit être `COMPLETED`, le score est compris entre 1 et 5 et une seule
  notation par rôle est permise.
- Le matching isole les comptes review des comptes production en comparant le
  flag review de la course et celui du profil.
- Les contrôles driver/KYC/KYV et l’état wallet restent des règles métier
  existantes ; le runner doit les satisfaire par le parcours normal.

### DiddiSend

- Notation sender/client : `POST /deliveries/{delivery_id}/rate`.
- Notation courier : `POST /courier/deliveries/{delivery_id}/rate`.
- Une livraison doit être `delivered`, l’auteur doit être le participant attendu,
  et la contrainte `(delivery_id, author_role)` empêche les doublons.
- Le matching refuse les croisements review/production via
  `is_review_account == is_review_delivery`.
- Les livraisons Food sont reconnues par `origin_module == "diddifood"` et le
  client est alors le `customer_user_id` plutôt que le sender classique.
- Conséquence runner : les deux adapters d’action doivent partager le même modèle
  de delivery et attendre la fin métier avant de noter.

### DiddiFood

- Notation customer : `POST /{order_id}/rating` sur le router customer.
- Une commande doit être `DELIVERED`, appartenir au customer JWT et ne peut être
  notée qu’une fois (`order_id` unique dans `order_ratings`).
- La création de commande transmet `is_review_account` et le delivery adapter
  transmet `is_review_delivery` à DiddiSend.
- Les lectures exposent les agrégats restaurant, mais aucune mutation de notation
  restaurant n’a été trouvée.
- Aucun endpoint DiddiFood distinct de notation courier/restaurant n’a été trouvé.
  Le courier rating est donc actuellement une responsabilité DiddiSend ; la
  notation restaurant constitue un gap de contrat à arbitrer.

## Verdict on the plan

Le découpage `identity → adapters → persistence → scenarios → orchestration → api`
est valide. Il faut cependant ajouter les contraintes suivantes :

1. Les scénarios doivent séparer les actions métier de leur précondition et
   attendre les statuts terminaux (`COMPLETED`, `delivered`, `DELIVERED`).
2. Les adapters doivent modéliser les rôles dérivés par le backend, pas les forcer
   dans les payloads.
3. Les identifiants de delivery/order/ride et les liens cross-service doivent être
   conservés dans le contexte du run.
4. Les erreurs `already rated`, `not completed/delivered`, `not owner` et
   `review-production mismatch` doivent être des erreurs terminales explicites,
   non retryables par défaut.
5. Le scénario DiddiFood ne peut pas être déclaré complet tant qu’un contrat de
   notation restaurant n’est pas fourni, ou tant que ce rôle n’est pas retiré du
   périmètre runner.
6. Le runner doit piloter un utilisateur Google/app séparément des acteurs review :
   la session Google Play ne peut pas être déduite des JWT DiddiFreeID et nécessite
   un driver E2E ou un hook de test explicitement documenté.

## Recommended implementation slices

1. Construire les adapters/auth et les contrats de lecture/notation existants.
2. Implémenter un scénario vertical DiddiSend (sender + courier).
3. Implémenter DiddiGo (passenger + driver).
4. Implémenter DiddiFood customer + courier via DiddiFood/DiddiSend.
5. Garder `restaurant review` en état `blocked_by_contract` jusqu’à décision
   produit/API ; ne pas inventer de route.

