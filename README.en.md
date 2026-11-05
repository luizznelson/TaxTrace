# TaxTrace

AI agent with an MCP server for querying Brazil's consumption tax reform (IBS and CBS), with **official-source citations**, **validity-date control** and **refusal when there is no evidence**.

> Status: planning. No functionality is implemented yet; see the [plan](PLANO.md) (Portuguese).

## Problem

Since 2026, companies operate under IBS and CBS (Complementary Law 214/2025), and the rules for issuing and validating tax documents keep changing through acts of the Federal Revenue Service and the IBS Management Committee. Classifying products and knowing what applies today means consulting many sources.

## Goals

- Answer questions with the cited official passage and its validity date.
- Refuse what the knowledge base does not support, without inventing tax guidance.
- Expose lookups as MCP tools and orchestrate them with an agent (LangGraph).
- Measure quality with a question set that has reference answers.

## Disclaimer

A lookup aid, not tax advice. Always check the official source.

Português: [README.md](README.md)
