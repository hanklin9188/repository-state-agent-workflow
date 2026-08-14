# Agent Roles

## Builder

May continue across adjacent engineering tasks in one context epoch when the gate permits it.

Delivers implementation, V0/V1 evidence, checkpoints, and a ready next task.

## Reviewer

Starts fresh. Reads the governing spec, diff or commit, tests, evidence, and limitations—not the builder's debugging transcript.

## Runner

Starts fresh for formal or authorized execution. Preserves raw evidence, does not redesign after seeing results, and stops at the execution boundary.

## Analyst

Starts fresh from sealed evidence and the governing protocol. Recomputes or interprets results without mutating raw evidence.

## Decision

Starts fresh at major architecture or scientific forks. Under Medium reasoning, use two passes: evidence decomposition, then decision synthesis.

## Role rotation rule

A change between these roles is a hard context rotation unless the repository contains an explicit, independently justified exception.
