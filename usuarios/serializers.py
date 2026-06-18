from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from .models import Usuario

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename']

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), source='permissions', write_only=True, required=False
    )

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permission_ids']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Primary group (role)
        groups = self.user.groups.all()
        data['role'] = groups[0].name if groups.exists() else None
        
        # Array of group names
        data['groups'] = [g.name for g in groups]
        
        # Array of permission codenames (e.g. 'pagos.add_pago', we split by '.' to return just codename if desired, but user.get_all_permissions() returns 'app_label.codename')
        # We will return just the codename to match frontend expectations: 'add_pago'
        perms = self.user.get_all_permissions()
        data['permissions'] = [p.split('.')[1] for p in perms]
        
        data['apoderado_id'] = self.user.apoderado_rel.id if self.user.apoderado_rel else None
        
        return data

class UsuarioSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), source='groups', write_only=True, required=False
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'is_parent', 'first_login', 'groups', 'group_ids', 'apoderado_rel']

    def update(self, instance, validated_data):
        groups = validated_data.pop('groups', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        
        if groups is not None:
            instance.groups.set(groups)
            
        return instance
        
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), source='groups', write_only=True, required=False
    )

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'group_ids']

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        password = validated_data.pop('password')
        username = validated_data.pop('username')
        user = Usuario.objects.create_user(
            username=username,
            password=password,
            **validated_data
        )
        if groups:
            user.groups.set(groups)
        return user