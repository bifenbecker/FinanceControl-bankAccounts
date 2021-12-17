from django.urls import path

from .views import OperationViewSet, CategoryView, CategoryListView, ListOperationsOfBill


urlpatterns = [
    path('operation', OperationViewSet.as_view({
        'post': 'create',
        'delete': 'destroy',
        'put': 'update',
        'get': 'retrieve'
    })),
    path('operations', OperationViewSet.as_view({
        'get': 'list'
    })),
    path('operations-of-bill', ListOperationsOfBill.as_view()),
    path('categories', CategoryListView.as_view({
        'get': 'list'
    })),
    path('category', CategoryView.as_view({
        'post': 'create'
    }))
]