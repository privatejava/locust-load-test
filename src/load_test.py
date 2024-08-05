import grpc
import time
import logging
from faker import Faker
from locust import task, between
from locust import events, User, SequentialTaskSet
from tinydb import TinyDB

# For the auto resolve package within the generated proto files
import sys
sys.path.append('src/proto')

# gRPC related imports
from src.proto.auth_service_pb2_grpc import AuthServiceStub
from src.proto.user_service_pb2_grpc import UserServiceStub
from src.proto.vacancy_service_pb2_grpc import VacancyServiceStub
from src.proto.rpc_create_vacancy_pb2 import CreateVacancyRequest
from src.proto.rpc_update_vacancy_pb2 import UpdateVacancyRequest
from src.proto.vacancy_service_pb2 import VacancyRequest,  GetVacanciesRequest
from src.proto.rpc_signin_user_pb2 import SignInUserInput



# The `LoadTest` class in Python defines tasks for load testing a gRPC-based application, including
# signing in users, managing vacancies, and tracking gRPC calls.

class LoadTest(User):
    
    wait_time = between(1, 5)  # Time between requests
    db:TinyDB

    def on_start(self):
        """
        The `on_start` function initializes various components such as Faker, TinyDB, gRPC channel, and
        service stubs for authentication, user, and vacancy services.
        """
        self.fake = Faker()
        self.db= TinyDB("db.json")
        self.channel = grpc.insecure_channel(self.environment.host)
        
        self.auth_service = AuthServiceStub(self.channel)
        self.user_service = UserServiceStub(self.channel)
        self.vacancy_service= VacancyServiceStub(self.channel)


    def _track_grpc_call(self, func, request, grpc_name, timeout=5):
        """Helper function to track gRPC call with Locust."""
        start_time = time.time()
        request_meta = {
            "request_type": "gRPC",
            "name": grpc_name,
            "response_length": 0,
            "exception": None,
            "context": None,
            "response": None,
        }
        try:
            request_meta["response"] = func(request, timeout=timeout)
            request_meta["response_length"] = sys.getsizeof(request_meta["response"])
            response_time = int((time.time() - start_time) * 1000)  # in milliseconds
            request_meta["response_time"] =  response_time
            events.request.fire(**request_meta)
            return request_meta["response"]
        except grpc.RpcError as e:
            response_time = int((time.time() - start_time) * 1000)
            request_meta["response_time"] =  response_time            
            events.request.fire(**request_meta)            
            raise

    
    def signin(self, user):
        logging.info("[Signin] Start")
        req = SignInUserInput(email=user["email"], password=user["password"])        
        response = self._track_grpc_call(self.auth_service.SignInUser, req, "SignInUser")
        logging.info(response)
        assert response.status == "success"

    @task
    def vacancy_list(self):
        data = self.db.all()
        for _ in data:
            self.get_vacancies()
        time.sleep(45)    
            

    @task(10)
    def vacancy_test(self):
        """
        The function `vacancy_test` iterates through data, signs in, creates, updates, and deletes
        vacancies, and retrieves vacancies.
        """
        data = self.db.all()
        for d in data:
            self.signin(d)
            vacancy = self.create_vacancy()
            self.update_vacancy(vacancy)
            self.delete_vacancy(vacancy)
            self.get_vacancies()

    
    def create_vacancy(self):
        """
        This Python function creates a vacancy with a title, description, division, and country, and
        returns the created vacancy.
        :return: The `create_vacancy` function is returning the created `vacancy` object after making a
        gRPC call to create a new vacancy.
        """
        logging.info("[CreateVacancy] Start")
        req = CreateVacancyRequest(Title=f"{self.fake.job()} needed [{self.fake.uuid4()}]", Description=self.fake.text(), Division= "SALES", Country="Nepal" )
        res = self._track_grpc_call(self.vacancy_service.CreateVacancy, req, "CreateVacancy")
        assert res != None
        vacancy = res.vacancy
        assert vacancy and len(vacancy.Id), f"[CreateVacancy] \t:: Invalid Response: {res}"
        return vacancy
    

    def update_vacancy(self, vacancy):
        """
        This Python function updates a vacancy by sending a gRPC request with the updated title and
        description.
        
        :param vacancy: It looks like the code snippet you provided is a method for updating a vacancy.
        The method takes a `vacancy` object as a parameter and updates its title and description by
        appending "[Updated]" to them
        """
        logging.info("[UpdateVacancy] Start")
        req = UpdateVacancyRequest(Id= vacancy.Id, Title = vacancy.Title +" [Updated]", Description = vacancy.Description +" [Updated]")
        res = self._track_grpc_call(self.vacancy_service.UpdateVacancy, req, "UpdateVacancy")
        assert res and res.vacancy, f"[UpdateVacancy] \t:: Invalid Response: {res}"
        logging.info(res)
        assert res.vacancy.Title ==  vacancy.Title +" [Updated]" , "Vacancy title not updated"
        assert res.vacancy.Description ==  vacancy.Description +" [Updated]" , "Vacancy description not updated"


    def delete_vacancy(self, vacancy):
        """
        This Python function deletes a vacancy using gRPC communication and logs the process.
        
        :param vacancy: The `delete_vacancy` function takes a `vacancy` object as a parameter. This
        object likely represents a job vacancy or position that needs to be deleted from a system or
        database. The function then uses the `vacancy.Id` attribute to create a `VacancyRequest` object
        for
        """
        logging.info("[DeleteVacancy] Start")
        req = VacancyRequest(Id= vacancy.Id)
        res = self._track_grpc_call(self.vacancy_service.DeleteVacancy, req, "DeleteVacancy")
        logging.info(res)
        assert res and res.success , f"[DeleteVacancy] \t:: Invalid Response : {res}"
    
    
    def get_vacancies(self):
        """
        This Python function logs a message, sends a request to get vacancies using gRPC, and logs the
        response.
        """
        logging.info("[GetVacancies] Start")
        req = GetVacanciesRequest()
        res_stream = self._track_grpc_call(self.vacancy_service.GetVacancies, req, "GetVacancies", 5)
        for r in res_stream:
            logging.info(r)
        
