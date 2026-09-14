# Kafka Consumer Lag & Processing Backlog — Runbook

## Symptoms
- Transactions taking more than 15 seconds to settle
- Kafka consumer group lag increasing steadily across partitions
- Out of memory warnings in transaction-service worker threads
- Prometheus metric `kafka_consumer_lag_records` > 10,000

## Diagnosis
1. Identify lag distribution:
   ```bash
   kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group transaction-processors
   ```
2. Check if a single partition is blocked on a poison pill message.
3. Check worker CPU and database lock wait times.

## Remediation
1. **Scale Consumers**: Scale the deployment replicas to match partition count (e.g. 10 consumers for 10 partitions).
2. **Skip Poison Pill**: Forward the unparseable offset to the dead-letter-topic (`dlq.transactions`).
3. **Restart Workers**: In case of consumer thread deadlock, restart consumer pods with rolling update.
