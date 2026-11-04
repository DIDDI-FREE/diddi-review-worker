# Audit réactif des déclencheurs

Audit en lecture seule des OpenAPI staging le 04-11-2026.

## Résultat

Le runner ne contient actuellement aucun détecteur HTTP, webhook, polling loop
ou worker branché sur les API métier. `ReactiveCoordinator` ne fait que décider
à partir d'un événement déjà observé.

## Signaux disponibles

- Go expose `GET /v1/rides` avec `role`, `status` et pagination, ainsi que
  `GET /v1/rides/{ride_id}` et `GET /v1/rides/active/current`.
- Go expose `POST /v1/drivers/online`, mais aucun flux d'événements ; la
  disponibilité peut donc être observée indirectement via les ressources du
  chauffeur, pas sous forme de notification.
- Send expose `GET /v1/courier/offers`, `GET /v1/deliveries/{delivery_id}` et
  `GET /v1/couriers/me/readiness`. Aucun listing consommateur des nouvelles
  livraisons ni webhook métier public n'a été trouvé.
- Food expose `GET /food/v1/restaurants/{restaurant_id}/orders`,
  `GET /food/v1/orders/{order_id}` et le tracking d'une livraison. Aucun listing
  client des nouvelles commandes ni webhook métier public n'a été trouvé.

## Conclusion

Une détection Go par polling est techniquement envisageable avec les comptes
Review associés. Send consommateur et Food consommateur ne disposent pas, dans
les contrats exposés, d'un signal fiable permettant de découvrir une nouvelle
ressource sans connaître son identifiant. Le runner doit donc rester en attente
pour ces cas ; il ne doit pas inventer de mission ni utiliser les routes
`internal`/admin pour contourner ce manque.

Les contrats de progression (matching normal, GPS, PIN, preuves et paiement)
doivent encore être câblés et testés avant toute validation E2E.
