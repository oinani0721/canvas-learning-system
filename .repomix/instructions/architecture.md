# Architecture Analysis Instructions

Analyze this codebase and answer:

1. **Layer separation**: Is the architecture properly layered (API → Service → Repository → Database)? Any layer violations?
2. **Dependency direction**: Do dependencies flow correctly? Any circular dependencies?
3. **Module cohesion**: Are related functionalities grouped together? Any god modules?
4. **Interface design**: Are API contracts clean? Any leaky abstractions?
5. **Data flow**: How does data flow from frontend to backend to database? Any bottlenecks?
6. **Error handling**: Is error handling consistent across layers?
7. **Community comparison**: How does this architecture compare to best practices for similar projects (Tauri + React + FastAPI)?

For each issue found, provide:
- Severity (Critical / High / Medium / Low)
- Specific file paths and code references
- Recommended fix with code examples from community best practices
