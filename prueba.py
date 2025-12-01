from app.core.database import SessionLocal, get_db
from app.controllers.user_controller import UserController
from app.schemas.user_schema import UserCreate

# Crear Session manual (igual que hace FastAPI)
db = SessionLocal()
try:
    user_controller = UserController()
    user_data = UserCreate(
        email="test@tes2t.com",
        username="testuser2",
        password="pass12345678"
    )
    
    # print(f"user_data.password: {user_data.password}")
    # user = user_controller.create_user(db, user_data)
    # print("✅ Usuario creado:", user.username)
    
    
    # user_update = user_controller.update_user(
    #     db,
    #     user_id=1,
    #     user_data=UserCreate(
    #         email="updated@test.com",
    #         username="updateduser",
    #         password="newpass1234"
    #     )
    # )
    
    # print("✅ Usuario actualizado:", user_update.username)
    
    users = user_controller.get_all_users(db, skip=0, limit=10)
    print(f"✅ Usuarios encontrados: {len(users)}")
    for u in users:
        print(f"- {u.id}: {u.username} ({u.email})")
        
    user_controller.authenticate_user(
        db,
        email="test@tes2t.com",
        password="pass12345678"
    )
    print("✅ Autenticación exitosa")
    
    
    db.commit()  # ← Commit manual en pruebas
    
finally:
    db.close()  # ← Siempre cerrar
