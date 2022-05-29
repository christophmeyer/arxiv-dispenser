import hashlib
import uuid

from database import User


def hash_password(salt, password):
    return hashlib.sha512((salt + password).encode('utf-8')).hexdigest(),


def create_user(name, password):
    salt = uuid.uuid4().hex
    user = User(idx=uuid.uuid4().hex,
                name=name,
                pw_hash=hash_password(salt, password),
                salt=salt)
    return user
