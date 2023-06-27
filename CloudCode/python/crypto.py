from cryptography.fernet import Fernet
import json, const

def read_write_json(data: dict = None, filename="credentials.json") -> dict:
    if data is None:
        with open(filename, 'r') as f:
            data = json.load(f)
    else:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    return data


def create_or_login(login, password):
  data = read_write_json()
  if login in data:
    return user_login(login, password)
  else:
    data[login] = password
    read_write_json(data)
  return "User created successfully."

def user_login(login, password):
  data = read_write_json()
  if not login in data:
    return "User does not exists."
  if data[login] != password:
    return "Wrong password."
  return True

# --

def generate_key():
  return Fernet.generate_key()

def encrypt(message: str, key: bytes = const.FERNET_KEY) -> str:
    return Fernet(key).encrypt(message.encode()).decode()

def decrypt(token: str, key: bytes = const.FERNET_KEY) -> str:
    return Fernet(key).decrypt(token.encode()).decode()

