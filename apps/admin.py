from parler.admin import TranslatableAdmin
from django.contrib.admin import register, ModelAdmin
from apps.models import Category, Product, SiteSettings, Order, Payment


@register(Category)
class CategoryAdmin(TranslatableAdmin):
    exclude = ('slug',)


@register(Product)
class ProductAdmin(TranslatableAdmin):
    exclude = ('slug',)


@register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    pass


@register(Order)
class OrderAdmin(ModelAdmin):
    pass


@register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("card_number", "user", "amount", "status", "receipt")

    def save_model(self, request, obj, form, change):
        if obj.status == Payment.PaymentStatus.CANCEL and obj.user:
            obj.user.balance += obj.amount
            obj.user.save()
        super().save_model(request, obj, form, change)
