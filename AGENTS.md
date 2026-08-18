# TutorLinkAI Development Rules

## Architecture

TutorLinkAI is a modular monorepo.

Frontend:
React + Vite

Backend:
FastAPI + PostgreSQL

AI:
Python ML/AI services

## Module Ownership

onboarding:
Student/tutor registration and assessment

verification:
Face, OCR, certificate verification

matching:
AI tutor matching and recommendation

booking:
Booking and session management

## Git Rules

Never modify main directly.

Work only on the assigned feature branch.

Do not overwrite another module.

Do not commit .env files.

Do not commit venv or node_modules.

## Shared Code

Shared functionality belongs in:
backend/app/core/
backend/app/database/
backend/app/models/
backend/app/schemas/
backend/app/services/

Do not duplicate shared functionality inside modules.

## Before modifying code

Inspect existing implementation first.

Do not rewrite files unnecessarily.

Run relevant tests before committing.