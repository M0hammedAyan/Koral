# 🚨 DO NOT BREAK - CRITICAL SYSTEMS MANIFEST

**ATTENTION:** Modifying these components will break production observability.

---

## 🛑 NEVER MODIFY WITHOUT EXTENSIVE TESTING

### 1. Frontend Dashboard Component

**File:** `frontend/src/pages/Dashboard.tsx`

**Why:** This is the user-facing incident visibility. Breakage = users see no alerts.

**What NOT to do:**
- ❌ Change WebSocket message handling
- ❌ Remove chart components
- ❌ Modify incident list rendering
- ❌ Change timestamp formatting (breaks sorting)

**What's OK:**
- ✅ Add new UI panels (ADD, don't REPLACE)
- ✅ Add new charts
- ✅ Add new incident filters
- ✅ Improve styling (CSS only)

**Test before merging:**
```bash
# In staging environment
# 1. Open dashboard
# 2. Trigger incident from test pod
# 3. Verify appears in <5 seconds
# 4. Verify charts update
# 5. Click incident details
# 6. Verify drill-down works
```

---

### 2. Backend Processor Service

**File:** `backend/services/processor.py`

**Why:** This is the critical anomaly → incident flow. Breakage = incidents never created.

**What NOT to do:**
- ❌ Change anomaly schema (fields: timestamp, pod, metric, value, z_score, is_anomaly)
- ❌ Remove correlation engine call
- ❌ Change incident cache structure
- ❌ Modify WebSocket broadcast logic

**What's OK:**
- ✅ Add new async processing steps
- ✅ Add new incident fields (backwards-compatible)
- ✅ Add new database queries
- ✅ Add new logging

**Before committing:**
```python
# ALWAYS verify this still works:
async def test_anomaly_to_incident():
    # 1. POST /anomalies with test data
    # 2. Verify correlation engine called
    # 3. Verify incident in database
    # 4. Verify WebSocket message sent
    pass
```

---

### 3. Correlation Engine RCA Logic

**File:** `correlation-engine/ai_core/rca.py`

**Why:** This determines incident severity. Wrong RCA = wrong alerts.

**What NOT to do:**
- ❌ Change root cause categories
- ❌ Change severity thresholds (z-score limits)
- ❌ Remove metric-to-cause mappings

**What's OK:**
- ✅ Add NEW root cause categories
- ✅ Improve confidence scoring
- ✅ Add new metrics to existing categories
- ✅ Add evidence reasoning

**Version control:**
```
# Tag versions when changing RCA logic
# So incidents can be re-analyzed with old/new engine
v2.0: Original 9 categories
v2.1: Added network category
v2.2: Improved confidence scoring
```

---

### 4. WebSocket Manager

**File:** `backend/websocket/manager.py`

**Why:** This broadcasts real-time updates. Breakage = static dashboard, no live updates.

**What NOT to do:**
- ❌ Change message format
- ❌ Remove disconnect cleanup
- ❌ Change connection state tracking
- ❌ Break broadcast loop

**What's OK:**
- ✅ Add connection metrics
- ✅ Improve error handling
- ✅ Add connection logging
- ✅ Add rate limiting

**Critical test:**
```python
# 1. Connect 5 WebSocket clients
# 2. Broadcast 1000 messages
# 3. Verify all clients receive all
# 4. Disconnect clients
# 5. Verify cleanup (no memory leak)
```

---

### 5. Database Schema (Existing Tables)

**File:** `backend/database.py`

**Tables to NEVER change:**
- `incidents` ← Schema locked
- `anomalies` ← Schema locked
- `fix_history` ← Schema locked
- `graph_nodes` ← Schema locked
- `graph_edges` ← Schema locked

**What NOT to do:**
- ❌ Drop columns
- ❌ Rename columns
- ❌ Change column types
- ❌ Add NOT NULL constraints to existing columns

**What's OK:**
- ✅ ADD new columns (nullable, defaults)
- ✅ Create NEW tables
- ✅ Create new indexes
- ✅ Add stored procedures

**Migration template:**
```sql
-- SAFE: Add new column
ALTER TABLE incidents ADD COLUMN ai_model TEXT DEFAULT '';

-- UNSAFE: Drop column
ALTER TABLE incidents DROP COLUMN ai_model;

-- UNSAFE: Change type
ALTER TABLE incidents ALTER COLUMN timestamp TYPE FLOAT;

-- SAFE: Add constraint to new column
ALTER TABLE incidents ADD CONSTRAINT check_severity 
  CHECK (severity IN ('critical', 'high', 'medium', 'low'));
```

---

### 6. Agent Base Class

**File:** `agents/base_agent.py`

**Why:** All agents extend this. Breakage = all metric collection fails.

**What NOT to do:**
- ❌ Change Z-score calculation
- ❌ Remove metric posting to backend
- ❌ Change payload format
- ❌ Remove health check endpoint

**What's OK:**
- ✅ Add new Prometheus gauges
- ✅ Add new metrics methods
- ✅ Improve error handling
- ✅ Add performance optimizations

**Backward compatibility check:**
```python
def test_agent_output_format():
    agent = CpuAgent()
    payload = agent._build_payload(value=45.2, z=3.5)
    
    # MUST have all these fields
    assert "timestamp" in payload
    assert "pod" in payload
    assert "metric" in payload
    assert "value" in payload
    assert "z_score" in payload
    assert "is_anomaly" in payload
```

---

### 7. API Authentication

**File:** `backend/auth.py`

**Why:** This controls access. Breakage = system open to anyone.

**What NOT to do:**
- ❌ Disable JWT validation
- ❌ Accept "null" tokens
- ❌ Skip API key checks
- ❌ Hardcode credentials

**What's OK:**
- ✅ Add new auth methods
- ✅ Add token refresh
- ✅ Add MFA support
- ✅ Add audit logging

**Security test:**
```python
def test_auth_enforced():
    # Request WITHOUT API key
    r = requests.get("http://backend:8000/incidents")
    assert r.status_code == 401  # Must reject
    
    # Request WITH invalid key
    r = requests.get("http://backend:8000/incidents", 
                    headers={"X-API-Key": "wrong"})
    assert r.status_code == 403  # Must reject
    
    # Request WITH valid key
    r = requests.get("http://backend:8000/incidents",
                    headers={"X-API-Key": os.getenv("API_KEY")})
    assert r.status_code == 200  # Must accept
```

---

### 8. Kubernetes Deployment Manifest

**File:** `k8s/koral-deployment.yaml`

**Why:** This controls production runtime. Breakage = rolling update failure.

**What NOT to do:**
- ❌ Change health check paths
- ❌ Remove resource limits
- ❌ Change security context
- ❌ Modify rolling update strategy

**What's OK:**
- ✅ Increase resource requests
- ✅ Add new environment variables
- ✅ Add new volume mounts
- ✅ Change replica count

**Before deploying:**
```bash
# 1. Test in minikube
kubectl apply -f k8s/koral-deployment.yaml --dry-run=client

# 2. Verify rollout strategy
kubectl describe deployment backend -n koral-system

# 3. Check health probes
kubectl get pods -n koral-system -o wide
```

---

## 📋 IMPACT ASSESSMENT TEMPLATE

Before modifying any critical component, answer:

```
Proposed Change: [What are you changing?]

Why: [What problem does this solve?]

Affected Components:
  - [ ] Frontend
  - [ ] Backend API
  - [ ] Database
  - [ ] Agents
  - [ ] WebSocket

Risk Level:
  - [ ] 🟢 LOW (add-only, no breaking)
  - [ ] 🟡 MEDIUM (existing field changed)
  - [ ] 🔴 HIGH (schema/API change)

Test Plan:
  1. [Unit test to add]
  2. [Integration test to add]
  3. [Manual test in staging]

Rollback Plan:
  - [How will we revert if it fails?]

Sign-off:
  - [ ] Code review approved
  - [ ] All tests passing
  - [ ] Staging verified
  - [ ] Team lead approved
```

---

## 🔍 PRE-COMMIT CHECKLIST

Run BEFORE merging any changes:

```bash
# 1. All tests pass
pytest tests/ -v

# 2. No syntax errors
python -m py_compile backend/*.py backend/routes/*.py backend/services/*.py

# 3. No breaking changes to API
# Review: backend/routes/*.py
#   - GET endpoints unchanged
#   - POST endpoints backwards compatible
#   - Removed endpoints? NO!

# 4. No breaking changes to database
# Review: backend/database.py
#   - Existing tables modified? YES → migration needed
#   - Old columns removed? NO!
#   - Schema version updated? YES

# 5. Docker builds
docker build -f backend/Dockerfile -t koral-backend:test .
docker build -f correlation-engine/Dockerfile -t koral-correlation:test .
docker build -f ai_engine/Dockerfile -t koral-ai:test .

# 6. Kubernetes manifests valid
kubectl apply -f k8s/ --dry-run=client -o yaml > /dev/null

# 7. No sensitive data in commit
git diff --cached | grep -E "(password|key|secret|token)" && echo "FAIL: secrets detected" && exit 1

# 8. Changes documented
# - CHANGELOG updated
# - README updated if needed
# - Comments added to complex logic
```

---

## 🚨 EMERGENCY SHUTDOWN

If critical component is broken in production:

```bash
# 1. IMMEDIATELY revert the commit
git revert HEAD

# 2. Deploy previous version
kubectl rollout undo deployment/backend -n koral-system

# 3. Verify system recovering
kubectl get pods -n koral-system
curl http://localhost:8000/health

# 4. Post-mortem
# - What broke?
# - Why did tests miss it?
# - How to prevent next time?
```

---

## 📊 System Health Indicators

Check these DAILY in production:

```python
# 1. Incident rate
SELECT COUNT(*) FROM incidents WHERE created_at > NOW() - 1h;
# Expected: 0-10/hour (depending on workload)
# Concerning: >50/hour (detector broken) or 0/hour (no anomalies)

# 2. WebSocket connections
SELECT COUNT(*) FROM connections WHERE status='active';
# Expected: 1-5 (active users)
# Concerning: 0 (frontend offline) or 1000+ (leak)

# 3. API latency
SELECT AVG(duration_ms) FROM request_log WHERE created_at > NOW() - 1h;
# Expected: <100ms
# Concerning: >500ms (timeout risk)

# 4. Error rate
SELECT COUNT(*) FROM request_log WHERE status_code >= 500;
# Expected: 0
# Concerning: >1/hour (system unstable)

# 5. Database size
SELECT pg_size_pretty(pg_database_size('koral'));
# Expected: 100MB-1GB
# Concerning: >5GB (retention policy broken)
```

---

## ✅ VERIFICATION CHECKLIST

After ANY change to critical components:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing in staging
- [ ] Dashboard loads without errors
- [ ] Incidents created successfully
- [ ] WebSocket updates in real-time
- [ ] Emails sent for critical incidents
- [ ] Fix tracking works
- [ ] Prometheus metrics exported
- [ ] Health checks respond
- [ ] Database queries fast (<100ms)
- [ ] No memory leaks (after 1 hour)
- [ ] No CPU spikes
- [ ] Logs clean (no error spam)

---

## 📞 WHO TO CONTACT

**If you broke something:**
1. Stop. Don't deploy further.
2. Revert the commit immediately.
3. Post in #incidents channel.
4. Create a post-mortem.
5. Review this document.

**Questions about what's critical:**
→ Read [SYSTEM_AUDIT_COMPLETE.md](../SYSTEM_AUDIT_COMPLETE.md)

**Questions about implementation:**
→ See specific component in audit report

---

## 🎓 REMEMBER

> **"We move fast by moving carefully. A broken production system is 1000x slower than careful implementation."**

- When in doubt: ASK
- Always test: IN STAGING FIRST
- Never rush: Autonomous systems need caution
- Document everything: Future you will thank you
- Keep humans in loop: For critical changes

---

*Last Updated: May 9, 2026*  
*Status: ACTIVE PRODUCTION PROTECTION*  
*Print this and keep on your desk.*
