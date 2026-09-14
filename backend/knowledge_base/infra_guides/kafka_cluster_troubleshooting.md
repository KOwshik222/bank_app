# Kafka Cluster & Consumer Lag — Troubleshooting Guide

## Symptoms
- Transaction events delayed in processing
- Consumer group lag exceeding 50,000 messages
- Under-replicated partitions warning in cluster metrics
- Message delivery timeouts in Payment and Notification services

## Root Causes
1. Consumer group rebalance storm caused by slow message processing
2. Broker node disk space exhausted (>95%)
3. Network partition between broker nodes and Kubernetes cluster
4. Uncaught poison pill message causing consumer crash loop

## Resolution Actions
1. Inspect consumer lag: `kafka-consumer-groups.sh --describe --group payment-workers`
2. Restart stalled consumer pods
3. Increase partitions and scale consumer replicas
4. Route poison pill message to Dead Letter Queue (DLQ)
