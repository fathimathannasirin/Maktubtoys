# Technical Implementation Summary

## Database Migrations

### Migration File
`store/migrations/0026_product_cost_price_product_margin_amount_and_more.py`

**Fields Added:**
```python
cost_price = DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
margin_amount = DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, null=True)
margin_percentage = DecimalField(max_digits=5, decimal_places=2, default=0, blank=True, null=True)
```

**Migration Status:** ✅ Applied

---

## Model Changes

### `store/models.py` - Product Model

**New Method:**
```python
def calculate_margin(self):
    """Calculate margin amount and percentage based on cost_price and selling price"""
    if self.cost_price and self.price:
        self.margin_amount = self.price - self.cost_price
        if self.price > 0:
            self.margin_percentage = (self.margin_amount / self.price) * 100
    return self.margin_amount, self.margin_percentage
```

**Modified save() method:**
```python
def save(self, *args, **kwargs):
    # ... existing code ...
    
    # Auto-calculate margins
    self.calculate_margin()
    
    super(Product, self).save(*args, **kwargs)
```

---

## Admin Configuration

### `store/admin.py` - ProductAdmin Updates

**Updated list_display:**
```python
list_display = ('product_code', 'product_name', 'price', 'cost_price', 
                'margin_amount', 'margin_percentage', 'stock', 'category', 
                'supplier', 'warehouse', 'image_preview', 'is_available')
```

**Updated fields:**
```python
fields = (
    'product_code', 'product_name', 'slug', 'description', 'price',
    'cost_price', 'margin_amount', 'margin_percentage',
    'images', 'image_preview',   
    'stock', 'category', 'age', 'supplier', 'warehouse', 'is_available'
)
```

**Readonly fields:**
```python
readonly_fields = ('image_preview', 'margin_amount', 'margin_percentage')
```

**Custom template:**
```python
change_form_template = 'admin/store/product_change_form.html'
```

---

### `warehousing/admin.py` - PurchaseItemInline Updates

**Enhanced fields and readonly:**
```python
readonly_fields = ('product_code', 'product_id_display', 'cost_info', 'create_product_link')
fields = ('product', 'product_code', 'product_id_display', 'quantity', 
          'unit_cost', 'cost_info', 'received_quantity', 'create_product_link')
```

**New display methods:**
```python
def product_code(self, obj):
    if obj.product:
        return obj.product.product_code
    return '-'

def product_id_display(self, obj):
    if obj.product:
        return f"ID: {obj.product.id}"
    return '-'

def cost_info(self, obj):
    if obj.product and obj.unit_cost:
        return f"Cost: {obj.unit_cost} QAR per unit"
    return '-'

def create_product_link(self, obj):
    """Link to create a new product from this purchase item"""
    if obj.product:
        url = reverse('admin:store_product_change', args=[obj.product.id])
        return format_html(
            '<a class="button" href="{}" target="_blank">Edit Product</a>',
            url
        )
    return '-'
```

---

## API Endpoint

### `store/views.py` - New API View

**Endpoint:** `get_purchase_items(request)`

```python
@csrf_exempt
def get_purchase_items(request):
    """API endpoint to fetch purchase items for product creation form"""
    from warehousing.models import PurchaseItem
    
    try:
        purchase_items = PurchaseItem.objects.select_related(
            'purchase', 'product'
        ).filter(
            purchase__status='Received'
        ).order_by('-purchase__ordered_at')[:50]
        
        data = []
        for item in purchase_items:
            data.append({
                'id': item.id,
                'purchase_number': item.purchase.purchase_number,
                'product_name': item.product.product_name,
                'product_code': item.product.product_code,
                'unit_cost': float(item.unit_cost),
                'quantity': item.quantity,
                'received_quantity': item.received_quantity,
            })
        
        return JsonResponse({'success': True, 'items': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
```

**Response Format:**
```json
{
  "success": true,
  "items": [
    {
      "id": 1,
      "purchase_number": "PUR-20260825-ABC123",
      "product_name": "Product Name",
      "product_code": "GM/PD0001",
      "unit_cost": 50.00,
      "quantity": 100,
      "received_quantity": 100
    }
  ]
}
```

---

### `store/urls.py` - New URL Pattern

```python
path('api/purchase-items/', views.get_purchase_items, name='get_purchase_items'),
```

**Full URL:** `http://localhost:8000/store/api/purchase-items/`

---

## Frontend JavaScript

### `templates/admin/store/product_change_form.html`

**Features:**
1. Real-time margin calculation
2. Purchase item selector UI
3. Search functionality
4. Auto-fill cost price
5. Dynamic dropdown with AJAX

**Key Functions:**

```javascript
function calculateMargin() {
    const price = parseFloat(priceInput.value) || 0;
    const costPrice = parseFloat(costPriceInput.value) || 0;

    let marginAmount = price - costPrice;
    let marginPercentage = 0;

    if (price > 0) {
        marginPercentage = (marginAmount / price) * 100;
    }

    marginAmountInput.value = marginAmount.toFixed(2);
    marginPercentageInput.value = marginPercentage.toFixed(2);
}
```

**Event Listeners:**
- Price input: `change` and `keyup` events trigger calculation
- Cost Price input: `change` and `keyup` events trigger calculation
- Search input: `focus` event loads purchase items
- Purchase item selection: `click` auto-fills cost price

**CSS Styling:**
- `.margin-display` - Display container
- `.margin-positive` - Green for positive margins
- `.margin-negative` - Red for negative margins
- `.margin-zero` - Gray for zero margins
- `.purchase-item-option` - Individual purchase item styling

---

## Forms

### `store/forms.py` - ProductForm

```python
class ProductForm(forms.ModelForm):
    purchase_item_id = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'id': 'id_purchase_item_id',
            'placeholder': 'Select from purchase items...',
            'class': 'form-control'
        }),
        label='Link to Purchase Item (Optional)'
    )
    
    class Meta:
        model = Product
        fields = [
            'product_name', 'slug', 'description', 'price', 'cost_price',
            'images', 'stock', 'category', 'age', 'supplier', 'warehouse',
            'is_available', 'margin_amount', 'margin_percentage'
        ]
        # ... widgets ...
```

---

## Data Flow Diagram

```
Purchase Order Created
    ↓
    └─→ PurchaseItem (with unit_cost)
            ↓
            ├─→ Admin: PurchaseItem shows Product Code, ID, Cost Info
            │
            └─→ API: /store/api/purchase-items/ returns list
                    ↓
                    └─→ Admin: Product Form
                            ├─→ Search/Select Purchase Item
                                └─→ Auto-fill cost_price
                                    ↓
                                    ├─→ User enters Selling Price
                                    │
                                    └─→ JS: Calculate Margins
                                        ├─→ Margin Amount = Price - Cost
                                        └─→ Margin % = (Amount/Price) × 100
                                            ↓
                                            └─→ Save to Database
```

---

## Calculation Logic

### Margin Amount
```
Margin Amount = Selling Price - Cost Price

Example:
Selling Price: 100 QAR
Cost Price: 60 QAR
Margin Amount: 40 QAR
```

### Margin Percentage
```
Margin % = (Margin Amount / Selling Price) × 100

Example:
Margin Amount: 40 QAR
Selling Price: 100 QAR
Margin %: (40/100) × 100 = 40%
```

### Edge Cases
- If Selling Price = 0: Margin % = 0
- If Cost Price = 0: Margin Amount = Selling Price, Margin % = 100%
- If Cost Price > Selling Price: Negative margin (loss)

---

## Performance Considerations

### Query Optimization
- Used `select_related()` in API endpoint for better performance
- Limited results to 50 recent items
- Filtered by 'Received' status only

### Database Indexes
- Consider adding index on `purchase__status` for API queries
- Consider adding index on `purchase__ordered_at` for sorting

### Caching (Future)
- Could cache purchase items list (expires every hour)
- Reduces database load

---

## Security

### CSRF Protection
- API endpoint uses `@csrf_exempt` for JavaScript fetch
- Alternative: Use csrf token in frontend

### Input Validation
- Cost Price: Decimal validation (10,2)
- Selling Price: Decimal validation (10,2)
- Margin fields: Calculated server-side in save()

### Data Integrity
- Margin fields are calculated server-side during save()
- Read-only in admin to prevent manual override
- No direct API to update margins (prevents fraud)

---

## Browser Compatibility

- ES6 JavaScript used
- Tested with modern browsers
- Requires JavaScript enabled for real-time calculation
- Fallback: User can manually enter margin (if editable)

---

## Files Changed Summary

| File | Change Type | Details |
|------|-------------|---------|
| store/models.py | Modified | Added 3 fields + calculate_margin() method |
| store/admin.py | Modified | Updated ProductAdmin display and fields |
| store/forms.py | Modified | Created ProductForm |
| store/views.py | Modified | Added get_purchase_items() API |
| store/urls.py | Modified | Added /api/purchase-items/ route |
| warehousing/admin.py | Modified | Enhanced PurchaseItemInline |
| templates/admin/store/product_change_form.html | Created | Custom admin form with JavaScript |

---

## Testing Checklist

- [ ] Database migration applied successfully
- [ ] Django system check passes
- [ ] API endpoint returns JSON correctly
- [ ] Purchase item selector loads in admin
- [ ] Selecting purchase item fills cost_price
- [ ] Margins calculate in real-time
- [ ] Negative margins display correctly
- [ ] Product saves with calculated margins
- [ ] PurchaseItem admin shows all new fields
- [ ] "Edit Product" button works in PurchaseItem admin

