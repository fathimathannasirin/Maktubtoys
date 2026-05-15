from .models import Category

def menu_links(request):
    # 1. Fetch all parent categories (excluding subcategories from the top list)
    links = list(Category.objects.filter(parent=None))
    
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
        
    return dict(links=links)