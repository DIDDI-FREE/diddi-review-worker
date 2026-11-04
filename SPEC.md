# Spec: diddi-review-runner

Date de référence : 04-11-2026

## Objective

Construire un service Python indépendant qui automatise des parcours Google Play Review
pour DiddiGo, DiddiSend et DiddiFood lorsqu’un seul utilisateur Google est connecté dans
une seule application. Le runner pilote des comptes DiddiFreeID dédiés aux reviews, mais
utilise uniquement les APIs métier existantes et les JWT utilisateur normaux.

Le service doit couvrir les rôles suivants :

- DiddiSend : sender review et courier review ;
- DiddiGo : passenger review et driver review ;
- DiddiFood : customer review, restaurant review et courier review.

Le runner ne contient aucune règle métier de ces produits. Il orchestre des appels
existants, vérifie les contrats de réponse, persiste son propre état et permet de rejouer
une étape sans créer de doublon.

## Non-goals and security boundaries

- Aucun token permanent, compte admin global ou accès direct aux bases métier.
- Aucun bypass KYC/KYV, wallet, disponibilité ou statut final.
- Aucune route spéciale qui force artificiellement un état métier.
- `is_review_account=true` sert uniquement à isoler les données review de la production.
- Les secrets et JWT ne sont jamais écrits en clair dans les logs, événements d’audit ou
  réponses API.

## Assumptions

1. Les APIs des cinq systèmes exposent des endpoints HTTP JSON authentifiés par Bearer JWT.
2. DiddiFreeID fournit un flux d’authentification programmatique pour les comptes de test
   et un endpoint de validation/introspection ou un JWKS exploitable.
3. Redis Streams est disponible pour la file d’exécution ; Redis sert aussi de stockage
   d’état court et de verrou distribué.
4. Un stockage durable SQL (PostgreSQL en production, SQLite possible en test) est
   disponible pour l’état des runs et l’audit.
5. Les identifiants des comptes review et leurs secrets sont fournis par variables
   d’environnement ou un secret manager, jamais par le code source.
6. Les détails exacts des routes métier seront configurés dans les adapters et pourront
   être ajustés sans changer l’orchestrateur.

## Tech Stack

- Python 3.12+
- FastAPI, Pydantic Settings, httpx
- SQLAlchemy 2 + Alembic
- Redis asyncio + Redis Streams
- PyJWT/cryptography pour validation locale si JWKS disponible
- structlog, OpenTelemetry (exporteurs configurables)
- pytest, pytest-asyncio, respx, testcontainers (profil E2E optionnel)
- Ruff, mypy, coverage
- Docker Compose avec runner, PostgreSQL et Redis

## Commands

```text
uv sync --group dev
uv run ruff check .
uv run mypy app
uv run pytest -q
uv run pytest -q -m e2e
docker compose up --build
```

## Project Structure

```text
app/config/          Configuration et validation d’environnement
app/auth/            JWT, sessions d’acteurs et redaction
app/actors/          Modèles de comptes et rôles review
app/scenarios/       Définitions des parcours et étapes
app/adapters/        Clients HTTP vers les systèmes externes
app/persistence/     Modèles SQL, repositories, événements et verrous
app/orchestration/   Worker Streams, machine d’état, retries et idempotence
app/api/             Routes FastAPI, schémas et dépendances
app/observability/   Logs, métriques, traces et correlation IDs
tests/unit/          Tests déterministes des règles locales
tests/integration/   Tests Redis/SQL et contrats adapter
tests/e2e/           Parcours complets contre services simulés ou environnements dédiés
docs/                Contrats, menaces, runbooks et diagrammes
```

## Core contracts

Un `ReviewRun` possède un identifiant, un scénario, un statut (`queued`, `running`,
`succeeded`, `failed`, `cancelled`), un correlation ID et une liste ordonnée de
`StepExecution`. Chaque étape a une clé idempotente déterministe, un timeout, un nombre
de tentatives et un résultat redigé.

Les transitions sont monotones et validées par la machine d’état. Une étape n’est
considérée réussie que si l’adapter reçoit une réponse HTTP et un payload conformes à son
contrat. Les erreurs 401/403, les contrôles métier refusés et les timeouts sont distincts
dans l’audit. Les retries sont limités, avec backoff et jitter ; aucune répétition aveugle
ne doit contourner un refus métier.

Le worker consomme Redis Streams avec consumer groups, acquitte uniquement après
persistance de l’état, et récupère les messages pending après expiration d’un lease.
L’API reste stateless ; elle publie des commandes et lit l’état persistant.

## API initiale

- `GET /health/live` : processus vivant.
- `GET /health/ready` : dépendances Redis/SQL accessibles.
- `POST /v1/runs` : crée un run à partir d’un scénario autorisé et le publie.
- `GET /v1/runs/{run_id}` : état courant et étapes redigées.
- `POST /v1/runs/{run_id}/retry` : relance seulement les étapes retryables échouées.
- `POST /v1/runs/{run_id}/cancel` : demande l’annulation coopérative.

Toutes les routes opérationnelles exigent une authentification de service configurée,
un correlation ID et une validation stricte du scénario. Les endpoints ne permettent
pas de choisir un token arbitraire ni de fournir un JWT dans la requête.

## Testing Strategy

- Unit : transitions d’état, redaction, sélection de rôles, backoff, idempotence et
  validation des claims `is_review_account`.
- Integration : repositories SQL, Redis Streams, leases, consumer groups et adapters
  avec serveurs HTTP simulés.
- E2E : un environnement Docker simulé des cinq APIs, avec comptes review passant les
  contrôles normaux ; vérification qu’un parcours complet ne touche jamais de base métier
  du runner et qu’un retry ne duplique pas une action idempotente.
- Security regression : tokens expirés, mauvais issuer/audience, compte non-review,
  scopes insuffisants, secrets dans logs et injection de scénario.

Objectif initial : couverture >= 85% sur `app/`, 100% sur transitions de statut,
redaction et validation des claims de sécurité.

## Code Style

```python
class ReviewAdapter(Protocol):
    async def execute(self, request: AdapterRequest) -> AdapterResponse: ...


async def run_step(step: Step, *, adapter: ReviewAdapter) -> StepResult:
    response = await adapter.execute(step.request)
    return StepResult.from_response(step.key, response)
```

Types explicites, fonctions courtes, dépendances injectées, pas d’état global mutable,
exceptions métier typées, noms en `snake_case`, modèles Pydantic aux frontières et
formatage Ruff.

## Boundaries

- Always : valider issuer/audience/expiration/scopes, vérifier `is_review_account`,
  redacter les secrets, utiliser des clés idempotentes, journaliser les transitions,
  exécuter les tests avant livraison.
- Ask first : modifier les contrats d’API externes, ajouter une dépendance runtime,
  changer le schéma de persistance, ajouter une route de contournement, modifier le
  pipeline CI/CD ou activer un exporteur externe.
- Never : token permanent, admin global, accès direct aux bases métier, bypass KYC/KYV/
  wallet/disponibilité, secret commité, JWT en clair dans logs ou réponses.

## Success Criteria

1. Le dépôt contient la structure demandée et démarre avec Docker Compose.
2. Le service expose l’API FastAPI et les health checks.
3. Un run est persisté, publié sur Redis Streams, consommé et mis à jour étape par étape.
4. Les adapters DiddiFreeID, DiddiPay, DiddiSend, DiddiGo et DiddiFood sont séparés,
   typés, testables et n’accèdent jamais à une base métier.
5. Les sept rôles review sont modélisés et les scénarios refusent tout acteur non-review.
6. Les retries, leases, annulations et idempotence sont testés.
7. Les tests unitaires, intégration et E2E simulé passent ; les logs sont redigés.
8. La documentation couvre configuration, contrats supposés, menaces, déploiement et
   runbook d’incident.

## Findings from local contract audit

Les dépôts existants confirment les routes de notation suivantes : DiddiGo expose
`POST /{ride_id}/rating`, DiddiSend expose `POST /deliveries/{delivery_id}/rate` et
`POST /courier/deliveries/{delivery_id}/rate`, et DiddiFood expose
`POST /{order_id}/rating` pour le customer. Les backends imposent eux-mêmes la propriété,
le rôle, le statut final et l’unicité.

DiddiFood ne fournit actuellement pas de mutation de notation restaurant. Le courier
rating d’une commande Food est porté par DiddiSend. Le scénario restaurant review doit
donc rester bloqué par contrat jusqu’à fourniture d’un endpoint métier existant ou
retrait explicite de ce rôle du périmètre.

## Open Questions

- Quelles sont les URLs, méthodes, payloads et scopes exacts des APIs DiddiFreeID,
  DiddiPay, DiddiSend, DiddiGo et DiddiFood ?
- Quel fournisseur SQL et quel mode de migration sont imposés en production ?
- Quel mécanisme de secret manager et quel issuer/audience JWT doivent être utilisés ?
- Quels scénarios Google Play Review exacts doivent être livrés en première version,
  notamment l’ordre des actions et les critères de succès métier ?
- Quelle API métier existante doit porter la notation restaurant DiddiFood ?
- Le parcours Google Play est-il piloté via un driver E2E (session Google unique) ou
  via un hook de test déjà disponible dans l’application ?
- L’API opérationnelle est-elle appelée par un CI/CD interne, un scheduler ou un opérateur,
  et quelle authentification de service est attendue ?
