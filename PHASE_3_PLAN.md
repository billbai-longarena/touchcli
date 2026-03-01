# Phase 3 Frontend Implementation Plan

**Timestamp**: 2026-03-02 ~22:00Z
**Caste**: Scout (Planning Phase)
**Status**: 🟢 READY FOR WORKER IMPLEMENTATION
**Estimated Duration**: 3-4 weeks
**Quality Target**: 90/100

---

## 📋 Executive Summary

Phase 3 implements the frontend client for TouchCLI, connecting to the production-ready Phase 2 backend via REST API and WebSocket. The frontend will provide a conversational sales interface with real-time agent responses, customer context, and opportunity management.

### Technology Stack Decision: **React 18 + TypeScript**

**Rationale**:
- ✅ Industry standard for real-time applications
- ✅ Strong WebSocket library ecosystem (Socket.io fallback)
- ✅ Excellent TypeScript support
- ✅ Large component library ecosystem (Material-UI, Tailwind, Shadcn)
- ✅ Proven for production sales tools

**Alternatives Considered**:
- Vue 3: Good choice (lighter, faster), but React has wider adoption
- Svelte: Excellent performance, but smaller ecosystem
- Next.js: Over-engineered for Phase 3 scope

---

## 🎯 Phase 3 Scope

### Primary Goals
1. ✅ WebSocket real-time messaging
2. ✅ JWT authentication flow (login → token → protected pages)
3. ✅ Conversation UI with message history
4. ✅ Customer and opportunity context display
5. ✅ Agent response streaming (real-time)
6. ✅ Dashboard with conversation list
7. ✅ End-to-end testing

### Out of Scope (Phase 4+)
- Voice input/output (requires Whisper API)
- Advanced analytics dashboard
- CRM integrations (Salesforce, HubSpot)
- Mobile native apps
- Internationalization (i18n)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│           Frontend (React 18 + TypeScript)              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │   Pages      │  │  Components  │  │    Hooks    │  │
│  │              │  │              │  │             │  │
│  │ • Login      │  │ • Message    │  │ • useAuth   │  │
│  │ • Dashboard  │  │ • Input      │  │ • useAPI    │  │
│  │ • Convo View │  │ • Context    │  │ • useWS     │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │            State Management (Zustand)            │  │
│  │  • auth (user, token, login/logout)             │  │
│  │  • conversations (list, current, messages)      │  │
│  │  • ui (loading, errors, notifications)          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         HTTP + WebSocket Client Layer            │  │
│  │  • axios for REST (conversations, customers)    │  │
│  │  • ws/Socket.io for real-time messaging        │  │
│  │  • JWT token injection in headers               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
              ↓ HTTPS/WSS ↓
┌─────────────────────────────────────────────────────────┐
│         Backend (Phase 2 - Already Complete)            │
│  • 14 REST endpoints (JWT protected)                    │
│  • WebSocket gateway (ws://localhost:8080/ws)          │
│  • Agent orchestration                                  │
│  • Database (PostgreSQL)                                │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Task Breakdown

### Task 3.1: Project Setup & Authentication (3-4 days)

**Objective**: Initialize React project with authentication flow

**Subtasks**:
1. Create React app (`npx create-vite@latest touchcli-frontend -- --template react`)
2. Install dependencies:
   - `axios` (HTTP client)
   - `zustand` (state management)
   - `react-router-dom` (routing)
   - `typescript`
   - `@tailwindcss/forms` (UI components)
   - `@heroicons/react` (icons)
   - `react-hot-toast` (notifications)

3. Set up folder structure:
   ```
   src/
   ├── pages/         (Login, Dashboard, ConversationView)
   ├── components/    (Message, Input, Header, etc.)
   ├── hooks/         (useAuth, useAPI, useWebSocket)
   ├── services/      (api.ts, websocket.ts)
   ├── stores/        (auth.ts, conversations.ts, ui.ts)
   ├── types/         (User, Conversation, Message, etc.)
   ├── utils/         (formatters, validators)
   └── App.tsx
   ```

4. Create Login page:
   - Form with email + "continue" (no password for demo)
   - JWT token retrieval from `/login` endpoint
   - Token storage (localStorage with expiration)
   - Redirect to dashboard on success

5. Create auth hook (`useAuth`):
   - User state (id, token, isAuthenticated)
   - Login/logout functions
   - Token auto-refresh on expiration
   - Protected route wrapper

**Deliverables**:
- ✅ React project scaffold
- ✅ Login page with auth flow
- ✅ Protected routes (redirect if no token)
- ✅ Zustand store for auth state

**Success Criteria**:
- [ ] `npm run dev` starts without errors
- [ ] Login page renders at `/login`
- [ ] Can login with test user UUID (from seeding)
- [ ] Token stored in localStorage
- [ ] Dashboard redirects if not authenticated

---

### Task 3.2: WebSocket Client Integration (3-4 days)

**Objective**: Implement real-time WebSocket connection for messages

**Subtasks**:
1. Create WebSocket service (`services/websocket.ts`):
   - Connect to `ws://localhost:8080/ws`
   - Auto-reconnect logic (exponential backoff)
   - Message type handling (message, heartbeat, error, system)
   - Event emitter pattern (subscribe/unsubscribe)

2. Create WebSocket hook (`hooks/useWebSocket`):
   - Connect on component mount
   - Listen for messages
   - Handle connection status
   - Cleanup on unmount

3. Message frame format (from Phase 2 spec):
   ```json
   {
     "type": "message",
     "conversation_id": "uuid",
     "user_id": "uuid",
     "content": "text",
     "timestamp": "ISO-8601"
   }
   ```

4. Heartbeat mechanism:
   - Send every 30 seconds
   - Server responds with pong
   - Track connection health

5. Error handling:
   - Network errors → auto-reconnect
   - Invalid frames → log and ignore
   - Connection close → notify user

**Deliverables**:
- ✅ WebSocket service with auto-reconnect
- ✅ useWebSocket hook
- ✅ Real-time message handling
- ✅ Connection status display

**Success Criteria**:
- [ ] WebSocket connects on page load
- [ ] Heartbeat working (no disconnects)
- [ ] Can send messages via WebSocket
- [ ] Receive agent responses in real-time
- [ ] Auto-reconnect on disconnect

---

### Task 3.3: Conversation UI Components (5-6 days)

**Objective**: Build core UI components for conversations

**Subtasks**:
1. Dashboard page (`pages/Dashboard.tsx`):
   - Conversation list (sidebar)
   - Current conversation view (main area)
   - Customer/opportunity context (right panel)
   - Create new conversation button

2. ConversationList component:
   - Fetch from `GET /conversations`
   - Display title, customer, last message, timestamp
   - Click to select conversation
   - Real-time updates (new messages highlight)
   - Pagination (50 conversations per page)

3. MessageView component:
   - Display message history (newest at bottom)
   - Auto-scroll to latest message
   - User messages (right-aligned, blue)
   - Agent messages (left-aligned, gray)
   - Timestamp and metadata

4. MessageInput component:
   - Text input with Shift+Enter for newline
   - Send button (disabled during transmission)
   - Loading state with spinner
   - Error display (red toast)
   - Character counter (optional)

5. CustomerContext component:
   - Display customer name, email, industry
   - Related opportunities (status, amount)
   - Quick action buttons

6. Header component:
   - Logo
   - Current user display
   - Logout button
   - Connection status indicator

**Deliverables**:
- ✅ Dashboard layout (3-column)
- ✅ Message display with styling
- ✅ Input component with send logic
- ✅ Customer context sidebar

**Success Criteria**:
- [ ] Dashboard displays list of conversations
- [ ] Clicking conversation loads messages
- [ ] Can type and send messages
- [ ] Agent responses appear in real-time
- [ ] Customer info displayed correctly
- [ ] Mobile responsive (basic, not required)

---

### Task 3.4: Real-time Message Streaming (3-4 days)

**Objective**: Implement streaming agent responses and optimistic updates

**Subtasks**:
1. Message streaming logic:
   - Send user message via HTTP POST `/messages`
   - Display optimistic message immediately (before server response)
   - Receive agent response via WebSocket
   - Update conversation state
   - Mark as "sent" when confirmed

2. Loading states:
   - Show typing indicator while agent responds
   - Disable input during response
   - Error state with retry button

3. Message state management (Zustand):
   ```typescript
   interface Message {
     id: string;
     content: string;
     sender: "user" | "agent";
     timestamp: ISO-8601;
     status: "sending" | "sent" | "failed";
   }

   interface Conversation {
     id: string;
     messages: Message[];
     customer: Customer;
     opportunity?: Opportunity;
   }
   ```

4. Optimistic updates:
   - Add message to UI before confirmation
   - Rollback on error
   - Show error toast if failed
   - Retry option

5. Scroll behavior:
   - Auto-scroll to new messages
   - Jump-to-latest button if scrolled up
   - Preserve scroll position on updates

**Deliverables**:
- ✅ Message submission flow
- ✅ Optimistic UI updates
- ✅ Loading and error states
- ✅ Auto-scrolling message view

**Success Criteria**:
- [ ] Send message appears instantly (optimistic)
- [ ] Agent response streams in real-time
- [ ] Typing indicator shown while waiting
- [ ] Errors handled gracefully with retry
- [ ] No duplicate messages
- [ ] Scroll to latest on new message

---

### Task 3.5: Customer & Opportunity Dashboard (4-5 days)

**Objective**: Implement dashboard views for customers and opportunities

**Subtasks**:
1. Customers page:
   - List all customers (`GET /customers`)
   - Search/filter by name, industry
   - Click customer → view conversations
   - Create new customer button
   - Customer details page (email, phone, industry, notes)

2. Opportunities page:
   - List opportunities (`GET /opportunities`)
   - Filter by status (discovery, proposal, negotiation, closed)
   - Filter by customer
   - Sort by amount, close date
   - Opportunity details (amount, probability, notes)
   - Create new opportunity (modal)

3. Dashboard analytics (optional Phase 3 stretch):
   - Total customers count
   - Active opportunities count
   - Total pipeline value
   - Conversations in progress count

4. Create new conversation from customer:
   - Button on customer details
   - Auto-link customer_id and opportunity_id
   - Redirect to conversation view

**Deliverables**:
- ✅ Customers list and detail pages
- ✅ Opportunities list with filters
- ✅ Quick create conversation from customer

**Success Criteria**:
- [ ] Customer list loads and displays
- [ ] Search filters work
- [ ] Opportunities show correct status badges
- [ ] Can create new opportunity
- [ ] Quick link to new conversation works

---

### Task 3.6: Authentication & Session Management (2-3 days)

**Objective**: Implement secure auth flow with token refresh

**Subtasks**:
1. Token management:
   - Store JWT in localStorage
   - Include token in all API requests (Authorization header)
   - Refresh token before expiration (1 hour default)
   - Handle 401 responses (token expired → logout)

2. Login flow:
   - Email input → fetch user UUID from backend
   - POST `/login?user_id=<uuid>` → get JWT token
   - Validate token format and expiration
   - Store in state + localStorage
   - Redirect to dashboard

3. Logout:
   - Clear token from localStorage
   - Clear auth state
   - Redirect to login

4. Protected API calls:
   - Auto-inject JWT in axios interceptor
   - Retry on 401 with token refresh
   - Logout if refresh fails

5. Session persistence:
   - Load token from localStorage on app init
   - Restore auth state
   - Resume WebSocket connection

**Deliverables**:
- ✅ JWT token lifecycle management
- ✅ Axios interceptor for auto-auth
- ✅ Session persistence

**Success Criteria**:
- [ ] Login works with test user
- [ ] Token included in all API calls
- [ ] Page refresh maintains session
- [ ] Logout clears token
- [ ] 401 responses handled gracefully

---

### Task 3.7: Testing & Deployment (5-7 days)

**Objective**: Complete testing and prepare for production deployment

**Subtasks**:
1. Unit tests (Vitest):
   - Test hooks (useAuth, useWebSocket, useAPI)
   - Test stores (Zustand)
   - Test utility functions
   - Target: 70%+ coverage

2. Integration tests (Cypress/Playwright):
   - Login flow → dashboard
   - Create conversation → send message → receive response
   - WebSocket connection and heartbeat
   - Error handling and recovery

3. E2E testing (manual checklist):
   - [ ] Complete user journey (login → conversation → logout)
   - [ ] Message streaming and real-time updates
   - [ ] Customer/opportunity views
   - [ ] Token expiration and refresh
   - [ ] Network error handling
   - [ ] Mobile responsiveness (basic)

4. Performance optimization:
   - Code splitting by route
   - Lazy load heavy components
   - Optimize images and assets
   - Measure Core Web Vitals (LCP < 2.5s)

5. Build & deploy:
   - `npm run build` → production bundle
   - Docker container for static hosting
   - Deploy to staging environment
   - Health check endpoint

6. Documentation:
   - README with setup instructions
   - Environment variables (.env.example)
   - Deployment guide
   - Architecture overview

**Deliverables**:
- ✅ Test suite with 70%+ coverage
- ✅ Production build
- ✅ Docker container
- ✅ Deployment documentation

**Success Criteria**:
- [ ] All tests pass (unit, integration, E2E)
- [ ] Build succeeds without warnings
- [ ] Performance metrics within target (LCP < 2.5s)
- [ ] No security vulnerabilities (npm audit)
- [ ] Deployed to staging and tested

---

## 📈 Timeline & Milestones

| Week | Tasks | Deliverable | Status |
|------|-------|-------------|--------|
| Week 1 | 3.1 (Project Setup) | Login page, auth flow | Foundation |
| Week 1 | 3.2 (WebSocket) | Real-time connection | Connectivity |
| Week 2 | 3.3 (UI Components) | Dashboard, messages | Core features |
| Week 2 | 3.4 (Message Streaming) | Real-time responses | Functional |
| Week 3 | 3.5 (Dashboard) | Customer/opportunity views | Full feature set |
| Week 3 | 3.6 (Auth) | Session management | Security |
| Week 4 | 3.7 (Testing & Deploy) | Production build | Ready |

**Total**: 3-4 weeks (21-28 days)
**Parallel**: Tasks can overlap (e.g., 3.1 + 3.2 in parallel)
**Buffer**: ~3-4 days for integration issues

---

## 🔧 Development Environment

### Prerequisites
- Node.js 18+ (LTS)
- npm 8+ or yarn 3+
- Git
- Backend running: `docker-compose up -d`

### Setup
```bash
# Create project
npx create-vite@latest touchcli-frontend -- --template react
cd touchcli-frontend

# Install dependencies
npm install

# Create .env.development.local
echo "VITE_API_URL=http://localhost:8000" > .env.development.local
echo "VITE_WS_URL=ws://localhost:8080/ws" >> .env.development.local

# Start dev server
npm run dev
# Now at http://localhost:5173
```

### Backend Requirements
All met by Phase 2:
- REST API at `http://localhost:8000`
- WebSocket at `ws://localhost:8080/ws`
- PostgreSQL database populated
- Test data available via seeding

---

## 🔐 Security Considerations

1. **JWT Token Storage**:
   - localStorage (vulnerable to XSS, acceptable for internal app)
   - Alternative: HttpOnly cookie (requires backend support)

2. **CORS**:
   - Backend configured: `CORS_ALLOWED_ORIGINS=http://localhost:5173`
   - Production: Update to `https://yourdomain.com`

3. **Environment Variables**:
   - Never commit `.env.local`
   - Use `.env.example` template

4. **API Keys**:
   - JWT secret on backend only
   - No API keys in frontend code

5. **HTTPS**:
   - Local: HTTP okay
   - Production: HTTPS required (WSS for WebSocket)

---

## 📚 Dependencies & Tech Stack

### Core
- **React 18**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool (fast development)
- **React Router v6**: Routing

### State Management
- **Zustand**: Lightweight state store

### HTTP & Real-time
- **axios**: HTTP client
- **ws** or **Socket.io-client**: WebSocket

### UI & Styling
- **Tailwind CSS**: Utility-first CSS
- **Heroicons**: Icon library
- **react-hot-toast**: Notifications

### Testing
- **Vitest**: Unit testing
- **Playwright**: E2E testing
- **@testing-library/react**: Component testing

### Dev Tools
- **ESLint**: Linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking

**Total Dependencies**: ~20 packages (minimal)

---

## 🎯 Success Criteria for Phase 3

**Functional Requirements**:
- ✅ User can login with JWT token
- ✅ Real-time messaging via WebSocket
- ✅ Conversation list and detail views
- ✅ Customer and opportunity management
- ✅ Agent responses stream in real-time
- ✅ Session persistence (refresh page → stay logged in)

**Quality Requirements**:
- ✅ 70%+ test coverage
- ✅ No TypeScript errors (strict mode)
- ✅ No console warnings
- ✅ Core Web Vitals: LCP < 2.5s
- ✅ Mobile responsive (base responsive design)

**Performance Requirements**:
- ✅ Page load < 3 seconds
- ✅ Message send → agent response < 500ms (p95)
- ✅ WebSocket RTT < 100ms (p99)
- ✅ No memory leaks (dev tools check)

---

## 🚀 Deployment Strategy

### Development
- Local: `npm run dev` (Vite server)
- Backend: `docker-compose up -d`

### Staging
- Build: `npm run build`
- Docker: `docker build -t touchcli-frontend .`
- Deploy: Push to staging environment
- Verify: All E2E tests pass

### Production
- Build: `npm run build` (optimized)
- Docker: Push to registry
- Deploy: Blue-green deployment
- Monitoring: Error tracking (Sentry)

---

## 📋 Signal & Handoff

**New Signal Created**: S-006 (Phase 3 Frontend, PROBE status)

**For Next Worker** (Phase 3 Implementation):
1. Read: This plan (PHASE_3_PLAN.md)
2. Read: `PHASE_3_HANDOFF.md` (API reference)
3. Read: `S-005_PERFORMANCE_SLA_COMPLETE.md` (performance targets)
4. Start: Task 3.1 (Project Setup)
5. Commit after each task (50+ lines)

**Recommended Approach**:
- Clone this repo to new branch: `feature/phase-3-frontend`
- Create subdirectory: `frontend/` or `touchcli-frontend/`
- Parallel development: Can split tasks (3.1/3.2 vs 3.5)
- Daily commits with clear messages
- PR workflow: Feature → staging → main

---

**Scout Session Complete**
Pheromone deposited: 2026-03-02 22:00Z
Ready for Worker phase implementation
Signal S-006 generated
Zero blockers identified

*End of Scout Phase - Phase 3 Ready to Begin*
