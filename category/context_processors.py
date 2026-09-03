from .models import Category
from store.models import Product
from datetime import datetime
import random

def menu_links(request):
    # 1. Fetch all parent categories (excluding subcategories from the top list)
    links = list(Category.objects.filter(parent=None))
    age_links = Product.objects.filter(
        is_available=True,
        age__isnull=False,
    ).order_by('age').values_list('age', flat=True).distinct()
    
    # 2. Find "Today's Deal" and move it to the top
    pinned_category = None
    for i, category in enumerate(links):
        # We check iexact to be safe with capital letters
        if category.category_name.strip().lower() == "today's deal" or \
           category.category_name.strip().lower() == "todays deal":
            pinned_category = links.pop(i)
            break
    
    # 3. If found, insert it at the very first position (index 0)
    if pinned_category:
        links.insert(0, pinned_category)

    return {
        'links': links,
        'age_links': age_links,
    }

def hourly_featured_categories(request):
    all_categories = list(Category.objects.all())
    count = len(all_categories)

    if count == 0:
        return {'footer_categories': []}

    # Generate a seed based on current year, day of year, and hour
    now = datetime.now()
    hourly_seed = int(f'{now.year}{now.timetuple().tm_yday}{now.hour}')

    # Seed the RNG deterministically so all users see the exact same 4 categories each hour
    rng = random.Random(hourly_seed)

    if count <= 4:
        featured = all_categories
    else:
        featured = rng.sample(all_categories, 4)

    return {'footer_categories': featured}