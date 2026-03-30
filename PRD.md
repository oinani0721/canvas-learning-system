# Test PRD — Ralph Runner Verification

## Epic 1: Health Check Endpoint Test

### Feature 1.1: Add /api/v1/ping endpoint
- Add a simple GET endpoint at `/api/v1/ping` that returns `{"status": "pong"}`
- Add a unit test that verifies the endpoint returns 200 with correct JSON

### Acceptance Criteria
- GET /api/v1/ping returns 200
- Response body is `{"status": "pong"}`
- Unit test passes
