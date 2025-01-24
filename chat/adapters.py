from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        Hook that can be used to further populate the user instance.
        """
        user = super().populate_user(request, sociallogin, data)
        
        if sociallogin.account.provider == 'google':
            # Get name from Google data
            name = data.get('name', '')
            first_name = data.get('given_name', '')
            last_name = data.get('family_name', '')
            
            # Set name fields
            if first_name:
                user_field(user, 'first_name', first_name)
            if last_name:
                user_field(user, 'last_name', last_name)
            
            # Set email as username if no username is provided
            if not user_username(user):
                email = user_email(user)
                username = email.split('@')[0]
                user_field(user, 'username', self.generate_unique_username([username, email]))
        
        return user
    
    def generate_unique_username(self, txts):
        """
        Generate a unique username from the given texts.
        """
        username = None
        User = get_user_model()
        
        for txt in txts:
            if not username:
                username = txt
                while User.objects.filter(username=username).exists():
                    username = f"{txt}_{User.objects.filter(username__startswith=txt).count() + 1}"
        
        return username
