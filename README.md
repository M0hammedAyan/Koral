#  KORAL Brain — Correlation & Root Cause Engine

##  Overview

This module implements the **intelligence layer** of the KORAL system.

It is responsible for:

* Understanding anomalies from agents
* Finding relationships between pods
* Identifying root cause (WHY, not just WHAT)
* Generating incident summaries
* Producing dependency graphs

---

##  What This Module Does

This component acts as the **brain of the system**.

### Pipeline:

```
Anomalies → Correlation → Rules → Incident → Graph
```

### Detailed Flow:

1. **Input Validation**

   * Ensures incoming data follows strict schema

2. **Anomaly Filtering**

   * Uses `is_anomaly = true` from agents
   * No anomaly computation is done here

3. **Correlation Engine**

   * Uses Pearson correlation with time lag
   * Identifies relationships between pods
   * Determines direction (cause → effect)

4. **Rule Engine**

   * Maps metric combinations to root causes
   * Example:

     * PVC I/O + CPU → Storage issue
     * Memory + OOM → Memory leak

5. **Incident Builder**

   * Generates final structured output
   * Includes root cause + confidence

6. **Dependency Graph**

   * Builds pod relationships for visualization

---

##  Input Data Contract (STRICT)

All incoming data must follow this schema:

```json
{
  "timestamp": 1710000000,
  "pod": "pod-A",
  "namespace": "koral-system",
  "metric": "cpu",
  "value": 85.2,
  "unit": "percent",
  "z_score": 3.1,
  "is_anomaly": true,
  "window_size": 300,
  "source": "cpu-agent"
}
```

###  Rules:

* All fields are **mandatory**
* `is_anomaly` must be computed by agents
* Brain does NOT compute z-score

---

##  Output

### 🔹 Incident Output

```json
{
  "incident_id": "INC-001",
  "root_cause": "Storage I/O spike caused CPU overload",
  "confidence": 0.76,
  "affected_pods": ["koral-system/pod-A", "koral-system/pod-B"]
}
```

---

### 🔹 Graph Output

```json
{
  "nodes": ["koral-system/pod-A", "koral-system/pod-B"],
  "edges": [
    {
      "source": "koral-system/pod-A",
      "target": "koral-system/pod-B",
      "correlation": 1.0,
      "lag": 1
    }
  ]
}
```

---

##  Design Principles

* **Separation of Concerns**

  * Agents → detect anomalies
  * Brain → analyze relationships

* **Explainability**

  * Uses rule-based logic (no black-box ML)

* **Scalability**

  * Works with multiple pods dynamically

* **Deterministic Behavior**

  * No randomness in outputs

---

##  Integration Guide

###  Member 3 (Backend & Agents)

Must:

* Send anomaly data to backend
* Ensure data follows schema exactly
* Compute:

  * `z_score`
  * `is_anomaly`

Brain expects:

```
POST /anomalies → JSON list
```

---

###  Member 2 (DevOps)

Must:

* Deploy this module as a service
* Ensure:

  * backend → brain communication
  * containerization

---

###  Member 4 (Frontend)

Consumes:

* `/incidents`
* `/graph`

Used for:

* Dashboard
* Dependency visualization (D3.js)

---

###  Member 5 (Evaluation)

Uses:

* Incident output
* Graph output

To evaluate:

* Precision
* Recall
* False positives
* Detection latency

---

##  Important Notes

* Correlation requires **multiple data points**
* Sparse data → no edges (expected behavior)
* Threshold used:

  ```
  correlation > 0.85
  ```

---

##  How to Run

```bash
python run.py
```

---

##  Summary

This module transforms:

```
Raw anomalies → Meaningful insights
```

It is responsible for:

* Understanding system behavior
* Explaining failures
* Enabling real-time observability

---

##  Key Insight

> KORAL does not just detect anomalies —
> it explains *why they happen*.
