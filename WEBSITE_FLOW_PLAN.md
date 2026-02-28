# Website Flow Plan

## Flow Diagram

```
Landing (#/)
    ├── [Login] → Login (#/login) → [success] → App (#/app)
    ├── [Register] → Register (#/register) → [success] → App (#/app)
    └── [Get started] → Login (#/login)

App (#/app)
    └── [Logout] → Landing (#/)
```

## Pages

| Route | Auth Required | Description |
|-------|---------------|-------------|
| `#/` | No | Landing page – hero, tagline, Login/Register CTAs |
| `#/login` | No | Login form |
| `#/register` | No | Register form |
| `#/app` | Yes | App home – analyze form, history, results |

## Auth Rules

- **Authenticated** user visiting `#/`, `#/login`, or `#/register` → redirect to `#/app`
- **Unauthenticated** user visiting `#/app` → redirect to `#/login`
- **Logout** → clear token, redirect to `#/`

## Components

1. **Landing** – Hero section, value prop, "Login" and "Register" buttons
2. **Login** – Username/password form, link to Register
3. **Register** – Username/email/password form, link to Login
4. **App** – Existing analyze section + history (unchanged behavior)

## Implementation

- Hash-based routing (`window.location.hash`)
- Single `index.html` with sections shown/hidden by route
- `popstate` / `hashchange` for back/forward support
