import grpc
import random
import string
from locust import HttpUser, task, between
from tinydb import TinyDB

# For the auto resolve package within the generated proto files
import sys
sys.path.append('src/proto')


from src.proto.auth_service_pb2_grpc import AuthServiceStub
from src.proto.rpc_signup_user_pb2 import SignUpUserInput
from src.proto.auth_service_pb2 import VerifyEmailRequest

class SeedUser(HttpUser):
    wait_time = between(1, 5)  
    db:TinyDB

    def on_start(self):
        self.db= TinyDB("db.json")
        self.channel = grpc.insecure_channel(self.environment.host)
        self.stub = AuthServiceStub(self.channel)
    
    def generate_random_credentials(self):
        
        """Generates random credentials for user signup."""
        username = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        email = f"{username}@mailinator.com"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        print("user: ", username, email, password)
        self.db.insert({"username":username, "email":email, "password":password})
        return username, email, password


    @task 
    def verify_user(self):
        data = self.db.all()
        for d in data:
            print(d)
            req = VerifyEmailRequest(verificationCode=d["code"])
            response = self.stub.VerifyEmail(req)
            print(response)

    # @task
    def signup_user(self):
        """Task to sign up a new user."""
        username, email, password = self.generate_random_credentials()
        request = SignUpUserInput(name=username, email=email, password=password, passwordConfirm=password)
        
        try:
            response = self.stub.SignUpUser(request)
            print(f"User signed up: {response}")
        except grpc.RpcError as e:
            print(f"Failed to sign up user: {e}")
