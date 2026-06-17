import pytest
from usuarios.models import Usuario

@pytest.mark.django_db
def test_create_user():
    user = Usuario.objects.create_user(username="testuser", password="password123")
    assert user.username == "testuser"
    assert Usuario.objects.count() == 1
