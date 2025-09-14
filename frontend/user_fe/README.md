# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

## Environment Variables

The frontend communicates with the FastAPI backend through a relative path by default: `/api/v1`.
This works seamlessly in:

- Local dev with the Vite proxy (configured in `vite.config.ts`) pointing to `http://localhost:8000`.
- Docker / container environments where the frontend and backend are served from the same origin or behind a reverse proxy.

Override the base URL only when the API is on a different host/port (e.g., remote dev server):

Steps:

1. Copy `.env.example` to `.env` in this directory.
2. Set `VITE_API_BASE_URL` to an absolute URL if needed.

```bash
# Optional – only override when not using same-origin + proxy
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

If `VITE_API_BASE_URL` is unset, Axios uses the relative path so requests go to the current page origin.
The effective value is exported from `src/services/api.ts` as `API_BASE_URL`.

### Dev Proxy

The Vite dev server proxy is configured so any request starting with `/api` is forwarded to the backend target (default `http://localhost:8000`).
Adjust `VITE_API_PROXY_TARGET` (a Node env var, not exposed to the client) when starting Vite if the backend runs elsewhere:

```bash
# Example (Linux/macOS shell)
VITE_API_PROXY_TARGET=http://127.0.0.1:9000 npm run dev
```

On Windows cmd you can run:

```cmd
set VITE_API_PROXY_TARGET=http://127.0.0.1:9000 && npm run dev
```
