# Quick Start Guide: Purchase to Product Workflow

## 📦 What You Can Do Now

### 1. **Link Products to Purchases**
   - When creating a product, you can now link it to a purchase item
   - This automatically fills the **Cost Price** field
   - All recent received purchases are available in the dropdown

### 2. **Real-Time Margin Calculation**
   - Enter or edit the **Selling Price**
   - **Margin Amount** and **Margin %** calculate automatically
   - No need to manually calculate - it updates as you type!

### 3. **View Purchase Details in Products**
   - In the **Products** list view, see:
     - Cost Price
     - Margin Amount
     - Margin Percentage
   - Easily identify profitable products

### 4. **Quick Access from Purchases**
   - In Purchase admin, each item shows:
     - Product Code
     - Product ID  
     - Cost Info
     - "Edit Product" button for quick access

---

## 🚀 Step-by-Step Usage

### Creating a Product from a Purchase

1. **Go to:** Admin > Store > Products > Add Product

2. **Find the "Link to Purchase Item" section** at the top

3. **Click on the search field** to see recent purchase items
   ```
   Input field: "Link to Purchase Item (Optional)"
   ```

4. **Search or select** a purchase item
   ```
   Display: "PUR-20260825-ABC123 - Sample Product (GM/PD0001)"
   Shows: "Cost: 50.00 QAR | Qty: 100/100"
   ```

5. **Click to select** - Cost Price is automatically filled!

6. **Enter Selling Price** in the Price field

7. **Watch the magic** ✨
   - **Margin Amount** = Selling Price - Cost Price
   - **Margin %** = (Margin Amount / Selling Price) × 100

8. **Fill other required fields:**
   - Product Name (must be unique)
   - Category
   - Image
   - Stock quantity
   - etc.

9. **Save Product** - Margins are saved automatically!

---

## 📊 Understanding the Fields

| Field | What It Is | Auto-Calculated? |
|-------|-----------|------------------|
| **Cost Price** | What you paid for the product | Can be filled from Purchase Item |
| **Price** (Selling Price) | What customers pay | Manual entry |
| **Margin Amount** | Profit per unit (Price - Cost) | ✅ Yes |
| **Margin Percentage** | Profit as % of selling price | ✅ Yes |

### Example Calculation:
```
Cost Price:        50.00 QAR
Selling Price:    100.00 QAR
─────────────────────────────
Margin Amount:     50.00 QAR
Margin %:          50.00 % (calculated as: 50/100 × 100)
```

---

## 🔧 Admin Interface Features

### In the Product Add/Edit Form:
- ✅ Purchase item dropdown with search
- ✅ Auto-fill cost price
- ✅ Real-time margin updates
- ✅ Readonly margin fields (automatically calculated)

### In the Purchase Admin:
- ✅ Each item shows Product ID and Code
- ✅ Shows unit cost information
- ✅ "Edit Product" button for linked products

### In the Products List View:
- ✅ Cost Price column
- ✅ Margin Amount column
- ✅ Margin % column
- ✅ Easily spot high/low margin products

---

## 🎯 Use Cases

### 1. **Bulk Purchasing & Pricing**
   - Import purchase order items
   - Link them to products
   - Set selling price based on margin targets
   - All margins calculate automatically

### 2. **Profit Analysis**
   - Check margin % in products list
   - Identify unprofitable products
   - Adjust prices as needed

### 3. **Supplier Cost Tracking**
   - Cost price linked to purchases
   - See which suppliers are more expensive
   - Manage supplier relationships

### 4. **Pricing Strategy**
   - Set margin targets (e.g., 40% margin)
   - System calculates required selling price
   - Maintain consistent profitability

---

## ⚠️ Important Notes

- **Cost Price can be empty** (marked as optional in model)
- **Margin fields are read-only** in the form (auto-calculated)
- **Purchase item linking is optional** (you can enter cost price manually)
- **API endpoint** at `/store/api/purchase-items/` returns JSON
- **Migration required** before using (already applied)

---

## 🔍 Troubleshooting

### Purchase items not showing?
- Make sure Purchase status = "Received"
- Check browser console (F12) for errors
- Try refreshing the admin page

### Margins showing zero?
- Ensure both Cost Price AND Selling Price are filled
- Both must be > 0 for calculation
- Try entering a selling price manually

### Getting an error when saving?
- Product Name must be unique
- Category is required
- Image is required
- All required fields must be filled

---

## 📱 API Endpoint

**URL:** `GET /store/api/purchase-items/`

**Returns:** List of recent received purchase items with:
- ID
- Purchase Number
- Product Name & Code
- Unit Cost
- Quantities

Use this to integrate with external systems or mobile apps.

---

## 💡 Pro Tips

1. **Set a default margin %** in your pricing strategy
   - Calculate required selling price = Cost Price ÷ (1 - Margin%)
   - Example: For 40% margin on 50 QAR cost: 50 ÷ 0.6 = 83.33 QAR

2. **Review margins regularly**
   - Go to Products list
   - Sort by Margin %
   - Identify opportunities for price adjustment

3. **Use cost price for analytics**
   - Better profitability tracking
   - Compare actual vs. expected margins
   - Supplier cost management

4. **Automate pricing** (future enhancement)
   - Could auto-calculate selling price from margin target
   - Auto-apply markups by category
   - Seasonal price adjustments

---

## 📞 Support

For issues or feature requests:
1. Check the WORKFLOW_DOCUMENTATION.md for detailed specs
2. Review the purchase item API response
3. Check Django admin error messages
4. Review browser console for JavaScript errors

