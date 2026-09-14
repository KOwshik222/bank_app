# Enterprise Cloud Deployment Architecture

This document details the production cloud deployment architecture for the **BankOps AI Incident Resolution & Root Cause Analysis Platform** within regulated banking infrastructure (PCI-DSS, SOC 2 Type II, ISO 27001 compliant).

---

## 1. High-Level Architecture Topology

```
                   +------------------------------------+
                   |       Internet / VPN Gateway       |
                   +-----------------+------------------+
                                     |
                         [AWS WAF / Azure FrontDoor]
                                     |
                        +------------v------------+
                        |  Public / DMZ Ingress   |
                        |   ALB (TLS 1.3 Term.)   |
                        +------------+------------+
                                     |
                 +-------------------v-------------------+
                 |           Private App Subnet          |
                 |                                       |
                 |   +-------------------------------+   |
                 |   |  EKS / AKS Cluster (BankOps)  |   |
                 |   |  - BankOps FastAPI Pods (HPA) |   |
                 |   |  - Real-time SSE Steppers     |   |
                 |   |  - Envoy Sidecar Proxies      |   |
                 |   +---------------+---------------+   |
                 +-------------------|-------------------+
                                     |
        +----------------------------+----------------------------+
        |                                                         |
+-------v-------+                                         +-------v-------+
| Isolated Data |                                         | AI/ML Runtime |
|    Subnet     |                                         |    Subnet     |
|               |                                         |               |
| - Amazon RDS  |                                         | - Qdrant Clust|
|   PostgreSQL  |                                         |   (Distributed|
|   Multi-AZ    |                                         |   Vector DB)  |
| - KMS Encrypt |                                         | - vLLM /      |
|               |                                         |   Self-hosted |
|               |                                         |   Llama 3.1   |
+---------------+                                         +---------------+
```

---

## 2. Infrastructure Components

### 2.1 Compute Tier (Kubernetes / EKS)
- **Deployment**: Multi-replica (minimum 2 pods across different AZs) with Horizontal Pod Autoscaler (HPA) triggered at 70% CPU or 50 req/sec.
- **Node Groups**: Dedicated spot/on-demand Linux worker nodes configured with strict IMDSv2 metadata tokens and no public IPv4 addresses.
- **Network Policies**: Calico or AWS VPC CNI NetworkPolicies enforcing zero-trust egress; pods can only connect to the database, vector store, and monitoring agents.

### 2.2 Vector Database (Qdrant Cloud / Distributed Qdrant)
- Clustered deployment with 3 replicas for high availability and consensus across Availability Zones.
- Persistent NVMe SSD volumes (AWS io2 or gp3) storing 384-dimensional dense semantic vectors.
- TLS-encrypted gRPC / REST communication on ports 6334/6333.

### 2.3 Relational Database (Amazon RDS PostgreSQL / Azure Database)
- Multi-AZ deployment with synchronous standby replication and automated point-in-time recovery (PITR) with 35-day retention.
- Storage encrypted with customer-managed AWS KMS keys (CMK) with automated annual rotation.
- Connection pooling managed via PgBouncer / RDS Proxy to prevent connection starvation during incident spikes.

### 2.4 Model Serving Infrastructure
- **Development / On-Premise**: Local Ollama container serving `llama3.2` and `nomic-embed-text`.
- **Enterprise Cloud Production**: Dedicated GPU instances (e.g. AWS `g5.xlarge` with NVIDIA A10G) running **vLLM** or **Triton Inference Server** with OpenAI-compatible endpoints, eliminating third-party data exfiltration risks.

---

## 3. Banking Security & Compliance Controls

| Control Area | Implementation |
|---|---|
| **Zero-Trust Network** | All intra-cluster communication encrypted via mutual TLS (mTLS) with Istio/Linkerd. Private endpoints only (no public IPs on workloads). |
| **Secrets Management** | Zero hardcoded credentials. Secrets fetched dynamically from **HashiCorp Vault** or **AWS Secrets Manager** via External Secrets Operator (ESO). |
| **Audit Immutability** | Audit log entries stream to Amazon S3 Glacier Vault Lock / Azure Immutable Blob with WORM (Write Once, Read Many) compliance. |
| **RBAC & Approval Gate** | Multi-Factor Authentication (MFA) required for incident approval; strict RBAC separation between `SUPPORT_ENGINEER` and `INCIDENT_MANAGER` / `ADMIN`. |
| **Data Masking** | PII and PCI account numbers are pseudonymized and masked before vectorization or LLM prompt construction. |
