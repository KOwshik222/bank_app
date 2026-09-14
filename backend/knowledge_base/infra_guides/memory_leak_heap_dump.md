# Memory Leak and Heap Dump Analysis — Runbook

## Symptoms
- Process resident memory (RSS) continuously climbs over hours or days
- JVM / Python runtime memory consumption exceeds 85% container limit
- Linux OOM (Out Of Memory) killer terminates service pod (exit code 137)
- Increased Garbage Collection (GC) pauses causing latency spikes

## Diagnostic Steps
1. Capture memory metrics: `ps -aux --sort=-%mem`
2. For Python services, generate memory snapshot via `tracemalloc`
3. Inspect caching mechanisms (unbounded in-memory dictionaries, LRU cache without maxsize)
4. Check database connection object lifecycle (unclosed cursors or connections)

## Remediation Steps
1. Immediate action: Restart service instance to release memory and restore availability
2. Scale service horizontally to distribute memory pressure
3. Apply hotfix setting upper bounds on all in-memory caches
4. Ensure all database connections are closed using context managers (`with` statements)
