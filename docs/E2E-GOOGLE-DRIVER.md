# Google Play E2E driver

Le runner backend ne pilote pas directement Google Play. Un driver mobile externe doit
implémenter `app.e2e.GooglePlayDriver` avec Appium, Maestro ou l’outil E2E déjà utilisé
par l’équipe mobile.

Le driver doit utiliser un compte Google de test unique par session et ne doit exécuter
que le parcours visible par l’utilisateur : ouverture de l’app, connexion Google,
création de la course/livraison/commande et attente du statut final.

Il transmet ensuite au runner les identifiants `ride_id`, `delivery_id` ou `order_id`.
Les comptes sender/courier/passenger/driver/customer review sont authentifiés séparément
par DiddiFreeID et leurs JWT restent courts.

Le driver ne doit jamais :

- modifier directement une base métier ;
- appeler une route admin ou une route de bypass ;
- injecter un statut final ;
- réutiliser un refresh token permanent dans les logs ou artefacts CI.

