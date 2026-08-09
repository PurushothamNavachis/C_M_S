import urllib.request
import urllib.error
import json
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1/users"

roles_to_test = [
    {
        "role_name": "SUPER_ADMIN",
        "username": f"test_superadmin_{str(uuid.uuid4())[:4]}",
        "email": f"superadmin_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527001"
    },
    {
        "role_name": "ADMIN",
        "username": f"test_admin_{str(uuid.uuid4())[:4]}",
        "email": f"admin_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527002"
    },
    {
        "role_name": "RECEPTIONIST",
        "username": f"test_receptionist_{str(uuid.uuid4())[:4]}",
        "email": f"rec_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527003"
    },
    {
        "role_name": "DOCTOR",
        "username": f"test_doctor_{str(uuid.uuid4())[:4]}",
        "email": f"doc_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527004",
        "specialization": "Neurologist (Neurology)",
        "license_number": f"LIC-NEURO-{str(uuid.uuid4())[:4]}",
        "consultation_fee": 150,
        "experience_years": 10
    },
    {
        "role_name": "LAB_AC",
        "username": f"test_labac_{str(uuid.uuid4())[:4]}",
        "email": f"labac_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527005",
        "qualification": "M.Sc Pathology",
        "license_number": f"LAB-PATH-{str(uuid.uuid4())[:4]}",
        "experience_years": 6
    },
    {
        "role_name": "SURGEON",
        "username": f"test_surgeon_{str(uuid.uuid4())[:4]}",
        "email": f"surgeon_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527006"
    },
    {
        "role_name": "PHARMACIST",
        "username": f"test_pharmacist_{str(uuid.uuid4())[:4]}",
        "email": f"pharma_{str(uuid.uuid4())[:4]}@cms.com",
        "password": "password123",
        "mobile_number": "8919527007"
    }
]

print("============================================================")
print("STARTING FULL SELF-REVIEW VALIDATION OF ALL SYSTEM ROLES")
print("============================================================")

passed = 0
failed = 0

for test_case in roles_to_test:
    role = test_case["role_name"]
    req = urllib.request.Request(
        BASE_URL,
        data=json.dumps(test_case).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        res = urllib.request.urlopen(req)
        body = json.loads(res.read().decode('utf-8'))
        print(f"[PASS] Role: {role:<15} | User ID: {body['id'][:8]} | Username: {body['username']} | Role assigned: {body['role']['name']}")
        passed += 1
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"[FAIL] Role: {role:<15} | HTTP {e.code} | Response: {err_msg}")
        failed += 1
    except Exception as e:
        print(f"[FAIL] Role: {role:<15} | Exception: {e}")
        failed += 1

print("============================================================")
if failed == 0:
    print(f"ALL {passed} ROLES CREATED SUCCESSFULLY WITH 0 ERRORS!")
else:
    print(f"RESULT: {passed} Passed, {failed} Failed")
print("============================================================")
