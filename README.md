# Locust Load Test
This is a simple load testing tool which will do a sample signin,  signup, vacancy related actions and generate reports.


### Dependencies
```bash
pip install -r requirements.txt
```

### Generate proto 
This will use the current proto files and generate its stub files using `grpc_tools` 

Run this command from the project directory
```bash
./generate_rpc.sh 
```

### Run
Make sure you have correct gRPC hostname with its port in this format `<domain>:<port>`

Run this command from the project directory
```bash
./test.sh "abc.com:8234"
```

Once it is completed it will generate the report in `report.html`