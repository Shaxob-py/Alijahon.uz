import datetime
import re
from symtable import Class

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.forms import Form, ModelForm
from django.forms.fields import CharField
from django.utils.translation import gettext as _

from apps.models import User, Order, Product, Thread, SiteSettings, Payment


class AuthForm(Form):
    phone_number = CharField(max_length=20)
    password = CharField(max_length=8)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        return re.sub(r'\D', '', phone_number)

    def clean(self):
        data = self.cleaned_data
        password = data.get('password')
        phone_number = data.get('phone_number')
        query = User.objects.filter(phone_number=phone_number)
        if query.exists():
            user = query.first()
            if check_password(password, user.password):
                self.user = user
            else:
                raise ValidationError(_('Wrong Password!'))
        else:
            user = self.save()
            self.user = user
        return data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create(phone_number=data.get('phone_number'))
        user.set_password(data.get('password'))
        user.save()
        return user


class ProfileModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileModelForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = User
        fields = "first_name", "last_name", "district", "address", "telegram_id", "about"


class ChangePasswordForm(Form):
    old_password = CharField(max_length=255)
    new_password = CharField(max_length=255)
    confirm_password = CharField(max_length=255)

    def clean_confirm_password(self):
        new_password = self.cleaned_data.get('new_password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if new_password != confirm_password:
            raise ValidationError(_("Passwords don't match"))
        return confirm_password

    def update(self, user):
        new_password = self.cleaned_data.get('new_password')
        user.set_password(new_password)
        user.save()


class OrderModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['total'].required = False
        self.fields['thread'].required = False

    class Meta:
        model = Order
        fields = 'phone_number', 'fullname', 'product', 'total', 'thread'

    def clean_total(self):
        product = self.cleaned_data.get('product')
        thread_id = self.data.get('thread', -1)
        thread = Thread.objects.filter(pk=thread_id).first()
        site = SiteSettings.objects.first()
        total_price = product.price + site.delivery_price
        if thread:
            total_price -= thread.discount
        return total_price

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        return re.sub("\D'", "", phone_number)


class ThreadModelForm(ModelForm):
    class Meta:
        model = Thread
        fields = "name", "product", "discount"

    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        product = self.cleaned_data.get('product')

        if product.seller_price < discount:
            raise ValidationError(_("The discount exceeded the specified limit!"))
        return discount


class PaymentModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['user'].required = False

    class Meta:
        model = Payment
        fields = "card_number", "card_number", "amount", 'user'

    def clean_user(self):
        return self.user

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number').replace(" ", "")
        if not card_number.isdigit() or len(card_number) != 16:
            raise ValidationError(_("Invalid card number!"))

        return card_number

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        user = self.user
        if amount > 1000:
            raise ValidationError(_("The amount exceeds the allowed limit!"))

        if amount >= user.balance:
            raise ValidationError("Mablah etarli emas")
        return amount


class OrderUpdateModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        self.user = kwargs.pop('operator', None)  # 🔁 operator -> user deb qabul qilamiz
        super().__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ('quantity', 'district', 'status', 'comment', 'thread', 'delivered_date', 'operator')

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        order = self.order
        if not order or not order.product:
            raise ValidationError("Buyurtma yoki mahsulot mavjud emas")

        if quantity > order.product.quantity:
            raise ValidationError("Maxsulot yetarli emas")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        thread = cleaned_data.get('thread')
        order = self.order

        if not order or not quantity:
            return cleaned_data

        site = SiteSettings.objects.first()
        if not site:
            raise ValidationError("Sayt sozlamalari topilmadi")

        # total hisoblash
        if thread:
            self.total = thread.discount_price * quantity + site.delivery_price
        else:
            self.total = order.product.price * quantity + site.delivery_price

        # bonus hisoblash
        if cleaned_data.get('status') == Order.StatusType.DELIVERED and thread and self.user:
            self.bonus = thread.discount_price
        else:
            self.bonus = 0

        return cleaned_data

    def clean_operator(self):
        return self.user  # operatorni avtomatik belgilash

    def clean_delivered_date(self):
        delivered_date = self.cleaned_data.get('delivered_date')
        if delivered_date and delivered_date < datetime.date.today():
            raise ValidationError("Yetkazilgan sana hozirgi kundan keyin bo'lishi kerak")
        return delivered_date
