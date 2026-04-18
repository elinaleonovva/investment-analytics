from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'access', 'refresh')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value).lower()
        if User.objects.filter(email=normalized_email).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return normalized_email

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        refresh = RefreshToken.for_user(user)
        user.access = str(refresh.access_token)
        user.refresh = str(refresh)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].lower()
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token
