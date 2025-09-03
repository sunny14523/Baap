from django import template
from mainapp.models import Product

register = template.Library()

@register.filter
def get_product(product_id):
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None
