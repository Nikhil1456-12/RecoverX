# RecoverX AI Revenue Recovery Twin Architecture

## 1. High-Level System Architecture Diagram

```mermaid
graph TD
    UI[Frontend: React 18, Vite, Tailwind CSS, Recharts]
    API[REST API: FastAPI, SQLAlchemy Async]
    Agents[Multi-Agent Swarm: LangChain / Custom]
    ML[ML Pipeline: XGBoost, Scikit-learn]
    DB[(Data Layer: SQLite / PostgreSQL)]
    Redis[(Redis Cache)]
    PG[Payment Gateway Adapters: Razorpay]

    UI <-->|HTTP/REST| API
    API <--> Agents
    Agents <--> ML
    API <--> DB
    API <--> Redis
    API <--> PG
```

## 2. End-to-End Data Flow Diagram

```mermaid
graph LR
    Ingest[Payment Failure Ingestion] --> Diagnosis[Diagnosis]
    Diagnosis --> TwinCreation[Twin Creation]
    TwinCreation --> Counterfactual[Counterfactual Simulation]
    Counterfactual --> PolicyEval[Policy Evaluation]
    PolicyEval --> Execution[Execution]
    Execution --> Observation[Observation]
    Observation --> Learning[Learning]
```

## 3. Recovery State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> DETECTED
    DETECTED --> DIAGNOSED
    DIAGNOSED --> SIMULATING
    SIMULATING --> POLICY_CHECK
    POLICY_CHECK --> ACTION_SELECTED
    ACTION_SELECTED --> EXECUTING
    EXECUTING --> WAITING
    WAITING --> OBSERVING
    OBSERVING --> RECOVERED
    OBSERVING --> RETRY_PLANNING
    OBSERVING --> ESCALATION
    OBSERVING --> STOPPED
    RETRY_PLANNING --> SIMULATING
    RECOVERED --> [*]
    ESCALATION --> [*]
    STOPPED --> [*]
```

## 4. Counterfactual Engine Architecture Diagram

**Expected Net Recovery Optimization Formula:**
$$ \text{ENR} = P_{\text{rec}} \times \text{Amt} - \text{Cost} - \text{FrictionCost} $$

```mermaid
graph TD
    FV[Feature Vector Assembly] --> MCS[Multi-Action Counterfactual Simulation]
    MCS --> ENR[Expected Net Recovery Optimization]
```

## 5. Deterministic Policy & Safety Guardrails Diagram

```mermaid
graph TD
    PolicyCheck[Policy Evaluation]
    PolicyCheck --> ChannelAllowlist[Channel Allowlist Check]
    PolicyCheck --> MaxRetryLimit[Max Retry Limit Check]
    PolicyCheck --> CooldownTimer[Cooldown Timer Check]
    PolicyCheck --> CustAttemptLimit[Customer Attempt Limit Check]
    PolicyCheck --> DNDCheck[DND Check]
    PolicyCheck --> DailyBudget[Daily Budget Knapsack Optimizer]
    PolicyCheck --> AutoRecoveryCeil[Auto-Recovery Amount Ceiling]
    PolicyCheck --> Idempotency[Idempotency Guard]
```

## 6. Multi-Agent Orchestration & Audit Trail

```mermaid
graph TD
    Swarm[Multi-Agent Swarm Orchestrator]
    Swarm --> RRA[RevenueRiskAgent]
    Swarm --> RCA[RootCauseAgent]
    Swarm --> RTA[RecoveryTwinAgent]
    Swarm --> CSA[CounterfactualSimulationAgent]
    Swarm --> RPA[RecoveryPolicyAgent]
    Swarm --> CA[CommunicationAgent]
    Swarm --> AE[ActionExecutor]
    Swarm --> REA[RecoveryEvaluationAgent]
    Swarm --> AuditTrail[(Immutable Audit Trail)]
```

## 7. Deployment & DevOps Architecture Diagram

```mermaid
graph TD
    NGINX[Nginx Reverse Proxy]
    DockerCompose[Docker Compose]
    NGINX --> DockerCompose
    DockerCompose --> FastAPI[FastAPI Backend]
    DockerCompose --> React[React Frontend]
    DockerCompose --> DB[(SQLite/PostgreSQL)]
    DockerCompose --> Redis[(Redis)]
    FastAPI --> ModelStore[Model Store]
```
