# Refactoring & Optimization Plan — Vertical Slices

This document tracks the vertical slice breakdown for implementing the hyperlocal search optimization and billing-stock integration in GarageNET.

---

## Slices Breakdown

### 1. Workshop Profile Geolocation and Registration
* **Blocked by:** None
* **User stories covered:** 
  * Story 1: Workshop registration with coordinates.
  * Story 2: Updating profile contact details.
* **Scope:** Implement the baseline `WorkshopProfile` model, registration/profile forms, and the profile configuration UI with settings sidebar and coordinates visual preview.

### 2. Inventory Ledger Management
* **Blocked by:** Slice 1
* **User stories covered:**
  * Story 3: Log B2B inventory items (names, SKUs, quantities, B2B prices).
  * Story 4: Edit or delete items from ledger.
* **Scope:** Implement `InventoryItem` model, form logic, and the dashboard/ledger catalog card grid view showing stock indicators and live filtering.

### 3. Job Card Creation and Status Lifecycle
* **Blocked by:** Slice 1
* **User stories covered:**
  * Story 5: Create vehicle job cards.
  * Story 13: Job cards status transition.
* **Scope:** Implement `JobCard` model (with status choices) and a check-in workflow layout tracking active jobs and recent entries.

### 4. Job Card Detail Page and Junction Billing Model
* **Blocked by:** Slice 2, Slice 3
* **User stories covered:**
  * Story 6: View job card detail page.
  * Story 7: Add parts to job card.
  * Story 10: Recalculate total bill.
* **Scope:** Introduce the junction `JobCardLineItem` model and build the tabbed `/job-cards/<id>/` detail action workspace. Connect adding/removing parts to automatic `total_bill` recalculations.

### 5. Transactional Stock Deductions & Replenishment
* **Blocked by:** Slice 4
* **User stories covered:**
  * Story 8: Validate stock constraints.
  * Story 9: Atomically deduct inventory stock.
  * Story 12: Replenish stock when line items are deleted.
* **Scope:** Enforce strict stock validations using database-level transaction locks (`select_for_update()`) and atomic database blocks when allocating or returning stock items.

### 6. Historical Invoice Integrity via Catalog Snapshotting
* **Blocked by:** Slice 5
* **User stories covered:**
  * Story 11: Snapshot item pricing on consumption.
  * Scope: Save snapshot columns (`part_name`, `sku`, `unit_price`) directly inside the line items table and set up safe cascade behavior on item delete/update to preserve past billing totals.

### 7. Hyperlocal Search & Radar Map
* **Blocked by:** Slice 2
* **User stories covered:**
  * Story 14: Search neighboring shops.
  * Story 15: Sort nearest-first.
  * Story 16: Display shop contact inline.
  * Story 17: Exclude own workshop & zero-stock.
* **Scope:** Implement database-level distance calculation (Haversine formula + bounding-box pre-filtering) and display results on a tabular lookup alongside an interactive SVG Radar Map.
