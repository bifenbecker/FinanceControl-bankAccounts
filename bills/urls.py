from django.urls import path
from .views import BillViewSet

urlpatterns = [
    path('bill', BillViewSet.as_view({
        'post': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),
    path('create-bill', BillViewSet.as_view({
        'post': 'create'
    })),
    path('list', BillViewSet.as_view({
        'get': 'list'
    }))
]
