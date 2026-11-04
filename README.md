# diddi-review-runner

Service indépendant d’orchestration des parcours review DiddiGo, DiddiSend et DiddiFood.

## État de l’implémentation

Le bootstrap FastAPI, l’authentification opérationnelle, les contrats d’acteurs, les
adapters HTTP, la validation des scénarios, le retry contrôlé et la frontière Redis Streams
sont en place. La persistance actuelle est en mémoire pour permettre le vertical slice ;
le worker devra relier `RedisRunStream` à un repository durable après validation des URLs et
contrats d’environnement.

Le runner utilise les JWT utilisateur normaux. Il ne possède aucune route admin, aucun
accès base métier et ne peut pas exécuter la notation restaurant DiddiFood : aucun contrat
métier correspondant n’existe dans le dépôt audité.

```powershell
uv sync --group dev
uv run pytest -q
uvicorn app.api.main:app --reload
alembic upgrade head
```

## Checklist de livraison

### Terminé localement

- API FastAPI protégée par credential de service
- Validation JWT review via JWKS
- Scénarios et rôles autorisés
- Adapters HTTP séparés
- Exécution séquentielle idempotente
- Redis Streams, consumer groups et récupération des messages pending
- Modèles SQLAlchemy et migration Alembic
- Correlation ID et tests unitaires

### Dépendances externes restantes

- Brancher le repository SQL dans le bootstrap de production.
- Fournir les URLs, scopes, issuer/audience et le mécanisme réel de résolution des JWT.
- Exécuter les tests d’intégration contre Redis/PostgreSQL et les APIs métier.
- Fournir le driver de session Google Play unique pour l’E2E.
- Fournir le contrat de notation restaurant DiddiFood, ou retirer ce rôle.

Ces éléments dépendent d’environnements et de contrats externes absents de ce dépôt ; ils
ne peuvent pas être simulés honnêtement comme une intégration terminée.
# diddi-review-worker
