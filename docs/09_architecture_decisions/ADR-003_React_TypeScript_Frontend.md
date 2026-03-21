# ADR-003: React + TypeScript + Tailwind CSS for Frontend

**Status**: Accepted

---

## Context

The frontend must be mobile-first, maintainable, and deployable as a static site to S3. Sellers use the app on a phone browser — the UI must be instinctively usable with no training.

---

## Options Considered

| Option | Mobile-First | Type Safety | Static Build | Learning Curve |
|--------|-------------|-------------|--------------|----------------|
| Plain HTML + CSS + JS | Manual | None | Yes | Minimal |
| React + JavaScript | Via Tailwind | None | Yes | Medium |
| React + TypeScript + Tailwind CSS | Via Tailwind | Strong | Yes | Medium |

---

## Decision

React 18 + TypeScript + Tailwind CSS.

---

## Rationale

- **React**: component-based architecture suits a multi-page app with shared UI elements (NavBar, SummaryCard, BookCard). Builds to static files — perfect for S3 + CloudFront hosting.
- **TypeScript**: catches type mismatches between API response shapes and UI component props at compile time. Eliminates an entire class of runtime bugs.
- **Tailwind CSS**: mobile-first by design. Responsive utilities (`sm:`, `md:`, `lg:`) built in. No custom CSS files per component. Keeps styling co-located with markup.

---

## Trade-offs Accepted

- Larger initial bundle than plain HTML/JS. Mitigated by CloudFront edge caching and Brotli/gzip compression.
- More upfront setup (TypeScript config, Tailwind config) compared to plain JS. Pays back immediately in type safety and consistent styling.
