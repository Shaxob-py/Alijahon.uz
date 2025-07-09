import datetime

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView, ListView, FormView, UpdateView, DetailView, CreateView

from apps.forms import AuthForm, ProfileModelForm, ChangePasswordForm, OrderModelForm, ThreadModelForm, \
    PaymentModelForm, OrderUpdateModelForm
from apps.models import Category, Product, User, Region, District, Order, WishList, Thread, SiteSettings, Payment




class HomeListView(ListView):
    queryset = Category.objects.all()
    template_name = 'apps/home.html'
    context_object_name = "categories"

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['products'] = Product.objects.all()
        return data


class AuthFormView(FormView):
    form_class = AuthForm
    success_url = reverse_lazy('home')
    template_name = 'apps/auth/auth-page.html'

    def form_valid(self, form):
        user = form.user
        login(self.request, user)
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(self.request)
        return redirect('auth')


class ProductListView(ListView):
    queryset = Product.objects.select_related('category').all()
    template_name = 'apps/product-list.html'
    context_object_name = "products"

    def get_queryset(self):
        c_slug = self.request.GET.get('category_slug')
        query = super().get_queryset()
        if c_slug:
            query = query.filter(category__slug=c_slug)
        return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['categories'] = Category.objects.all()
        data['c_slug'] = self.request.GET.get('category_slug')
        return data


class OrderFormView(CreateView):
    queryset = Product.objects.all()
    form_class = OrderModelForm
    template_name = 'apps/order/order-form.html'

    def get_context_data(self, **kwargs):
        product_slug = self.kwargs.get('slug')
        data = super().get_context_data(**kwargs)
        data['product'] = Product.objects.get(slug=product_slug)
        return data

    def form_valid(self, form):
        order = form.save(commit=False)
        order.customer = self.request.user
        order.save()
        site = SiteSettings.objects.first()
        return render(self.request, 'apps/order/order-receive.html', context={'order': order, 'site': site})


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    queryset = User.objects.all()
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')
    form_class = ProfileModelForm
    pk_url_kwarg = None
    context_object_name = "user"

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data

    def form_invalid(self, form):
        pass


class SearchProductListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/search-product-list.html'
    context_object_name = "products"

    def get_queryset(self):
        search = self.request.GET.get('search')
        query = Product.objects.filter(
            Q(translations__name__icontains=search) | Q(translations__description__icontains=search) | Q(
                category__translations__name__icontains=search))
        return query.distinct()


class UserChangePassword(LoginRequiredMixin, FormView):
    form_class = ChangePasswordForm
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        old_password = form.cleaned_data.get("old_password")
        user = self.request.user
        if not check_password(old_password, user.password):
            messages.error(self.request, _("Password invalid !"))
            return super().form_invalid(form)
        form.update(user)
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


def district_view(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id).values("id", "name")
    data = [{"id": district.get("id"), "name": district.get("name")} for district in districts]
    return JsonResponse(data, safe=False)


def wishlist_view(request, pk):
    query = WishList.objects.filter(product_id=pk, user=request.user)
    clicked = False
    if not query.exists():
        clicked = True
        WishList.objects.create(user=request.user, product_id=pk)
    else:
        query.delete()
    return JsonResponse({"clicked": clicked})


class WishListView(ListView):
    queryset = WishList.objects.all()
    template_name = 'apps/auth/wishlist.html'
    context_object_name = "wishlist"

    def get_queryset(self):
        query = super().get_queryset().filter(user=self.request.user)
        return query


class OrderListView(LoginRequiredMixin, ListView):
    queryset = Order.objects.all()
    template_name = 'apps/order/order-list.html'
    context_object_name = "orders"

    def get_queryset(self):
        query = super().get_queryset().filter(customer=self.request.user)
        return query


class ThreadCreateView(CreateView):
    queryset = Thread.objects.all()
    template_name = 'apps/market/market-list.html'
    form_class = ThreadModelForm
    success_url = reverse_lazy('thread-list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()
        data['categories'] = Category.objects.all()
        return data

    def form_valid(self, form):
        thread = form.save(commit=False)
        thread.owner = self.request.user
        thread.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class ThreadListView(LoginRequiredMixin, ListView):
    queryset = Thread.objects.all().order_by('-created_at')
    template_name = 'apps/market/thread-list.html'
    context_object_name = 'threads'

    def get_queryset(self):
        query = super().get_queryset().filter(owner=self.request.user)
        return query


class ThreadDetailView(DetailView):
    queryset = Thread.objects.all()
    template_name = 'apps/order/order-form.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        thread = data.get("thread")
        thread.visit_count += 1
        thread.save()
        data['product'] = self.object.product
        return data


class MarketListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/market/market-list.html'
    context_object_name = 'products'

    def get_queryset(self):
        category_slug = self.request.GET.get('category_slug')
        query = super().get_queryset()
        if category_slug == 'top':
            query = query.annotate(order_count=Count('orders')).order_by('-order_count')
        elif category_slug:
            query = query.filter(category__slug=category_slug)
        return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['categories'] = Category.objects.all()
        data['c_slug'] = self.request.GET.get('category_slug')
        return data


class StatisticListView(LoginRequiredMixin, ListView):
    queryset = Thread.objects.all()
    template_name = 'apps/market/statistics.html'
    context_object_name = 'threads'

    def get_queryset(self):
        period = self.request.GET.get('period')
        now = datetime.datetime.now()
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_yesterday = start_of_today - datetime.timedelta(days=1)
        start_of_week = start_of_today - datetime.timedelta(days=7)
        start_of_month = start_of_today.replace(day=1)
        start_of_all = datetime.datetime(2000, 1, 1)

        time_range = {
            "today": (start_of_today, now),
            "last_day": (start_of_yesterday, start_of_today),
            "wekly": (start_of_week, now),
            "monthly": (start_of_month, now),
            "all": (start_of_all, now),
        }
        range_time = time_range.get(period)
        query = Thread.objects.all().filter(owner=self.request.user).filter(
            orders__created_at__range=range_time).annotate(
            new_count=Count('orders', filter=Q(orders__status=Order.StatusType.NEW)),
            ready_count=Count('orders', filter=Q(orders__status=Order.StatusType.READY_TO_DELIVERY)),
            delivering_count=Count('orders', filter=Q(orders__status=Order.StatusType.DELIVERING)),
            delivered_count=Count('orders', filter=Q(orders__status=Order.StatusType.DELIVERED)),
            not_call_count=Count('orders', filter=Q(orders__status=Order.StatusType.NOT_CALL)),
            canceled_count=Count('orders', filter=Q(orders__status=Order.StatusType.CANCELED)),
            archived_count=Count('orders', filter=Q(orders__status=Order.StatusType.ARCHIVED)),
        ).values(
            'visit_count',
            'product__translations__name',
            'name',
            'new_count',
            'ready_count',
            'delivering_count',
            'delivered_count',
            'not_call_count',
            'canceled_count',
            'archived_count')
        return query

    def get_context_data(self, *args, **kwargs):
        tmp = self.get_queryset().aggregate(
            visit_total=Sum('visit_count'),
            new_total=Sum('new_count'),
            ready_total=Sum('ready_count'),
            delivering_total=Sum('delivering_count'),
            delivered_total=Sum('delivered_count'),
            not_call_total=Sum('not_call_count'),
            canceled_total=Sum('canceled_count'),
            archived_total=Sum('archived_count'),
        )
        data = super().get_context_data()
        data.update(tmp)
        return data


class PaymentCreateView(LoginRequiredMixin, CreateView):
    template_name = 'apps/payment/pay-form.html'
    form_class = PaymentModelForm
    success_url = reverse_lazy('pay-form')

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(**kwargs)
        data['payments'] = Payment.objects.filter(user=self.request.user)
        return data

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        user.balance -= form.instance.amount
        user.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
        return super().form_invalid(form)


class CompetitionListVew(ListView):
    queryset = User.objects.all()
    template_name = 'apps/market/competition.html'
    context_object_name = 'sellers'

    def get_queryset(self):
        query = (super().get_queryset().annotate
                 (completed_count=Count('threads__orders',
                                        filter=Q(threads__orders__status=Order.StatusType.DELIVERED))
                  ).filter(completed_count__gt=0).values('completed_count',
                                                         'first_name', 'last_name'))
        return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['site'] = SiteSettings.objects.first()
        return data


class OperatorOrderListVew(ListView):
    queryset = Order.objects.all()
    template_name = 'apps/operator/operator-page.html'
    context_object_name = 'orders'

    def get_queryset(self):
        status = self.request.GET.get('status', 'new')
        category_id = self.request.GET.get('category_id')
        district_id = self.request.GET.get('district_id')
        query = super().get_queryset()
        Order.objects.filter(operator=self.request.user).update(hold=True)
        if category_id:
            query = Order.objects.filter(product__category_id=category_id)

        if district_id:
            query = Order.objects.filter(district_id=district_id)

        if status != 'new' and self.request.user.role == User.RoleType.DELIVERER:
            query = query.filter(operator=self.request.user, status=status)
        else:
            query = query.filter(status=status)
            return query

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(*args, **kwargs)
        data['status'] = Order.StatusType.values
        data['categories'] = Category.objects.all()
        data['regions'] = Region.objects.all()
        data['deliver_status'] = [Order.StatusType.DELIVERED, Order.StatusType.READY_TO_DELIVERY,
                                  Order.StatusType.DELIVERING]
        data['operator_status'] = [Order.StatusType.NEW, Order.StatusType.CANCELED, Order.StatusType.ARCHIVED,
                                   Order.StatusType.NOT_CALL, Order.StatusType.CANCELED]
        category_id = self.request.GET.get('category_id')
        district_id = self.request.GET.get('district_id')
        if category_id:
            data['category_id'] = category_id

        if district_id:
            data['district_id'] = district_id
        return data


class OrderUpdateView(UpdateView):
    queryset = Order.objects.all()
    template_name = 'apps/operator/order-change.html'
    context_object_name = 'order'
    pk_url_kwarg = 'pk'
    form_class = OrderUpdateModelForm
    success_url = reverse_lazy('operator-orders')

    def get(self, request, *args, **kwargs):
        return_date = super().get(request, *args, **kwargs)
        self.object.hold = True
        self.object.save()
        return return_date

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['order'] = self.object
        kwargs['operator'] = self.request.user
        return kwargs

    def get_context_data(self, *args, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data

    def form_valid(self, form):
        status = form.cleaned_data.get('status')
        obj = self.object.get_object(self.queryset)
        if obj.therad and status == Order.StatusType.DELIVERED:
            seller = obj.therad.owner
            seller.balance += (obj.therad.product.seller_proce - obj.therad.discount) * obj.quantity
            seller.save()
        return super().form_valid(form)


class DiagramView(TemplateView):
    template_name = 'apps/market/diagram.html'


def region_orders_data(request):
    orders = Order.objects.values('district__region__name').annotate(count=Count('id')).order_by('-count')

    response = {
        'regions': [],
        'numbers': []
    }

    for item in orders:
        region_name = item['district__region__name'] or "Nomaʼlum"
        response['regions'].append(region_name)
        response['numbers'].append(item['count'])

    return JsonResponse(response)
