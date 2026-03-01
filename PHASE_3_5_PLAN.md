# Phase 3.5 Plan: Customer & Opportunity Dashboard

**Status**: Planning & Reconnaissance
**Date**: 2026-03-02
**Scout Session**: Current (Termite-1772391490-24142)
**Progress**: Phase 3 at 57% (Tasks 3.1-3.4 complete, 3/7 complete)

---

## Overview

**Phase 3.5: Customer & Opportunity Dashboard Management**
- Create CRM dashboard showing customers and sales opportunities
- Build relationship views (customer ↔ conversations ↔ messages)
- Implement opportunity pipeline visualization
- Add basic CRUD operations for CRM data
- Integrate with existing conversation UI

**Estimated Effort**: 4-5 days (Pheromone estimate)
**Complexity**: Medium (new components, existing API ready)
**Blockers**: None identified

---

## Current State (Scout Observations)

### ✅ Completed (Tasks 3.1-3.4)

| Task | Completion | Lines | Owner | Date |
|------|-----------|-------|-------|------|
| 3.1 | Auth & Setup | 765 | Worker | ~1 day |
| 3.2 | WebSocket Integration | 350 | Worker | ~1 day |
| 3.3 | Conversation UI | 400 | Worker | ~1 day |
| 3.4 | Message Streaming | 500 | Worker | ~1 day |
| **3.5** | **CRM Dashboard** | **800-1000** | **Worker (next)** | **4-5 days** |

### Backend Readiness (for Task 3.5)

```
✅ GET /customers
   - List all customers
   - Returns: id, name, email, phone, created_at, updated_at

✅ GET /customers/{id}
   - Single customer detail
   - Relationship: conversations (all conversations with this customer)

✅ GET /opportunities
   - List all opportunities
   - Filters available (customer_id, stage, etc.)
   - Fields: id, customer_id, title, amount, stage, created_at

✅ GET /opportunities/{id}
   - Opportunity detail view
   - Includes customer reference

✅ POST /opportunities
   - Create new opportunity
   - Required: customer_id, title, amount, stage
   - Returns created opportunity with ID

✅ PATCH /opportunities/{id}
   - Update opportunity (stage changes, amount, title)
   - Partial updates supported

✅ DELETE /opportunities/{id}
   - Delete opportunity
   - Removes from system
```

### Frontend Architecture (Current)

**File Structure**:
```
frontend/src/
├── pages/
│   ├── Login.tsx              (Task 3.1)
│   ├── Dashboard.tsx          (Task 3.1)
│   ├── Conversations.tsx      (Task 3.2-3.4)
│   └── MISSING: Customers.tsx (Task 3.5) ⬅️
├── components/
│   ├── ConversationList.tsx
│   ├── MessageList.tsx
│   ├── MessageInput.tsx
│   └── MISSING: Customer* components (Task 3.5) ⬅️
├── store/
│   ├── authStore.ts
│   ├── conversationStore.ts
│   └── NEW: crmStore.ts (Task 3.5) ⬅️
├── api/
│   ├── client.ts
│   └── websocket.ts
└── hooks/
    ├── useAuth.ts
    └── NEW: useCRM.ts (Task 3.5, optional) ⬅️
```

---

## Task 3.5 Implementation Plan

### Core Deliverables

1. **Customer List Page** (200-250 lines)
   - Display all customers in grid/list view
   - Search/filter by name, email
   - Click to view customer detail
   - Pagination (10 customers per page)
   - Action buttons (view detail, create conversation)

2. **Customer Detail Page** (250-300 lines)
   - Single customer information
   - Tab 1: Customer Info (name, email, phone, created date)
   - Tab 2: Opportunities (kanban-style board with drag-drop)
   - Tab 3: Conversations (list of conversations with this customer)
   - Action: Create new opportunity button
   - Action: Create new conversation button

3. **Opportunity Components** (200-250 lines)
   - OpportunityCard: Displays single opportunity
   - OpportunityBoard: Kanban-style pipeline view (Prospecting → Negotiation → Closed)
   - OpportunityForm: Modal for creating/editing
   - OpportunityDetail: Expanded view for single opportunity

4. **CRM Store** (150-200 lines)
   - Zustand store for customer and opportunity data
   - Actions: fetchCustomers, fetchOpportunities, createOpportunity, updateOpportunity, deleteOpportunity
   - State: customers[], opportunities[], currentCustomer, currentOpportunity, loading, error
   - Integrate with existing conversationStore

5. **Styling** (150-200 lines)
   - CustomersPage.css (grid, filters, pagination)
   - CustomerDetail.css (tabs, opportunity board)
   - OpportunityCard.css (card styling, status badges)
   - ResponsiveDesign (mobile-friendly layouts)

### Navigation Updates

**Update App.tsx routing**:
```tsx
<Route path="/customers" element={<ProtectedRoute><CustomersPage /></ProtectedRoute>} />
<Route path="/customers/:id" element={<ProtectedRoute><CustomerDetail /></ProtectedRoute>} />
<Route path="/opportunities" element={<ProtectedRoute><OpportunitiesPage /></ProtectedRoute>} />
```

**Update header navigation**:
- Add "Customers" link to header
- Add "Opportunities" link to header
- Active state indication

### Opportunity Board Implementation

**Kanban Board Structure**:
```
Prospecting          Negotiation         Closed
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Opportunity1 │    │ Opportunity3 │    │ Opportunity5 │
│ $50,000      │    │ $150,000     │    │ $200,000 ✓   │
│ Acme Corp    │    │ TechStart    │    │ Enterprise   │
└──────────────┘    └──────────────┘    └──────────────┘
│ Opportunity2 │
│ $75,000      │
│ StartupXYZ   │
└──────────────┘
```

**Drag-Drop Interactions**:
- Drag card between columns
- Drop triggers PATCH /opportunities/{id} with new stage
- Optimistic update (same as messages)
- Rollback on error

---

## Data Relationships

```
Customer (1) ──── (N) Opportunity
    │
    └──── (N) Conversation
             │
             └──── (N) Message

Opportunity → Customer (FK)
Conversation → Customer (FK)
Message → Conversation (FK)
```

**View Hierarchy**:
1. Customers Page → Select Customer
2. Customer Detail → View Opportunities OR View Conversations
3. Opportunity Detail → View related Customer
4. Conversation Detail → View related Customer (link)

---

## UI/UX Patterns (Already Established in Tasks 3.1-3.4)

- **Modals**: Create Opportunity modal (similar to Create Conversation)
- **Loading States**: Spinners + disabled buttons during fetch/mutation
- **Error Handling**: Error banners with retry buttons
- **Optimistic Updates**: Show changes immediately, confirm via server
- **Pagination**: Load more button or numbered pagination
- **Search/Filter**: Debounced search input, real-time filter

---

## Technical Decisions (Scout Recommendations for Worker)

1. **State Management**: Use Zustand (consistent with conversationStore)
   - Separate crmStore.ts for customers/opportunities
   - Keep stores isolated but composable
   - Share loading/error patterns

2. **API Client**: Reuse existing apiClient with JWT auth
   - No additional configuration needed
   - Error handling already in place (401 redirects to login)

3. **Component Architecture**:
   - Container page components (CustomersPage, CustomerDetail)
   - Presentational components (CustomerCard, OpportunityCard)
   - Reusable UI (Modal, Form, Board)

4. **Opportunity Board**: Use simple drag-drop (native HTML5 or React DnD)
   - Recommendation: HTML5 native for simplicity
   - Alternative: react-beautiful-dnd for polish (if time allows)

5. **Pagination Strategy**:
   - Option A: Load all data (if customer count < 500)
   - Option B: Lazy load with "Load More" button
   - Recommendation: Option A for MVP (simpler, faster)

---

## File Checklist (Scout Verification)

### To Create
- [ ] `frontend/src/pages/CustomersPage.tsx`
- [ ] `frontend/src/pages/CustomerDetail.tsx`
- [ ] `frontend/src/pages/OpportunitiesPage.tsx`
- [ ] `frontend/src/components/CustomerCard.tsx`
- [ ] `frontend/src/components/CustomerSearch.tsx`
- [ ] `frontend/src/components/OpportunityCard.tsx`
- [ ] `frontend/src/components/OpportunityBoard.tsx`
- [ ] `frontend/src/components/OpportunityForm.tsx`
- [ ] `frontend/src/store/crmStore.ts`
- [ ] `frontend/src/styles/CustomersPage.css`
- [ ] `frontend/src/styles/CustomerDetail.css`
- [ ] `frontend/src/styles/OpportunityBoard.css`
- [ ] `frontend/src/styles/OpportunityCard.css`

### To Modify
- [ ] `frontend/src/App.tsx` (add routes for /customers, /customers/:id, /opportunities)
- [ ] `frontend/src/components/ConversationList.tsx` (add navigation link to customers)
- [ ] `frontend/src/App.css` (add sidebar navigation styles if needed)

---

## Estimated Line Counts (Scout Analysis)

| Component | Lines | Notes |
|-----------|-------|-------|
| CustomersPage | 150-200 | List with search/filter |
| CustomerDetail | 200-250 | Tabs + opportunity board |
| OpportunitiesPage | 100-150 | Global opportunities view |
| CustomerCard | 50-75 | Reusable card component |
| OpportunityCard | 75-100 | Card with stage badge |
| OpportunityBoard | 150-200 | Kanban board with DnD |
| OpportunityForm | 150-200 | Modal form (create/edit) |
| crmStore | 200-250 | Zustand store + actions |
| Styles | 400-500 | CSS for all new components |
| **TOTAL** | **1075-1425** | Expected range |

**Recommendation**: Aim for 1000-1100 lines (like Tasks 3.3-3.4)

---

## Testing & Verification (Post-Implementation)

### Manual Testing Checklist
- [ ] Load customers page, verify list displays
- [ ] Search/filter customers by name works
- [ ] Click customer, view detail page
- [ ] Click "Create Opportunity" opens modal
- [ ] Fill form, submit, see success + close modal
- [ ] Verify new opportunity appears in board
- [ ] Drag opportunity between columns (kanban)
- [ ] Verify PATCH request sent on drop
- [ ] Open opportunities page, verify all displayed
- [ ] Click opportunity card, view detail
- [ ] Test error handling (close WebSocket, try create)
- [ ] Test mobile responsive layout

### Integration Points
- ✅ Backend APIs (GET, POST, PATCH, DELETE)
- ✅ JWT authentication (inherited from Task 3.1)
- ✅ Existing store patterns (conversationStore template)
- ✅ WebSocket (not needed for Task 3.5, async jobs done via REST)
- ✅ Navigation routing (App.tsx updates)

---

## Known Considerations

### Edge Cases
1. **Empty Customers List**: Show empty state with "Create customer" guidance
2. **No Opportunities**: Show empty kanban columns with "Create" button
3. **Deleted Customer**: Handle 404 if customer deleted while viewing
4. **Network Errors**: Retry button for failed fetches
5. **Large Lists**: Pagination / lazy loading if needed later

### Future Enhancements (Not in Phase 3.5)
1. **Bulk Actions**: Select multiple opportunities, change stage
2. **Filters**: By opportunity stage, amount range, date range
3. **Sorting**: By name, created date, opportunity count
4. **Export**: Download customer/opportunity data as CSV
5. **Customer Creation**: Create new customers in UI (currently backend only)
6. **Edit Customer**: Update customer info (currently view-only)

---

## Success Criteria

Phase 3.5 is complete when:
- ✅ All 6 new pages/components render without errors
- ✅ Customer list page displays and filters
- ✅ Customer detail shows opportunities and conversations
- ✅ Opportunity kanban board loads and displays
- ✅ Create opportunity form works end-to-end
- ✅ Drag-drop updates opportunity stage
- ✅ Error handling shows proper messages
- ✅ Mobile responsive layout works
- ✅ All components build with TypeScript strict mode
- ✅ Navigation links work between pages

---

## Next Phase (Task 3.6: Testing & CI/CD)

After Task 3.5 completion, Task 3.6 should focus on:
- Unit tests for components (React Testing Library)
- Integration tests for CRM workflows
- E2E tests (Cypress/Playwright)
- GitHub Actions pipeline
- Code coverage reporting
- Automated build & deploy

**Estimated**: 5-7 days

---

## Scout Observations & Recommendations

1. **Team Velocity**: 4 tasks completed in ~1 session = high productivity. Workers are efficiently implementing frontend features.

2. **Code Quality**: Pheromone traces show clean patterns (Zustand stores, optimistic updates, error handling). New code should follow same patterns.

3. **Testing Gap**: Tasks 3.1-3.4 have manual testing but no automated tests. Consider adding unit tests during Task 3.5 implementation.

4. **Performance**: WebSocket messages display instantly (optimistic updates). CRM views should use same pattern for mutations.

5. **Architecture Consistency**: New components should mirror existing patterns (ConversationList, MessageList structure) for maintainability.

---

**Prepared by**: Scout Agent (Termite-1772391490-24142)
**Session Type**: Reconnaissance & Planning
**Recommended Next Caste**: Worker (implementation)
**Signal**: Ready to emit S-006 updates or create new signal for Phase 3.5 execution

