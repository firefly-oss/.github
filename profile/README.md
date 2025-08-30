<h1 align="center">Firefly — Open-Core Banking Platform</h1>

<p align="center">
  <i>Build banks like software products — modern, modular, and open.</i>
</p>

<p align="center">
  <a href="https://getfirefly.io"><img alt="Website" src="https://img.shields.io/badge/website-getfirefly.io-informational?logo=firefox-browser"></a>
  <a href="https://github.com/firefly-oss"><img alt="GitHub Org" src="https://img.shields.io/badge/GitHub-firefly--oss-000?logo=github"></a>
  <a href="#"><img alt="Docs" src="https://img.shields.io/badge/docs-available-6f42c1?logo=readthedocs"></a>
  <a href="#"><img alt="Community" src="https://img.shields.io/badge/community-join_us-0ea5e9?logo=discord"></a>
  <a href="#"><img alt="Security Policy" src="https://img.shields.io/badge/security-policy-16a34a?logo=security"></a>
</p>

---

**Firefly** provides fintech teams and banks an **open-core** foundation to launch and scale financial products—without black boxes or vendor lock-in. Built with **composable architecture**, **cloud-native** baseline, and **transparent by design** principles.

**Core capabilities:** Banking accounts, payments hub, lending services, compliance, risk management, document handling, and comprehensive APIs.

---

## 🧱 Design Tenets

- **API-first** — clean, versioned contracts with SDKs.
- **Event-driven** — decoupled domains with streaming/CDC.
- **Security-led** — least privilege, signed artifacts, SBOMs.
- **Testable by default** — golden datasets, simulators, reproducible envs.
- **Observability everywhere** — tracing, metrics, actionable logs.

---

## 🛠️ Tech Stack (typical)

- **Backend:** Java/Spring Boot 3 (WebFlux), Kotlin or Java
- **Data:** PostgreSQL, Kafka (events/streams)
- **Infra:** Docker, Kubernetes, Helm, GitHub Actions
- **Ops UI:** Angular/React (where applicable)

> Stacks may vary by repo—see each README for specifics.

---

## 🏗️ Architecture Documentation

Firefly follows a **microservices architecture** with clear separation of concerns across multiple layers:

```mermaid
graph TB
    subgraph "Application/Process Layer"
        A1[Core Orchestrator]
        A2[Customer Onboarding]
        A3[Loan Origination Workflow]
        A4[Payment Orchestration]
        A5[Risk Management]
        A6[Regulatory Reporting]
    end
    
    subgraph "Core Banking Services"
        B1[Accounts Management]
        B2[Payment Processing]
        B3[Card Services]
        B4[Ledger Management]
        B5[Payment Hub]
        B6[PSD2/Open Banking]
    end
    
    subgraph "Core Lending Services"
        C1[Loan Origination]
        C2[Loan Servicing]
        C3[Portfolio Management]
        C4[Collections]
        C5[Underwriting]
    end
    
    subgraph "Domain Services"
        D1[Customer Domain]
        D2[Accounts & Payments]
        D3[Product Domain]
        D4[Organization Domain]
        D5[Treasury & Finance]
    end
    
    subgraph "Common Platform Services"
        E1[Customer Management]
        E2[User Management]
        E3[Document Management]
        E4[Notification Service]
        E5[Audit Service]
    end
    
    subgraph "Shared Libraries & Adapters"
        F1[Common Libraries]
        F2[BaaS Adapters]
        F3[Payment Adapters]
        F4[Identity Adapters]
    end
    
    A1 --> B1
    B1 --> D1
    D1 --> E1
    E1 --> F1
```

### 📚 Detailed Layer Documentation

- **[📋 Complete Architecture Overview](docs/architecture.md)** - Platform architecture vision and design principles
- **[🏛️ Core Banking Services](docs/core-banking-services.md)** - Account management, payments, cards, and ledger services
- **[💰 Core Lending Services](docs/core-lending-services.md)** - Loan origination, servicing, portfolio management, and collections
- **[⚙️ Application Services](docs/application-services.md)** - Workflow orchestration and business process automation
- **[🏢 Domain Services](docs/domain-services.md)** - Specialized business domain services and bounded contexts
- **[🛡️ Common Platform Services](docs/common-platform-services.md)** - Shared platform capabilities and cross-cutting concerns
- **[📚 Shared Libraries & Adapters](docs/shared-libraries-adapters.md)** - Reusable components and external system integrations
- **[🏗️ Infrastructure Layer](docs/infrastructure-layer.md)** - Cloud infrastructure, containerization, and operational components

---

## 🚀 Get Started

1. **Explore the repos** → domain services, SDKs, and adapters.
2. **Read the architecture docs** → understand the platform structure and components.
3. **Read each README** → local setup, environment variables, samples.
4. **Run locally** → most services ship `docker-compose` or Helm charts.
5. **Extend** → add adapters (KYC, payments, FX, core hooks).
6. **Contribute** → pick a **Good First Issue** or open a **Discussion**.

---

## 🤝 Contributing

We welcome issues, PRs, and RFCs. Great first contributions include:
- improving quickstarts or docs,
- adding tests or examples for a public API,
- proposing rule/policy examples for the Policy Engine.

Before contributing:
- Review **CONTRIBUTING.md** and **CODE_OF_CONDUCT.md**.
- For security issues, follow **SECURITY.md**.

---

## 🧩 Use Cases You Can Build

- **Neobank / EMI** — multi-currency accounts, cards, payments, fees.
- **Lending / BNPL** — pricing, eligibility, disbursements, collections.
- **Wallets & Programs** — stored value, limits, KYX, compliance workflows.
- **Treasury & FX** — internal ledgering, settlements, reconciliation.

---

## 📍 Quick Links

- 🌐 **Website:** https://getfirefly.io  
- 📚 **Docs:** (coming soon)  
- 🗺️ **Roadmap / Milestones:** (coming soon)
- 🛡️ **Security Policy:** see `SECURITY.md`  
- 💬 **Community:** GitHub Discussions (and chat, if available)

---

## 🏁 Why Firefly

- **Modern core, zero lock-in.**  
- **Composable domains** that evolve with your roadmap.  
- **Production-ready patterns** for compliance, scale, and speed.

> Ship value faster. Don’t reinvent the core.

---

<p align="center">
  <sub>Made with ❤️ by the <b>Firefly</b> community.</sub><br>
  <sub>© 2025 Firefly Software Solutions Inc. Some repositories may offer enterprise add-ons; see individual licenses.</sub>
</p>
