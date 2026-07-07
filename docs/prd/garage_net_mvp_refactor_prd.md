# Product Requirement Document (PRD) — GarageNET MVP Refactoring & Hyperlocal Search Optimization

## Problem Statement

The current GarageNET codebase has critical architectural flaws and data flow limitations that block it from being a viable B2B MVP:
1. **Flawed Hyperlocal Search:** The P2P search calculates distances in Python memory for *all* inventory items in the database. As the database grows, this will result in severe performance degradation and memory exhaustion.
2. **Disconnected Billing & Stock Flow:** Job Cards and Inventory Items are completely decoupled. Mechanics cannot record which parts were consumed by a job, stock counts are not updated when parts are used, and the total bill must be entered manually.
3. **Audit & Invoice Vulnerability:** If a parts catalog item is updated (due to supplier pricing changes) or deleted, any historical Job Cards pointing to it will either change their total bill or crash/delete the line item entirely.
4. **Missing Detail Flow:** There is no detail page to view a specific Job Card or manage its line items, and no direct inline contact information for neighboring shops in the search results.

---

## Solution

We will refactor the codebase to establish a reliable, database-backed transactional flow and a performant hyperlocal search engine:
1. **Database-Level Proximity Engine:** Implement a bounding box pre-filter followed by database-level Haversine distance calculations directly in PostgreSQL, returning sorted results without loading records into memory.
2. **Junction Billing Model:** Introduce a `JobCardLineItem` model to track inventory items assigned to jobs and automatically calculate the bill.
3. **Catalog Snapshotting:** Snapshot the part name, SKU, and unit price at the time of consumption to ensure historical invoice integrity even if catalog items are deleted or modified.
4. **Transactional Stock Deductions:** Enforce strict inventory validations using database-level transaction locks (`select_for_update()`) to prevent negative inventory and ensure atomic consistency.
5. **Dedicated Job Detail UI:** Provide a `/job-cards/<id>/` detail page to manage line items and display a clean invoice summary, and render inline shop contact details inside the search results.

---

## User Stories

1. As a workshop owner, I want to register my shop with coordinates and address, so that neighboring shops can find me.
2. As a workshop owner, I want to update my profile details, so that my contact details remain accurate.
3. As a mechanic, I want to log my inventory items with names, SKUs, quantities, and B2B prices, so that I can track my active stock.
4. As a mechanic, I want to edit or delete inventory items from my ledger, so that my parts catalog stays clean.
5. As a mechanic, I want to create a Job Card for a customer's vehicle, so that I can track the repair work.
6. As a mechanic, I want to view a dedicated Job Card Detail page, so that I can see the invoice summary and manage the parts used for that vehicle.
7. As a mechanic, I want to add inventory parts to a Job Card on its detail page, so that they are added to the customer's bill.
8. As a mechanic, I want the system to block me from adding a part if requested quantity exceeds my current stock, so that I don't overbook parts.
9. As a mechanic, I want the system to immediately deduct stock from the inventory when a part is added to a Job Card, so that other mechanics don't try to use or sell the same part.
10. As a mechanic, I want the system to automatically recalculate the Job Card's total bill when line items are added or removed, so that I don't have to calculate it manually.
11. As a mechanic, I want the system to snapshot the part name, SKU, and unit price on the Job Card's line items, so that historical invoices remain unchanged even if the catalog item's price changes or the item is deleted.
12. As a mechanic, I want to delete a line item from a Job Card, so that I can correct errors and return the parts back to my stock immediately.
13. As a mechanic, I want to update the status of a Job Card (e.g. from Received to In-Progress or Ready), so that I can manage the work lifecycle.
14. As a mechanic, I want to search for a part across neighboring shops within a specified radius (e.g., 50 km), so that I can quickly source missing items.
15. As a mechanic, I want the search results to be sorted nearest to furthest, so that I can contact the closest shop first.
16. As a mechanic, I want the search results to display each workshop's direct contact details (shop name, phone number, and address) inline, so that I can call them immediately or drive to get the part without extra navigation clicks.
17. As a mechanic, I want the search to exclude my own workshop's inventory and any parts with zero quantity, so that I only see available parts from other shops.

---

## Implementation Decisions

### Modules & Database Models
* **`JobCardLineItem` Junction Model:**
  * Foreign key to `JobCard` (`on_delete=models.CASCADE`).
  * Foreign key to `InventoryItem` (`on_delete=models.SET_NULL, null=True`).
  * Char fields for `part_name` and `sku`, Decimal field for `unit_price` to store the billing snapshot.
  * Positive Integer field for `quantity`.
* **`JobCard` Updates:**
  * Keep `total_bill` as a database field.
  * Add a method to calculate the sum of `quantity * unit_price` of associated line items and save the updated total.

### Hyperlocal Search Optimization
* **Bounding Box Filter:** In the search view, calculate minimum/maximum latitude and longitude bounds in Python using the search radius and center coordinates. Use these bounds to pre-filter items in SQL before calculating precise distance.
* **Database-Level Haversine Formula:** Utilize Django's database math functions (`Sin`, `Cos`, `ASin`, `Sqrt`, `Radians`) to calculate distances in the SQL query, annotating the queryset and sorting using `.order_by()`.

### Stock Concurrency & Integrity
* **Atomic Transactions:** Wrap stock deductions and replenishment within `transaction.atomic()`.
* **Pessimistic Locking:** Use `.select_for_update()` when querying `InventoryItem` for stock adjustments to prevent race conditions during concurrent modifications.
* **Strict Validation:** Assert `InventoryItem.quantity >= requested_quantity` before creating a line item.

### UI & Page Flow
* **Job Card Detail Page:** A dedicated view showing the Job Card metadata, status tracker, active line items table with "Delete" buttons, and an "Add Part" form containing an inventory dropdown and quantity field.
* **P2P Search UI:** A single search view with radius selection options and results rendered as direct contact cards containing phone number links (`tel:`) and physical addresses.

---

## Testing Decisions

* **External Behavior Focus:** Tests should assert database state changes and HTTP response content/redirection, avoiding checking internal private methods.
* **Geospatial Distance Testing:** Proximity verification tests using predefined test workshops (e.g., Pune to Mumbai distance validations).
* **Billing and Stock Integrity Tests:**
  * Add/Delete line item assertions verifying corresponding stock levels and `total_bill` updates.
  * Race condition simulations (using test transactions) verifying that database-level locking blocks negative allocations.
  * Price change assertions verifying that deleting or changing the price of a catalog item leaves past job card totals unaffected.

---

## Out of Scope

* Online payment gateways, automatic ordering, or messaging systems between workshops.
* Custom user roles/permissions (e.g. separate billing clerk vs. mechanic roles).
* Automated HTML5 browser geolocation detection (MVP will require manual entry of coordinates).

---

## Further Notes

* All templates will leverage the existing Bootstrap 5 style setup to remain clean and responsive.
* All database changes will be fully supported by Django migrations.
