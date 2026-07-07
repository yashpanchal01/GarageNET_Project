# UI Prototyping Decision Record

## Job Card Detail UI

### Question
What should the Job Card Detail page (`/job-cards/<id>/`) look like to best support workshop mechanics and owners?

### Verdict
**Variant B (Tabbed Action Workspace)** combined with **Variant C (Interactive Flow Progress Bar)** was selected as the final design.

### Rationale
- **High-Density Focus:** Separating the dense parts tables from general vehicle information and audit logs into structured tabs keeps the workspace uncluttered (Variant B).
- **Interactive Status Flow:** Positioning Variant C's interactive horizontal status progress bar at the top allows users to update statuses with a single click instead of form submissions.
- **Scroll Prevention:** Prevents the page from expanding vertically when jobs have many parts, keeping the workspace compact.
- **Audit Transparency:** The Activity Log tab exposes the database record changes clearly, increasing operational confidence.

### Decision Date
2026-07-07

---

## P2P Part Search UI

### Question
What should the Peer-to-Peer (P2P) Part Search page (`/part-search/`) look like to best facilitate part sourcing across workshops?

### Verdict
**Variant B (Comparison Table)** combined with **Variant C (Proximity Radar Map)** was selected as the final design.

### Rationale
- **Efficient Sourcing Comparisons:** Displaying matching parts in a compact, row-based comparison table makes it extremely fast to scan and contrast prices, stock availability, and distances side-by-side.
- **Geospatial Proximity Radar:** Integrating Variant C's custom interactive SVG radar map on the right offers a visual representation of nearby workshops, plotting them coordinates-relative to the user's location.
- **Bidirectional Highlights:** Hovering/clicking a table row highlights the corresponding node on the mock map (and vice-versa), offering a premium, cohesive spatial workflow.

### Decision Date
2026-07-07

---

## Workshop Dashboard UI

### Question
What should the Workshop Dashboard home page (`/`) look like to best support workshop owners and operators?

### Verdict
**Variant C (Modern Analytics Board)** was selected as the final design.

### Rationale
- **Interactive Quick Actions:** The launchpad buttons (Register Job, B2B Search, Manage Inventory) at the top speed up navigation for everyday shop operations.
- **Visual Analytics:** The donut chart SVG visualizes job distribution, and progress bars in the job list give instant visual cues of progress.
- **Clean Structure:** Organizes the low-stock parts ledger cleanly on the side, keeping the view clean.

### Decision Date
2026-07-07

---

## Parts Inventory Ledger UI

### Question
What should the Parts Inventory Ledger page (`/inventory/`) look like to best support stock keeping and editing?

### Verdict
**Variant C (Catalog Cards Grid)** was selected as the final design.

### Rationale
- **Touch-Friendly Cards Layout:** Displaying parts in a catalog grid is highly readable on both tablets and desktop screens, providing a clean visual separation of items.
- **Pulsing Low-Stock Alert:** Highlighting low-stock cards with a pulsing red outline directs immediate focus to items that need reordering.
- **Client-Side Live Filtering:** Live search field allows operators to quickly filter through the grid by typing, providing high responsiveness.

### Decision Date
2026-07-07

---

## Job Cards List UI

### Question
What should the Job Cards Manager page (`/job-cards/`) look like to best support vehicle registrations and workflows?

### Verdict
**Variant A (Workspace Ledger)** was selected as the final design.

### Rationale
- **Logical Sidebar Operations:** Side-by-side split keeps the registration form sticky on the left, making vehicle check-ins fast and clear.
- **Client-Side Live Filtering:** Live search input filters row entries instantly by typing vehicle or customer names.
- **Clear Status Transition Forms:** Each row includes a small select dropdown form to transition job statuses with one click.

### Decision Date
2026-07-07

---

## Workshop Profile UI

### Question
What should the Workshop Profile configuration page (`/profile/`) look like to best support coordinate logging and profile edits?

### Verdict
**Variant B (Settings Sidebar Layout)** combined with **Variant C (Geospatial Placement Preview)** was selected as the final design.

### Rationale
- **Structured Grouped Inputs:** Organizes the setup form into distinct branding and geolocation sections, preventing user form fatigue.
- **Geospatial Placement Preview:** Integrates the SVG preview canvas in the right column, reflecting coordinate inputs visually as a location pin in real-time.
- **Contextual Guidelines:** Displays guidelines directly alongside the canvas mapping.

### Decision Date
2026-07-07
