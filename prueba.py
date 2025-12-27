from app.client.person_client import PersonClient
from app.controllers.user_controller import UserController
from app.core.database import SessionLocal

person_client = PersonClient()
uc = UserController()

db = SessionLocal()


async def main():
    # data = {
    #     "first_name": "Jostin",
    #     "last_name": "Jimenez",
    #     "identification": "115696977",
    #     "type_identification": "CEDULA",
    #     "type_stament": "ESTUDIANTES",
    #     "direction": "house",
    #     "phono": "0985001169",
    #     "email": "jostin.jimenez@unl.edu.ec",
    #     "password": "dwgkoro16",
    # }

    # person_resp = await person_client.create_person_with_account(data)

    # users = await person_client.get_all_filter()
    # print(users)

    users = uc.get_all_users(db)
    print(users)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
