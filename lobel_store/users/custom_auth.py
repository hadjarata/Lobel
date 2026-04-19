from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(BaseBackend):
    """
    Custom authentication backend that allows users to login with email instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user using email or username.
        """
        if username is None or password is None:
            return None
            
        # Try to find user by email first, then by username as fallback
        try:
            # Check if username looks like an email
            if '@' in username:
                user = User.objects.get(Q(email=username) | Q(username=username))
            else:
                user = User.objects.get(Q(username=username) | Q(email=username))
                
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
            
    def get_user(self, user_id):
        """
        Retrieve user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
