# Coreason Agent Protocol (CAP)

The Coreason Agent Protocol defines the standard HTTP interface that any Coreason Agent must expose. This ensures interoperability regardless of the hosting environment (Lambda, K8s, Local).

## Endpoint 1: `POST /assist`

Invoke the agent to process a request.

**Headers:**
* `Content-Type: application/json`

**Body:** `ServiceRequest` Schema
* `request_id`: UUID (Unique ID for this HTTP transaction)
* `context`: SessionContext (Strict separation of Who is asking from What they are asking)
* `payload`: AgentRequest (The actual query, files, or multi-modal input)

### Responses

**Streaming Response (Default)**
* **Header:** `Content-Type: text/event-stream`
* **Format:** Sequence of `StreamPacket` (defined in `definitions.presentation`)

**Synchronous Response**
* **Header:** `Content-Type: application/json`
* **Format:** `ServiceResponse`
    * `request_id`: UUID (Echoes the request)
    * `created_at`: datetime
    * `output`: Dict[str, Any] (The final result)
    * `metrics`: Optional[Dict[str, Any]] (Execution stats like token count, latency)

## Endpoint 2: `GET /health`

Check the health status of the agent.

**Format:** `HealthCheckResponse`
* `status`: Literal["ok", "degraded", "maintenance"]
* `agent_id`: UUID
* `version`: str (SemVer)
* `uptime_seconds`: float
