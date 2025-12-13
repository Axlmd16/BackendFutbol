

from app.client.person_client import PersonClient


person_client = PersonClient()


async def main():
    
    data = {
    "first_name": "Jostin",
    "last_name": "Jimenez",
    "identification": "115696977",
    "type_identification": "CEDULA",
    "type_stament": "ESTUDIANTES",
    "direction": "house",
    "phono": "0985001169",
    "email": "jostin.jimenez@unl.edu.ec",
    "password": "dwgkoro16"
    }
    
    person_resp = await person_client.create_person_with_account(data)

    print(person_resp)
        
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())