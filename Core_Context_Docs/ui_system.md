Good. Now let me write the complete updated UI system document combining everything — the original, Bordio inspiration, reviewer feedback, and the frontend design principles:

cat > /home/nirav/projects/AI/docs/ui_system.md << 'ENDOFFILE'
# UI System — Talent Operating System
# Version: 3.0 — Complete rewrite with Bordio inspiration + reviewer feedback
# Research Date: March 2026

## Document Purpose
Complete UI/UX design system for the Talent Operating System.
All agents must follow these guidelines exactly when building any frontend component.
Never deviate from these patterns without updating this document first.

---

## CORE DESIGN PHILOSOPHY

### Founder Vision (Non-Negotiable)
- Eye-pleasing, modern, professional design
- Clean light interface inspired by Bordio (bordio.com)
- Side panel system — data and sub-data on single screen
- User never navigates away to see related information
- Focused important data visible immediately
- Fast eye-catching critical information
- Suitable for global user base of all backgrounds and cultures
- Each screen has ONE clear goal — never confuse the user

### Design Inspiration: Bordio
Bordio (bordio.com) is the visual reference for this platform.
Key characteristics to replicate:
- Clean white canvas as primary background
- Light sidebar (not dark navy)
- Color-coded cards with left accent borders
- Column-based layout for pipeline views (like Bordio calendar columns)
- Minimal visual noise — content breathes
- Colorful but professional icon system
- Friendly rounded corners throughout
- Actions appear on hover — clean by default

### 2026 Design Principle
The era of pure minimalism is over.
The era of Density + Intelligence is here.
Power users (recruiters, HR managers) want high-information interfaces.
Candidates want clean consumer-grade interfaces.
Design principle: Right density for the right user.
B2B users (recruiter, HR, agency): Dense but organized
B2C users (candidates): Clean, spacious, mobile-first

---

## COLOR SYSTEM

### Brand Colors
Primary: #4F46E5 (Indigo — professional, modern, memorable)
Primary Dark: #3730A3
Primary Light: #818CF8
Primary Surface: #EEF2FF

Why Indigo not Blue:
Most ATS platforms use blue (LinkedIn blue, Workday blue).
Indigo feels premium, modern, and distinctive.
Stands out in the recruitment space.

### Semantic Colors
Success: #10B981 (Emerald green)
Warning: #F59E0B (Amber)
Error: #EF4444 (Red)
Info: #3B82F6 (Blue)

### Neutral Palette (Light Mode)
Text Primary: #111827
Text Secondary: #6B7280
Text Disabled: #9CA3AF
Border Light: #F3F4F6
Border Default: #E5E7EB
Border Strong: #D1D5DB
Surface White: #FFFFFF
Surface Light: #F9FAFB
Surface Medium: #F3F4F6
Layout Background: #F8FAFC

### Dark Mode Palette
Dark Background: #0F172A
Dark Surface: #1E293B
Dark Border: #334155
Dark Text Primary: #F1F5F9
Dark Text Secondary: #94A3B8

### Sidebar Colors (Bordio-Inspired Light Sidebar)
Sidebar Background: #FFFFFF
Sidebar Border: #F3F4F6 (right border only, very light)
Sidebar Text: #374151
Sidebar Icon Active: #4F46E5
Sidebar Item Active Background: #EEF2FF
Sidebar Item Active Text: #4F46E5
Sidebar Item Hover: #F9FAFB
Sidebar Section Label: #9CA3AF (uppercase, small)

### Status Colors (Consistent Everywhere)
Applied/New: #3B82F6 (Blue)
Screening: #8B5CF6 (Purple)
Shortlisted: #F59E0B (Amber)
Interview Scheduled: #F97316 (Orange)
Interview Done: #06B6D4 (Cyan)
Offered: #10B981 (Emerald)
Joined: #059669 (Green)
Rejected: #EF4444 (Red)
Withdrawn: #6B7280 (Gray)
On Hold: #84CC16 (Lime)
Draft: #9CA3AF (Gray)
Pending Approval: #FBBF24 (Yellow)
Active: #10B981 (Emerald)
Paused: #F59E0B (Amber)
Closed: #6B7280 (Gray)

---

## TYPOGRAPHY

### Font Selection
Primary: Outfit (Google Fonts — friendly, modern, globally readable)
Alternative: Plus Jakarta Sans (if Outfit unavailable)
Fallback: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif
Code: JetBrains Mono, Fira Code, monospace

Why Outfit not Inter:
Inter is used by every generic SaaS tool.
Outfit is friendly, professional, and distinctive.
Excellent Latin and extended character support for global use.
Slightly rounded terminals give warmth without being childish.

### Type Scale
Display: 36px / 44px / 700
H1: 28px / 36px / 700
H2: 22px / 30px / 600
H3: 18px / 26px / 600
H4: 16px / 24px / 600
Body Large: 16px / 26px / 400
Body: 14px / 22px / 400
Body Small: 13px / 20px / 400
Caption: 12px / 18px / 400
Label: 12px / 18px / 500
Code: 13px / 20px / 400

### Usage Rules
Page titles: H1 only at top of page
Section headings: H2 or H3 inside content
Never more than H3 inside card content
Minimum body text: 14px always
Table compact rows: 13px acceptable
Never use weight below 400 in body text
Never use size below 12px anywhere

---

## SPACING SYSTEM

Base unit: 4px
Scale: 2, 4, 6, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 80, 96px

Standard component spacing:
Page padding: 24px all sides
Card padding: 20px
Card inner gap: 16px
Table cell padding: 10px 16px
Form item bottom margin: 20px
Section gap: 24px
Sidebar padding: 12px 16px
Right panel padding: 20px
Modal padding: 24px
Badge padding: 2px 10px

---

## LAYOUT SYSTEM

### Three Zone Layout (Master Layout)
Every authenticated page follows this structure:

+---------------+--------------------------------+------------------+
|               |                                |                  |
| LEFT SIDEBAR  |      MAIN CONTENT AREA         |  RIGHT PANEL     |
|   220px       |      Flexible width            |  360px           |
|               |                                |                  |
| Light bg      |  White background              | Slides in        |
| Always fixed  |  Primary data                  | on item click    |
| Collapsible   |  Scrollable                    | Contextual       |
| to 60px       |                                | actions + data   |
+---------------+--------------------------------+------------------+


### Left Sidebar Specification
Width: 220px expanded, 60px icon-only collapsed
Background: #FFFFFF
Right border: 1px solid #F3F4F6
Position: Fixed, full height

Top section:
- Logo: 36px height, left aligned with 20px padding
- App name next to logo (hidden in icon-only mode)

Middle section (navigation):
- Section labels: 10px uppercase #9CA3AF with 16px top margin
- Nav items: 40px height, 12px horizontal padding, border-radius 8px
- Icon: 18px, colored when active (#4F46E5), gray (#9CA3AF) when inactive
- Label: 14px #374151, hidden in icon-only mode
- Active state: #EEF2FF background + #4F46E5 text and icon
- Hover: #F9FAFB background
- Notification badge: Red dot on icon when pending items
- Sub-items: Indent 12px, shown when parent expanded

Bottom section:
- Quick create button (+ icon with label)
- Divider
- User avatar (32px circle) + name + role
- Settings gear icon

### Main Content Area Specification
Background: #F8FAFC
Contains: Page header + filter bar + content

Page header (48px height):
- Left: Page icon (20px) + Page title (H2) + breadcrumb
- Right: Primary CTA button + secondary actions
- Bottom border: 1px solid #F3F4F6

Filter bar (when applicable, 48px height):
- Search input (Meilisearch-powered, instant results)
- Filter chips (status, date, assignee, etc.)
- View toggle (table / kanban / list)
- Sort dropdown
- Background: #FFFFFF with bottom border

Content area:
- Background: #F8FAFC
- Padding: 24px
- Content fills available space

### Right Panel Specification
Width: 360px
Background: #FFFFFF
Left border: 1px solid #F3F4F6
Left shadow: -4px 0 16px rgba(0,0,0,0.06)
Slides in from right: 220ms ease-out
Position: Fixed, full height

Header (56px):
- Back/close button left
- Title (H3) center
- Action menu (three dots) right

Content:
- Scrollable
- Tabs for: Overview, Notes, History, Documents, Communication
- Each tab lazy-loaded

Footer (when applicable):
- Primary action button full width
- Secondary text action below

---

## COMPONENT LIBRARY

### Candidate Card (Pipeline Kanban)
Inspired by Bordio task cards.
Width: Full column width
Height: Auto (min 80px)
Background: #FFFFFF
Border: 1px solid #F0F1F3
Border-radius: 10px
Left accent: 4px solid [status color]
Shadow: 0 1px 3px rgba(0,0,0,0.05)
Hover shadow: 0 4px 12px rgba(0,0,0,0.1)
Hover: Translate up 1px
Cursor: Pointer

Card content layout:
Top row: Avatar initial (32px circle) + Name (14px 600) + Status badge
Middle row: Current title @ Company (13px gray)
Bottom row: Source tag + Match score + Days ago
Hover reveals: Move stage, Reject, Quick view buttons

### Pipeline Column (Bordio Calendar Column Inspired)
Width: 260px minimum
Background: Very light tinted per stage (5% opacity of status color)
Header: Stage name (14px 600) + count badge + add button
Cards stack vertically with 8px gap
Column scrollable vertically
Drag and drop between columns
Column collapse: Click header to minimize

### Data Table
Based on Ant Design Table.
Row height: 52px default, 40px compact
Header: 13px 600 uppercase gray background #F9FAFB
Row: White alternating with #FAFAFA (very subtle)
Row hover: #F5F7FF (very light indigo tint)
Row click: Opens right panel
Selected rows: #EEF2FF background

Always include:
- Checkbox first column (24px)
- Avatar + name combination column
- Status badge column
- Key data columns
- Actions column (appears on row hover)
- Bulk action toolbar when rows selected (slides in from top)
- Empty state at bottom
- Cursor-based pagination

### Status Badge
Shape: Pill (border-radius 100px)
Size: 12px font, 4px 10px padding
Style: Light background (10% opacity) + matching text color
Examples:
- Shortlisted: #FEF3C7 background + #92400E text
- Active: #D1FAE5 background + #065F46 text
- Rejected: #FEE2E2 background + #991B1B text
Never use plain text for status — always badge

### Metric Card (Dashboard)
Background: #FFFFFF
Border: 1px solid #F3F4F6
Border-radius: 12px
Padding: 20px
Shadow: 0 1px 3px rgba(0,0,0,0.04)

Layout:
- Top: Icon (24px colored) + label (12px gray uppercase)
- Middle: Value (32px 700 dark)
- Bottom: Trend indicator (arrow + percentage + period)

Variants:
- Default: White background
- Highlight: Light indigo background for primary metric
- Alert: Light red background for overdue items

### Button System
Primary: #4F46E5 background, white text, hover #3730A3
Secondary: White background, #E5E7EB border, #374151 text
Danger: #EF4444 background, white text
Ghost: Transparent, #4F46E5 text, hover #EEF2FF background
Link: No background, no border, #4F46E5 text, underline on hover

Sizes:
Large: 40px height, 16px font, 20px horizontal padding
Default: 34px height, 14px font, 16px horizontal padding
Small: 28px height, 12px font, 12px horizontal padding

Border-radius: 8px on all buttons
Never use square corners on buttons

### Form Elements
Input height: 36px
Border: 1px solid #E5E7EB
Border-radius: 8px
Focus border: #4F46E5
Background: #FFFFFF
Placeholder: #9CA3AF
Label: 13px 500 #374151, always above field
Required: Red asterisk after label
Helper text: 12px #6B7280 below field
Error state: Red border + red error message below

### Modal
Max-width: 560px (standard), 720px (large), 480px (small)
Background: #FFFFFF
Border-radius: 16px
Shadow: 0 20px 60px rgba(0,0,0,0.15)
Overlay: rgba(0,0,0,0.4) backdrop blur 4px
Header: Title (H3) + close button
Footer: Action buttons right-aligned
Body: Scrollable with max-height 60vh

### Drawer
Slides from right for complex forms and detail views
Width: 520px desktop, full screen mobile
Same styling as right panel but larger
Used for: Create/edit forms, detailed views requiring full form
Header: Back arrow + title + close

### Empty State
Never show blank white space.
Always show:
- Centered illustration (64px icon or simple SVG)
- Title (H3): Clear description of empty state
- Description (body): What user can do
- CTA button: Primary action to fill the empty state

Examples:
No jobs: "No jobs posted yet" + "Post your first job to start hiring" + Create Job button
No candidates: "No candidates found" + "Try adjusting your search filters" + Clear Filters button

### Loading Skeleton
Always use skeleton that matches shape of content.
Never use spinner alone for full page loads.
Skeleton color: #F3F4F6 animated to #E5E7EB
Animation: Shimmer left to right, 1.5s infinite

### Toast Notifications
Position: Bottom right
Max width: 360px
Border-radius: 10px
Shadow: 0 4px 16px rgba(0,0,0,0.12)

Success: #ECFDF5 background + #065F46 text + #10B981 left border
Error: #FEF2F2 background + #991B1B text + #EF4444 left border
Warning: #FFFBEB background + #92400E text + #F59E0B left border
Info: #EFF6FF background + #1E40AF text + #3B82F6 left border

Auto-dismiss: Success 3s, Info 4s, Warning 5s, Error manual dismiss
Max 3 toasts visible at once

---

## PAGE TEMPLATES

### Dashboard Page
Layout: Bento grid
Top row: 4 metric cards (equal width)
Second row: Large chart (2/3 width) + summary list (1/3 width)
Third row: Two medium cards equal width
Fourth row: Full width table or activity feed

### List/Table Page
Layout: Filter bar + full-width data table
Right panel slides in on row click
Bulk action bar slides in when rows selected
Empty state centered in table area

### Pipeline/Kanban Page
Layout: Horizontal scroll of columns
Filter bar above columns
Each column: Stage name + count + cards
Drag and drop between columns
Right panel slides in on card click
Column add button at end of row

### Detail Page (Full Page)
Used for complex items requiring full editing
Layout: Left main content (70%) + right sidebar (30%)
Tabs within main content for different data sections
Right sidebar: Quick actions + related items + timeline

### Form Page (Modal or Drawer)
Multi-step forms: Progress indicator at top
Single-form: Standard modal
Complex multi-section forms: Drawer (520px)
Section headers within form to group fields
Save button always visible (sticky footer)

---

## ROLE-BASED INTERFACES

### Company HR Dashboard
Landing page on login:
Row 1: Open Jobs | Active Candidates | Interviews Today | Pending Approvals
Row 2: Hiring pipeline overview (stages with counts) + Upcoming interviews today
Row 3: Recent agency submissions + Overdue actions (red alerts)
Row 4: Recent activity feed

Quick access from sidebar:
Dashboard, Jobs, Pipeline, Candidates, Agencies, Interviews, Analytics, Settings

### Agency Recruiter Dashboard
Landing page on login:
Row 1: My Assigned Jobs | Submitted Today | In Process | Placements This Month
Row 2: My candidate pipeline + Today's follow-up tasks
Row 3: Client activity + Deadline alerts (amber/red)
Row 4: Team activity (for managers)

Quick access from sidebar:
Dashboard, My Jobs, Candidates, Clients, Pipeline, Team, Analytics, Settings

### Candidate Portal
Mobile-first design, consumer-grade feel.
Landing page on login:
- Passport completeness progress bar (prominent, colorful)
- Active applications with visual stage tracker
- Upcoming interview cards
- Recommended jobs (3-4 cards)
- Upcoming cafe sessions

Navigation: Bottom tab bar on mobile
Tabs: Home, My Passport, Jobs, Applications, Interviews

### Common Elements (All Roles)
Top navigation bar:
- Left: Hamburger (mobile) or logo
- Center: Global search (Cmd+K opens command palette)
- Right: Notification bell (badge) + User avatar + dropdown

---

## COMMAND PALETTE (Cmd+K)

Opens as centered modal overlay.
Search input at top with instant results.
Sections: Recent items | Quick Actions | Navigation
Keyboard: Arrow keys navigate, Enter selects, Esc closes.

Quick actions:
- Create Job, Add Candidate, Schedule Interview
- Go to Pipeline, Go to Dashboard
- Search candidates, Search jobs
- Open settings

---

## INTERVIEW CAFE MISSION CONTROL

Full-screen interface during live sessions.
This is a unique screen unlike anything else on the platform.

Layout:
Top bar: Session name + timer + Live badge + counts + Pause button
Left panel (280px): Queue of waiting candidates
Center (flex): Grid of interview room cards
Right panel (240px): Session stats + quick controls

Queue Card:
Candidate photo initial + name + applied role
Passport heat score badge + time waiting
Shortlist button (green) + Skip button (gray)
Drag to assign to room

Interview Room Card:
Room number + interviewer name
Candidate name (when occupied)
Timer (how long in interview)
Status: Waiting (gray) / Active (green pulse) / Done (check)
Quick feedback buttons on hover

Top Bar Counts:
Registered | Checked In | Screened | Interviewing | Offers Made

Color scheme for Cafe:
Slightly different from main app — more energetic
Primary: #10B981 (green — live, active feel)
Background: #0F172A (dark — focus, broadcast feel)
Cards: #1E293B
Text: #F1F5F9

---

## TALENT PASSPORT PUBLIC PAGE

Completely different aesthetic from the app.
This is the candidate's professional identity page — like a premium portfolio.

Design:
Clean, modern, almost like a personal website
Large hero section: Photo + name + title + location + heat score
Sections: About, Experience, Education, Skills, Assessments, Interviews
Share link prominently displayed (one-click copy)
Privacy toggles visible only to passport owner
Access log visible only to passport owner

Colors:
White background, dark text
Accent color based on passport owner's chosen theme
Professional feel — not corporate but not casual

---

## MOBILE DESIGN

### Breakpoints
Mobile: 0-767px
Tablet: 768-1199px
Desktop: 1200px+

### Mobile Adaptations
Sidebar: Hidden, hamburger opens as overlay
Right panel: Full-screen bottom drawer
Pipeline: Single column, swipe left/right between stages
Tables: Card view on mobile (not horizontal scroll)
Metric cards: 2x2 grid on mobile
Forms: Full width, 44px touch targets minimum
Buttons: Full width on forms
Navigation: Bottom tab bar (5 main items)
Notifications: Top slide-down banner

### Candidate Mobile (Primary Device)
Candidate portal is MOBILE FIRST — designed for phone first.
Bottom tab navigation: Home, Passport, Jobs, Applications, Interviews
Thumb-friendly: All primary actions within thumb reach
Large tap targets: 48px minimum
Offline capable: Cache last-viewed data

---

## ACCESSIBILITY

### WCAG 2.1 AA Required
Color contrast: 4.5:1 for normal text minimum
Large text contrast: 3:1 minimum
Focus indicators: Always visible, never removed
Screen reader: All interactive elements have ARIA labels
Images: All have alt text
Forms: Labels always associated with inputs
Errors: Linked to fields with aria-describedby

### Keyboard Navigation
Tab: Move through interactive elements
Shift+Tab: Move backwards
Enter/Space: Activate buttons
Arrow keys: Navigate menus, tables, kanban
Escape: Close overlays, panels, modals
Cmd+K: Command palette

---

## ANIMATION SYSTEM

### Principles
Fast and purposeful only.
Never animate for decoration.
Respect prefers-reduced-motion setting.
Animations should feel native, not flashy.

### Standard Durations
Micro (button hover, badge): 80ms
Fast (dropdown, tooltip): 120ms
Normal (modal, panel): 200ms
Slow (page transition): 300ms
Never exceed 400ms for any animation

### Standard Easings
Enter: ease-out (fast start, slow end — feels responsive)
Exit: ease-in (slow start, fast end — feels intentional)
Movement: ease-in-out (smooth throughout)

### Specific Animations
Right panel open: Slide from right 200ms ease-out
Right panel close: Slide to right 150ms ease-in
Modal open: Fade + scale 95%→100% 150ms ease-out
Toast appear: Slide up from bottom 200ms ease-out
Dropdown: Fade + slide down 4px, 120ms ease-out
Row hover: Background color 80ms
Card hover: Shadow + translate(-1px) 120ms ease-out
Button press: Scale 98%, 80ms
Skeleton shimmer: 1.5s infinite left-to-right

### No Animations On
Table data updates (layout shifts)
Status badge color changes
Counter number updates
Skeleton to content transitions (fade only)

---

## ICONS

### Icon Libraries
Primary: Lucide React (consistent, clean, 24px default)
Supplement: Heroicons for any Lucide gaps
Never: Mix icon styles on same screen

### Icon Sizes
Navigation sidebar: 20px
Button icons: 16px
Table action icons: 16px
Status icons: 14px
Dashboard metric icons: 24px
Empty state icons: 48px
Notification icons: 20px

### Icon Colors
Navigation inactive: #9CA3AF
Navigation active: #4F46E5
Action icons: #6B7280, hover #374151
Status icons: Match status color
Danger icons: #EF4444

---

## INTERNATIONALIZATION

All text must use i18n keys (react-i18next library).
Never hardcode English text in components.
Date formats: Follow user locale (moment.js or date-fns with locale)
Number formats: Intl.NumberFormat with user locale
Currency: Symbol + amount, locale-aware
Time zones: All times stored UTC, displayed in user timezone
RTL support: All layouts work mirrored for Arabic and Hebrew
Font: Outfit supports all required character sets

---

## PERFORMANCE TARGETS

First Contentful Paint: Under 1.2 seconds
Largest Contentful Paint: Under 2.0 seconds
Time to Interactive: Under 2.5 seconds
Cumulative Layout Shift: Under 0.05
First Input Delay: Under 50ms

Techniques:
- Route-based code splitting (React.lazy)
- Image lazy loading with blur placeholder
- Virtual scrolling for tables over 100 rows
- TanStack Query caching for API responses
- WebSocket for real-time (no polling)
- Skeleton loading prevents layout shifts
- Font preloading for Outfit

---

## KEY RULES FOR ALL AGENTS

When building any React component:

1. Use Ant Design as component base — never reinvent what Ant Design provides
2. Use Tailwind CSS for all custom styling on top of Ant Design
3. Follow Bordio-inspired light design — no dark sidebars
4. Use Outfit font everywhere — never Inter or Roboto
5. Use #4F46E5 Indigo as primary color — not blue
6. Every list and table MUST have empty state component
7. Every data fetch MUST show loading skeleton
8. Every action MUST have success and error toast feedback
9. Every component MUST work on mobile at 375px width
10. Right panel opens on item click — never navigate to new page for basic views
11. Status MUST always be a colored badge — never plain text
12. All text MUST use i18n keys — never hardcode English
13. Every interactive element MUST be keyboard accessible
14. Follow three-zone layout on every authenticated page
15. Status colors MUST be consistent — same status always same color
16. Card hover MUST show shadow increase and slight upward movement
17. Actions on cards MUST appear only on hover — clean by default
18. Animations MUST respect prefers-reduced-motion
19. All forms MUST have inline validation — never wait for submit
20. Command palette MUST be accessible from any page via Cmd+K
ENDOFFILE