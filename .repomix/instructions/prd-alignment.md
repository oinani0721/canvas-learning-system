# PRD vs Code Alignment Analysis Instructions

This pack contains both PRD documents and source code. Analyze alignment:

1. **Feature coverage**: For each PRD requirement, does corresponding code exist? List unimplemented features.
2. **Architecture match**: Does the code structure match the architecture described in the PRD?
3. **API contracts**: Do the actual API endpoints match what the PRD specifies?
4. **Data model**: Does the database schema align with PRD data requirements?
5. **Dead code**: Is there code that implements features NOT in the PRD (scope creep)?
6. **Quality gaps**: Where does the implementation quality fall short of PRD expectations?

Output format:
- Table: PRD Requirement → Implementation Status (Implemented / Partial / Missing / Deviated)
- For each deviation: what was specified vs what was built
- Priority-ranked list of gaps to address
