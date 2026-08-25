# Purchase to Product Workflow Implementation

## Overview
This implementation creates a seamless workflow to link Purchase entries with Product creation, including automatic cost price population and real-time margin calculations.

## Components Implemented

### 1. **Product Model Enhancements** (`store/models.py`)
- ✅ Added `cost_price` field (DecimalField, nullable)
- ✅ Added `margin_amount` field (DecimalField, auto-calculated)
- ✅ Added `margin_percentage` field (DecimalField, auto-calculated)
- ✅ Added `calculate_margin()` method for margin computation
- ✅ Modified `save()` method to auto-calculate margins

**Migration:** `store/migrations/0026_product_cost_price_product_margin_amount_and_more.py`

### 2. **Product Admin Updates** (`store/admin.py`)
- ✅ Updated `ProductAdmin.list_display` to show cost_price, margin_amount, margin_percentage
- ✅ Updated fields to include cost_price and margin fields (read-only)
- ✅ Added custom template: `admin/store/product_change_form.html`

### 3. **Purchase Item Admin Enhancement** (`warehousing/admin.py`)
- ✅ Enhanced `PurchaseItemInline` with:
  - Product Code display
  - Product ID display  
  - Cost Info display
  - Edit Product link for quick access
  - Readonly fields for easy reference

### 4. **API Endpoint** (`store/views.py`)
- ✅ Created `get_purchase_items()` API endpoint
- ✅ Returns recent received purchase items with:
  - Purchase number
  - Product name & code
  - Unit cost (cost price)
  - Quantities

**Endpoint URL:** `/store/api/purchase-items/`

### 5. **Admin Template** (`templates/admin/store/product_change_form.html`)
- ✅ Real-time margin calculation JavaScript
- ✅ Purchase item selector UI
- ✅ Search functionality for purchase items
- ✅ Auto-fill cost_price from selected purchase item
- ✅ Live margin calculations as user types

**Calculations:**
```
Margin Amount = Selling Price - Cost Price
Margin % = (Margin Amount / Selling Price) × 100
```

### 6. **Product Form** (`store/forms.py`)
- ✅ Created custom `ProductForm` with purchase item linking
- ✅ Added purchase_item_id field (optional dropdown)
- ✅ Integrated margin display fields

## Workflow Usage

### Step 1: Create Purchase Entry
1. Go to **Warehousing** > **Purchases**
2. Create/receive a purchase order with items
3. Notice the PurchaseItem inline shows:
   - Product Code (e.g., GM/PD0001)
   - Product ID
   - Cost/Unit Info
   - Edit Product link

### Step 2: Create Product from Purchase
1. Go to **Store** > **Products** > **Add Product**
2. You'll see a **"Link to Purchase Item"** section at the top
3. Click on the search field to view recent purchase items
4. Select a purchase item from the dropdown
5. Cost price is **auto-populated**
6. Enter the **Selling Price**

### Step 3: Auto-Calculation
As you adjust prices:
- **Margin Amount** = Selling Price - Cost Price
- **Margin %** = (Margin Amount / Selling Price) × 100

Both fields update in **real-time** as you type!

## Database Fields Added

| Field | Type | Default | Nullable |
|-------|------|---------|----------|
| cost_price | DecimalField(10,2) | 0 | Yes |
| margin_amount | DecimalField(10,2) | 0 | Yes |
| margin_percentage | DecimalField(5,2) | 0 | Yes |

## API Responses

### GET `/store/api/purchase-items/`

**Success Response:**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "purchase_number": "PUR-20260825-ABC123",
      "product_name": "Sample Product",
      "product_code": "GM/PD0001",
      "unit_cost": 50.00,
      "quantity": 100,
      "received_quantity": 100
    }
  ]
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Frontend Features

### Purchase Item Selector
- Search purchase items in real-time
- Display: `Purchase# - ProductName (Code)`
- Shows: `Cost: X QAR | Qty: received/total`
- Click to select and auto-fill cost_price

### Margin Calculation
- **Live calculation** as user types price
- **Status indicators:**
  - ✅ Green: Positive margin
  - ❌ Red: Negative margin
  - ⚪ Gray: Zero margin or no cost price

### Readonly Fields (Auto-Calculated)
- `margin_amount`: Automatically calculated
- `margin_percentage`: Automatically calculated

## Integration Points

### Django Admin
- Product admin shows cost and margins
- PurchaseItem inline links to products
- Edit Product button in purchase items

### API Usage
- Fetch purchase items for frontend integration
- Used by admin JavaScript

### Forms
- ProductForm includes all margin fields
- Purchase item selector dropdown

## Next Steps (Optional Enhancements)

1. **Bulk Product Creation**
   - Create multiple products from a single purchase order
   - Template-based pricing rules

2. **Cost Price History**
   - Track cost price changes over time
   - Average cost calculation

3. **Margin Reports**
   - Dashboard showing margin by category
   - Product profitability reports

4. **Auto-Margin Rules**
   - Set margin % and auto-calculate selling price
   - Apply markups by supplier or category

5. **Purchase Item Status**
   - Track which purchase items have linked products
   - Show unmapped items in a report

## Files Modified

1. `store/models.py` - Added margin fields and calculation
2. `store/admin.py` - Updated ProductAdmin display
3. `store/forms.py` - Created ProductForm with purchase linking
4. `store/views.py` - Added purchase items API endpoint
5. `store/urls.py` - Added API route
6. `warehousing/admin.py` - Enhanced PurchaseItemInline
7. `templates/admin/store/product_change_form.html` - Created with JS

## Testing Checklist

- [ ] Create a Purchase order with items
- [ ] Mark purchase as "Received"
- [ ] Go to Add Product
- [ ] Verify purchase items dropdown loads
- [ ] Select a purchase item
- [ ] Verify cost_price is populated
- [ ] Edit selling price
- [ ] Verify margins calculate in real-time
- [ ] Save product
- [ ] Verify margins are saved to database
- [ ] Check PurchaseItem admin shows product info correctly

## Troubleshooting

**Purchase items not showing:**
- Ensure purchases have status = "Received"
- Check browser console for API errors
- Verify `/store/api/purchase-items/` returns data

**Margins not calculating:**
- Ensure both price and cost_price have values
- Check browser developer tools for JavaScript errors
- Verify margin fields are not locked in readonly mode (for calculation)

**Product not saving:**
- Check for required field errors (slug, category, etc.)
- Verify image/file upload permissions
- Check Django admin error messages

