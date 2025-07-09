from django.urls import path

from apps.views import HomeListView, AuthFormView, LogoutView, ProductListView, ProfileUpdateView, district_view, \
    UserChangePassword, SearchProductListView, OrderFormView, OrderListView, wishlist_view, WishListView, \
    ThreadCreateView, ThreadListView, ThreadDetailView, MarketListView, StatisticListView, PaymentCreateView, \
    OperatorOrderListVew, CompetitionListVew, DiagramView, region_orders_data , OrderUpdateView

urlpatterns = [
    path('', HomeListView.as_view(), name='home'),
    path('product-list', ProductListView.as_view(), name='product-list'),
    path('search', SearchProductListView.as_view(), name='search'),
]



#------order-------
urlpatterns += [
    path('order-form/<str:slug>', OrderFormView.as_view(), name='order-form'),
    path('order-list', OrderListView.as_view(), name='order-list'),

]

#-----------user----------
urlpatterns += [
    path('auth', AuthFormView.as_view(), name='auth'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('user/profile', ProfileUpdateView.as_view(), name='profile'),
    path('user/profile/change-password', UserChangePassword.as_view(), name='change-password'),
    path('district-list', district_view, name='district_list'),
    path('wishlist/<int:pk>', wishlist_view, name='wish'),
    path('wish/list', WishListView.as_view(), name='wishlist'),

    path('diagram', DiagramView.as_view(), name='diagram'),
    path('api/region-orders/', region_orders_data, name='region-orders-data'),
]


#--------------------- market|Thread --------------------------

urlpatterns += [
    path('market-list', MarketListView.as_view(), name='market-list'),
    path('thread-form', ThreadCreateView.as_view(), name='thread-form'),
    path('thread-list', ThreadListView.as_view(), name='thread-list'),
    path('thread/<int:pk>', ThreadDetailView.as_view(), name='thread'),
    path('thread/statistic', StatisticListView.as_view(), name='thread-statistic'),
    path('thread/competition', CompetitionListVew.as_view(), name='thread-competition'),
]

#-------------- Pay -------------------------------

urlpatterns += [
    path('pay-form' , PaymentCreateView.as_view(), name='pay-form')]


# ------------ Operator ---------
urlpatterns += [
    path('operator/order/list' , OperatorOrderListVew.as_view(), name='operator-orders'),
    path('operator/order/update/<int:pk>' , OrderUpdateView.as_view(), name='operator-update')]
