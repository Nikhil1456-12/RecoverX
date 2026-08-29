# RecoverX: AI Revenue Recovery Twin

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Active%20(HTTPS)-success?style=for-the-badge&logo=cloudflare)](https://crm-ease-permission-weblog.trycloudflare.com)
[![API Docs](https://img.shields.io/badge/Swagger%20API%20Docs-Interactive-blue?style=for-the-badge&logo=fastapi)](https://crm-ease-permission-weblog.trycloudflare.com/docs)
[![Pitch Video](https://img.shields.io/badge/5--Min%20Pitch-Interactive%20Player-purple?style=for-the-badge&logo=youtube)](https://crm-ease-permission-weblog.trycloudflare.com/pitch.html)
[![Tests](https://img.shields.io/badge/Tests-32%2F32%20Passed%20(100%25)-brightgreen?style=for-the-badge)](https://github.com/Nikhil1456-12/RecoverX)

> **Razorpay AI Builder Track 3 — AI Revenue Recovery**

---

## 🌐 Public Live Links

| Destination | Live URL | Description |
|---|---|---|
| 🖥️ **Live Web Platform** | [**https://crm-ease-permission-weblog.trycloudflare.com**](https://crm-ease-permission-weblog.trycloudflare.com) | Full React 18 Fintech Dashboard, What-If Lab, Experiment Lab & Leakage DNA |
| 📖 **Interactive API Docs** | [**https://crm-ease-permission-weblog.trycloudflare.com/docs**](https://crm-ease-permission-weblog.trycloudflare.com/docs) | Swagger UI testing all 28 FastAPI REST endpoints |
| 🎬 **5-Min Pitch Simulator** | [**https://crm-ease-permission-weblog.trycloudflare.com/pitch.html**](https://crm-ease-permission-weblog.trycloudflare.com/pitch.html) | Self-running pitch presentation with synthesized voiceover & live animations |
| 🩺 **Service Health Check** | [**https://crm-ease-permission-weblog.trycloudflare.com/health**](https://crm-ease-permission-weblog.trycloudflare.com/health) | Real-time health monitor returning `{"status": "healthy", "demo_mode": true}` |

---

## Executive Summary & Core Value Proposition
RecoverX is a next-generation AI-powered revenue recovery system that employs personalized "Recovery Twins" and counterfactual simulation to optimize the recovery of failed payments.

## The Differentiation: Counterfactual Recovery Twin vs Naive Retries / Generic Spam
Traditional recovery systems use naive retries or generic dunning sequences. RecoverX builds a Digital Twin for each failed transaction and simulates counterfactual actions to determine the optimal recovery strategy without causing customer friction or fatigue.

## The Core Formula: Expected Net Recovery Optimization
$$ \text{ENR} = P_{\text{rec}} \times \text{Amt} - \text{Cost} - \text{FrictionCost} $$

## 10 Key Merchant Capabilities
1. Instant Failure Ingestion
2. Intelligent Root Cause Analysis
3. Customer Persona Building
4. Dynamic Policy Evaluation
5. Omnichannel Recovery Execution
6. Friction Cost Minimization
7. Idempotent Action Safeguards
8. DND & Cooldown Compliance
9. Real-time Observation & Adaptation
10. Comprehensive Audit Trail

## Architecture Overview & System Flow
Please see `docs/architecture.md` for full architectural details and Mermaid diagrams.

## Tech Stack
- FastAPI
- React 18
- Vite
- Tailwind CSS v4
- Recharts
- XGBoost
- Scikit-learn
- SQLAlchemy 2.0 Async
- Docker

## Quickstart Guide
```bash
git clone <repo>
cd brave-borg
docker compose up --build
```
Or locally:
```bash
make install
make run
```

## Demo Walkthrough Guide
1. **Initialize System**: Setup the application and log into the admin dashboard.
2. **Setup Razorpay Integration**: Input test API keys for Razorpay Sandbox.
3. **Trigger Webhook**: Simulate a payment failure from Razorpay Sandbox.
4. **View Failure Ingestion**: Observe the new failure in the "Recent Failures" table.
5. **Inspect Diagnostics**: See the RootCauseAgent classification.
6. **Recovery Twin Genesis**: View the profile initialization for the specific customer.
7. **Simulate Counterfactuals**: Watch the CounterfactualSimulationAgent evaluate different messaging sequences.
8. **Analyze ENR**: Review the Expected Net Recovery scores for the simulated actions.
9. **Observe Guardrail Triggers**: Attempt a disallowed action and view the PolicyAgent blocking it.
10. **Action Selection**: The system selects the optimal action with the highest ENR.
11. **Execution via API**: See the action sent back out via the Razorpay/Communication adapter.
12. **Audit Trail Review**: Open the immutable log of the event sequence.
13. **Customer Interaction**: Simulate the customer clicking the payment link.
14. **State Transition**: Watch the state update from `EXECUTING` to `WAITING` to `OBSERVING`.
15. **Successful Payment**: Trigger a success webhook from Razorpay.
16. **Recovery Validation**: Observe the system update to `RECOVERED` state.
17. **Evaluation Update**: View the RecoveryEvaluationAgent update its success metrics.
18. **Escalation Case**: Simulate a second failure and observe escalation to `ESCALATION` queue.
19. **Dashboard Analytics**: Review aggregate metrics for recovery rate and uplift.
20. **Finish Demo**: Shut down local environment.

## API Reference
- `POST /api/v1/payments/webhook` - Ingest failed payment
- `GET /api/v1/recovery/status/{id}` - Check twin status
- `POST /api/v1/recovery/simulate` - Run counterfactual analysis

## ML Training & Synthetic Dataset Architecture
Models are trained on synthetic but highly realistic transactional data modeling various failure modes, customer demographics, and historic behaviors to accurately predict probability of recovery.

## Policy Guardrails & Deterministic Safety Rules
- Channel Allowlist
- Max Retry Limit
- Cooldown Timers
- Daily Budget Constraints
- Idempotency Safeguards

## Razorpay Integration & Webhook Handling
Supports live sandbox and mock demo modes for seamless integration.

## Evaluation Metrics & Benchmark Uplift
Achieves a simulated **+36.5% Recovery Uplift** over naive scheduled retries by dynamically minimizing friction costs.

## Testing & Verification Guide
Run `pytest` to execute the full suite of unit and integration tests.

## Security & Compliance
No secrets in frontend, idempotent actions, DND compliance, immutable audit trails.

## Limitations & Future Roadmap
- Expanding to more channels (e.g., WhatsApp, Voice)
- Real-time model fine-tuning with reinforcement learning
- Advanced integration with external CRMs
