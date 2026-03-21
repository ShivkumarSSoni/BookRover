# BookRover — Frontend

React (TypeScript) + Tailwind CSS mobile-first frontend.

## Stack
- React 18 + TypeScript
- Tailwind CSS (mobile-first styling)
- React Router (client-side routing)
- Axios (API calls)
- Jest + React Testing Library (tests)

## Structure
```
src/
├── components/     # Reusable UI components
├── pages/          # One file per page/route
├── hooks/          # Custom React hooks (data fetching, state)
├── services/       # API call functions (axios)
├── context/        # React Context providers (auth, seller)
└── utils/          # Shared utilities (formatCurrency, etc.)
```

## Local Setup

```powershell
# Install dependencies
npm install

# Start dev server (proxies /api to http://localhost:8080)
npm run dev
```

Frontend runs at: http://localhost:5173  
Requires the backend running on port 8000 for API calls.

## Running Tests

```powershell
# Run all tests
npm test

# Watch mode
npm run test:watch

# With coverage
npm run test:coverage
```

## Building for Production

```powershell
npm run build
```

Output is in `dist/` — deploy to S3 + CloudFront.
