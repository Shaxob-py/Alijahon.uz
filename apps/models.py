from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models import Model, ForeignKey, CASCADE, ImageField, SET_NULL, TextChoices
from django.db.models.fields import SmallIntegerField, TextField, DateTimeField, URLField, CharField, DecimalField, \
    SlugField, IntegerField, BooleanField, DateField, EmailField
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel


class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user_object(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("The given phone_number must be set")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.password = make_password(password)
        return user

    def _create_user(self, phone_number, password, **extra_fields):
        """
        Create and save a user with the given phone_number, and password.
        """
        user = self._create_user_object(phone_number, password, **extra_fields)
        user.save(using=self._db)
        return user

    async def _acreate_user(self, phone_number, password, **extra_fields):
        """See _create_user()"""
        user = self._create_user_object(phone_number, password, **extra_fields)
        await user.asave(using=self._db)
        return user

    def create_user(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    create_user.alters_data = True

    async def acreate_user(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return await self._acreate_user(phone_number, password, **extra_fields)

    acreate_user.alters_data = True

    def create_superuser(self, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)

    create_superuser.alters_data = True

    async def acreate_superuser(
            self, phone_number=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return await self._acreate_user(phone_number, password, **extra_fields)

    acreate_superuser.alters_data = True


class User(AbstractUser):
    class RoleType(TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        DELIVERER = "deliverer", "Deliverer"
        USER = "user", "User"

    phone_number = CharField(max_length=20, unique=True)
    username = CharField(unique=True, max_length=255, null=True, blank=True)
    email = EmailField(unique=True, null=True, blank=True)
    objects = CustomUserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []
    telegram_id = CharField(max_length=50, default="")
    about = TextField(default="")
    address = CharField(max_length=255, default="")
    district = ForeignKey("apps.District", SET_NULL, null=True, blank=True, related_name="users")
    balance = DecimalField(max_digits=10, decimal_places=0, default=0)
    role = CharField(max_length=10, choices=RoleType, default=RoleType.USER)

    def wishlist_products(self):
        return list(self.wishlist.all().values_list("product__pk", flat=True))


class Region(Model):
    name = CharField(max_length=255)


class District(Model):
    name = CharField(max_length=255)
    region = ForeignKey("apps.Region", CASCADE, related_name="districts")


class BaseSlug(TranslatableModel):
    slug = SlugField(null=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        name = self.safe_translation_getter('name', any_language=True) or ""
        slug = slugify(name)
        query = self.__class__.objects.filter(slug=slug).exclude(pk=self.pk)
        while query.exists():
            slug += "-1"
            query = self.__class__.objects.filter(slug=slug).exclude(pk=self.pk)
        self.slug = slug
        return super().save(*args, **kwargs)


class Category(BaseSlug):
    icon = URLField()
    translations = TranslatedFields(
        name=models.CharField("name", max_length=255)
    )


class Product(BaseSlug):
    image = ImageField(upload_to="products/")
    translations = TranslatedFields(
        name=models.CharField("name", max_length=200),
        description=RichTextUploadingField("description")
    )
    price = DecimalField(max_digits=9, decimal_places=0)
    quantity = SmallIntegerField(default=1)
    category = ForeignKey('apps.Category', CASCADE, related_name='products')
    created_at = DateTimeField(auto_now_add=True)
    update_at = DateTimeField(auto_now=True)
    seller_price = DecimalField(default=0, decimal_places=0, max_digits=9)
    message_id = CharField(max_length=255)


class Order(Model):
    class StatusType(TextChoices):
        NEW = "new", _("New")
        READY_TO_DELIVERY = "ready to delivery", _("Ready To Delivery")
        DELIVERING = "delivering", _("Delivering")
        DELIVERED = "delivered", _("Delivered")
        NOT_CALL = "not call", _("Not Call")
        CANCELED = "canceled", _("Canceled")
        ARCHIVED = "archived", _("Archived")

    delivered_date = DateField(null=True, blank=True)
    customer = ForeignKey("apps.User", SET_NULL, null=True, blank=True, related_name="orders")
    product = ForeignKey("apps.Product", SET_NULL, null=True, blank=True, related_name="orders")
    fullname = CharField(max_length=255)
    phone_number = CharField(max_length=20)
    quantity = SmallIntegerField(default=1)
    total = DecimalField(max_digits=9, decimal_places=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    thread = ForeignKey("apps.Thread", SET_NULL, null=True, blank=True, related_name="orders")
    status = CharField(choices=StatusType, default=StatusType.NEW)
    comment = TextField(null=True, blank=True)
    district = ForeignKey("apps.District", SET_NULL, null=True, blank=True, related_name="orders")
    operator = ForeignKey("apps.User", SET_NULL, null=True, blank=True, related_name="operator_orders")
    hold = BooleanField(default=False)


class WishList(Model):
    user = ForeignKey('apps.User', CASCADE, related_name="wishlist")
    product = ForeignKey("apps.Product", CASCADE, related_name="wishlist")

    class Meta:
        unique_together = ("user", "product")


class Thread(Model):
    owner = ForeignKey('apps.User', CASCADE, related_name='threads')
    product = ForeignKey('apps.Product', CASCADE, related_name='threads')
    discount = DecimalField(decimal_places=0, max_digits=9)
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    visit_count = IntegerField(default=0)

    @property
    def discount_price(self):
        return self.product.price - self.discount


class SiteSettings(Model):
    delivery_price = DecimalField(max_digits=9, decimal_places=0)
    competition = ImageField(upload_to="site/")
    competition_start = DateField(null=True)
    competition_end = DateField(null=True)
    competition_description = RichTextUploadingField(null=True)


class Payment(Model):
    class PaymentStatus(TextChoices):
        REVIEWED = "reviewed", "Reviewed"
        COMPLETED = "completed", "Completed"
        CANCEL = "cancel", "Cancel"

    amount = DecimalField(max_digits=9, decimal_places=0)
    user = ForeignKey('apps.User', SET_NULL, null=True, blank=True, related_name="payments")
    receipt = ImageField(upload_to="payments/", null=True, blank=True)
    comment = TextField(null=True, blank=True)
    status = CharField(choices=PaymentStatus, max_length=255, default=PaymentStatus.REVIEWED)
    card_number = CharField(max_length=20)
    pay_at = DateTimeField(auto_now_add=True)
