from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import Profile, User


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['nickname', 'avatar_key']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']
        read_only_fields = ['id', 'username', 'email', 'profile']


class RegisterSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'nickname', 'password', 'password_confirm']

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError({'password_confirm': ['Passwords do not match.']})

        validate_password(password)

        if User.objects.filter(username__iexact=attrs.get('username')).exists():
            raise serializers.ValidationError({'username': ['A user with that username already exists.']})

        if User.objects.filter(email__iexact=attrs.get('email')).exists():
            raise serializers.ValidationError({'email': ['User with this email already exists.']})

        if Profile.objects.filter(nickname__iexact=attrs.get('nickname')).exists():
            raise serializers.ValidationError({'nickname': ['User with this nickname already exists.']})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password_confirm')
        nickname = validated_data.pop('nickname')

        with transaction.atomic():
            user = User.objects.create_user(password=password, **validated_data)
            profile = user.profile
            profile.nickname = nickname
            profile.avatar_key = 'knight-1'
            profile.save(update_fields=['nickname', 'avatar_key'])
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['nickname', 'avatar_key']

    def validate_nickname(self, value):
        if Profile.objects.filter(nickname__iexact=value).exclude(user=self.context['request'].user).exists():
            raise serializers.ValidationError('User with this nickname already exists.')
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), username=username, password=password)
        if user is None:
            raise serializers.ValidationError({'non_field_errors': ['Invalid credentials.']})

        attrs['user'] = user
        return attrs
