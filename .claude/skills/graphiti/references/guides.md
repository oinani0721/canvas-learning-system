# Graphiti - Guides

**Pages:** 1

---

## Performance Optimization Guide

**URL:** llms-txt#performance-optimization-guide

**Contents:**
- Reuse the Zep SDK Client
- Optimizing Memory Operations

> Best practices for optimizing Zep performance in production

This guide covers best practices for optimizing Zep's performance in production environments.

## Reuse the Zep SDK Client

The Zep SDK client maintains an HTTP connection pool that enables connection reuse, significantly reducing latency by avoiding the overhead of establishing new connections. To optimize performance:

* Create a single client instance and reuse it across your application
* Avoid creating new client instances for each request or function
* Consider implementing a client singleton pattern in your application
* For serverless environments, initialize the client outside the handler function

## Optimizing Memory Operations

The `thread.add_messages` and `thread.get_user_context` methods are optimized for conversational messages and low-latency retrieval. For optimal performance:

* Keep individual messages under 10K characters
* Use `graph.add` for larger documents, tool outputs, or business data
* Consider chunking large documents before adding them to the graph (the `graph.add` endpoint has a 10,000 character limit)
* Remove unnecessary metadata or content before persistence
* For bulk document ingestion, process documents in parallel while respecting rate limits

---
