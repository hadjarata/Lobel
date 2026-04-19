from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]  # inscription publique
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        user = request.user

        if not user or not user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        customer = Customer.objects.filter(user=user).first()

        if not customer:
            return Response(
                {"detail": "Customer profile not found for this user."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(customer)
        return Response(serializer.data)