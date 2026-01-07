"""
Script de migración para poblar la base de datos PostgreSQL
con datos del microservicio de usuarios (MariaDB).

Ejecutar con: uv run python scripts/migrate_data.py
"""

import random
import secrets
import string
import sys
from datetime import date, timedelta

# Configurar stdout encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import psycopg2
import pymysql
from passlib.context import CryptContext

# Configuración de bases de datos
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "dev_user",
    "password": "dev_password",
    "dbname": "futbol_db",
}

MARIADB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "rootpass",
    "database": "sportDB",
}

# Roles y tipos
ROLES = ["ADMINISTRATOR", "COACH", "INTERN"]
# ATHLETE_TYPES se toma del campo type_stament de cada persona
RELATIONSHIP_TYPES = ["FATHER", "MOTHER", "LEGAL_GUARDIAN"]
SEXES = ["MALE", "FEMALE"]

# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def generate_random_password(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_date_adult() -> date:
    today = date.today()
    days = random.randint(18 * 365, 45 * 365)
    return today - timedelta(days=days)


def generate_date_minor() -> date:
    today = date.today()
    days = random.randint(8 * 365, 17 * 365)
    return today - timedelta(days=days)


def get_mariadb_persons():
    """Obtiene personas desde MariaDB."""
    conn = pymysql.connect(
        host=MARIADB_CONFIG["host"],
        port=MARIADB_CONFIG["port"],
        user=MARIADB_CONFIG["user"],
        password=MARIADB_CONFIG["password"],
        database=MARIADB_CONFIG["database"],
        charset="latin1",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, external_id, identification, name, last_name,
                       direction, phono, type_stament
                FROM persons
            """)
            rows = cur.fetchall()
            # Convertir strings a UTF-8
            result = []
            for row in rows:
                clean = {}
                for k, v in row.items():
                    if isinstance(v, bytes):
                        clean[k] = v.decode("latin1", errors="replace")
                    elif isinstance(v, str):
                        clean[k] = v
                    else:
                        clean[k] = v
                result.append(clean)
            return result
    finally:
        conn.close()


def clean_database(pg_conn):
    """Limpia la base de datos PostgreSQL."""
    tables = [
        "attendances",
        "technical_assessments",
        "yoyo_tests",
        "sprint_tests",
        "endurance_tests",
        "tests",
        "evaluations",
        "statistics",
        "athletes",
        "representatives",
        "accounts",
        "users",
    ]
    with pg_conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"  [OK] {table}")
            except Exception as e:
                print(f"  [!] {table}: {e}")
    pg_conn.commit()


def main():
    print("=" * 50)
    print("MIGRACION: MariaDB -> PostgreSQL")
    print("=" * 50)

    # Conectar PostgreSQL
    print("\n[1] Conectando a PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        pg_conn.set_client_encoding("UTF8")
        print("  [OK] Conectado")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    # Limpiar DB
    print("\n[2] Limpiando base de datos...")
    clean_database(pg_conn)

    # Obtener personas de MariaDB
    print("\n[3] Obteniendo personas de MariaDB...")
    try:
        persons = get_mariadb_persons()
        print(f"  [OK] {len(persons)} personas")
    except Exception as e:
        print(f"  [ERROR] {e}")
        pg_conn.close()
        return

    # Separar por tipo
    externos = [p for p in persons if p.get("type_stament") == "EXTERNOS"]
    otros = [p for p in persons if p.get("type_stament") != "EXTERNOS"]
    print(f"  - EXTERNOS: {len(externos)}")
    print(f"  - Otros: {len(otros)}")

    # ============ CREAR USUARIOS (Solo 3) ============
    print("\n[4] Creando usuarios...")

    # Seleccionar 3 personas para ser usuarios
    user_pool = otros[:3] if len(otros) >= 3 else otros

    # Roles y contraseñas fijas para cada usuario
    fixed_users = [
        {"role": "ADMINISTRATOR", "pwd": "admin123", "email_prefix": "admin"},
        {"role": "COACH", "pwd": "coach123", "email_prefix": "coach"},
        {"role": "INTERN", "pwd": "intern123", "email_prefix": "intern"},
    ]

    user_creds = {}
    with pg_conn.cursor() as cur:
        for i, p in enumerate(user_pool):
            if i >= len(fixed_users):
                break

            name = f"{p.get('name', '')} {p.get('last_name', '')}".strip()
            dni = p.get("identification", "")
            ext = p.get("external_id", "")

            role = fixed_users[i]["role"]
            pwd = fixed_users[i]["pwd"]
            email = f"{fixed_users[i]['email_prefix']}@unl.edu.ec"

            hashed = hash_password(pwd)
            user_creds[dni] = {"name": name, "role": role, "pwd": pwd, "email": email}

            # Insertar user
            cur.execute(
                """
                INSERT INTO users (
                external, full_name, dni, is_active, created_at, updated_at
                )
                VALUES (%s, %s, %s, true, NOW(), NOW()) RETURNING id
            """,
                (ext, name, dni),
            )
            user_id = cur.fetchone()[0]

            # Insertar account
            cur.execute(
                """
                INSERT INTO accounts (
                    user_id, email, password_hash, role, is_active, 
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, true, NOW(), NOW())
            """,
                (user_id, email, hashed, role),
            )

            print(f"  [+] {name[:30]} ({role}) - {pwd}")
    pg_conn.commit()

    # ============ CREAR REPRESENTANTES Y MENORES (EN PARES) ============
    print("\n[5] Creando representantes con sus atletas menores...")

    # Dividir externos: mitad representantes, mitad menores
    half = len(externos) // 2
    rep_candidates = externos[:half]
    minor_candidates = externos[half:]

    # Asegurar que hay igual cantidad de representantes y menores
    pairs_count = min(len(rep_candidates), len(minor_candidates), 10)

    rep_ids = {}
    minors_created = []

    with pg_conn.cursor() as cur:
        for i in range(pairs_count):
            rep_person = rep_candidates[i]
            minor_person = minor_candidates[i]

            # Crear representante
            rep_name = (
                f"{rep_person.get('name', '')} {rep_person.get('last_name', '')}"
            ).strip()
            rep_dni = rep_person.get("identification", "")
            rep_ext = rep_person.get("external_id", "")
            phone = (
                rep_person.get("phono") if rep_person.get("phono") != "S/N" else None
            )
            rel = random.choice(RELATIONSHIP_TYPES)

            cur.execute(
                """
                INSERT INTO representatives 
                (external_person_id, full_name, dni, phone, relationship_type, 
                 is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW()) RETURNING id
            """,
                (rep_ext, rep_name, rep_dni, phone, rel),
            )
            rep_id = cur.fetchone()[0]
            rep_ids[rep_ext] = rep_id

            # Crear atleta menor con este representante
            minor_name = (
                f"{minor_person.get('name', '')} {minor_person.get('last_name', '')}"
            ).strip()
            minor_dni = minor_person.get("identification", "")
            minor_ext = minor_person.get("external_id", "")
            dob = generate_date_minor()
            sex = random.choice(SEXES)
            h = round(random.uniform(1.40, 1.75), 2)
            w = round(random.uniform(35, 65), 1)
            atype = minor_person.get("type_stament", "EXTERNOS")

            cur.execute(
                """
                INSERT INTO athletes 
                (external_person_id, full_name, dni, type_athlete, 
                date_of_birth, height, weight, sex, representative_id, 
                is_active, created_at, updated_at)
                VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW()
                ) RETURNING id
            """,
                (minor_ext, minor_name, minor_dni, atype, dob, h, w, sex, rep_id),
            )
            ath_id = cur.fetchone()[0]

            # Estadisticas
            cur.execute(
                """
                INSERT INTO statistics 
                (athlete_id, speed, stamina, strength, agility, matches_played,
                 goals, assists, yellow_cards, red_cards, is_active, created_at, 
                 updated_at)
                VALUES (%s, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 0, true, NOW(), NOW())
            """,
                (ath_id,),
            )

            minors_created.append(minor_person)
            print(f"  [+] Rep: {rep_name[:20]} -> Atleta: {minor_name[:20]}")

    pg_conn.commit()
    print(f"  Total: {pairs_count} pares (representante + atleta menor)")

    # ============ CREAR ATLETAS ADULTOS ============
    print("\n[6] Creando atletas adultos...")

    # Adultos de otros (excluyendo los 3 usuarios)
    adults = [p for p in otros if p not in user_pool][:20]
    count = 0

    with pg_conn.cursor() as cur:
        # Adultos
        for p in adults:
            name = f"{p.get('name', '')} {p.get('last_name', '')}".strip()
            dni = p.get("identification", "")
            ext = p.get("external_id", "")
            dob = generate_date_adult()
            sex = random.choice(SEXES)
            h = round(random.uniform(1.60, 1.90), 2)
            w = round(random.uniform(55, 85), 1)
            atype = p.get("type_stament", "EXTERNOS")  # Usar el tipo real de la persona

            cur.execute(
                """
                INSERT INTO athletes 
                (external_person_id, full_name, dni, type_athlete, date_of_birth, 
                 height, weight, sex, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true, NOW(), NOW()) RETURNING id
            """,
                (ext, name, dni, atype, dob, h, w, sex),
            )
            ath_id = cur.fetchone()[0]

            # Estadisticas
            cur.execute(
                """
                INSERT INTO statistics 
                (athlete_id, speed, stamina, strength, agility, matches_played, 
                goals, assists, yellow_cards, red_cards, is_active, created_at,
                updated_at)
                VALUES (%s, NULL, NULL, NULL, NULL, 0, 0, 0, 0, 0, true, NOW(), NOW())
            """,
                (ath_id,),
            )
            count += 1
            print(f"  [+] {name[:30]} (Adulto)")

    pg_conn.commit()
    pg_conn.close()

    # ============ RESUMEN ============
    total_athletes = count + pairs_count  # Adultos + Menores
    print("\n" + "=" * 50)
    print("COMPLETADO")
    print("=" * 50)
    print(f"Usuarios: {len(user_creds)}")
    print(f"Representantes: {len(rep_ids)}")
    print(f"Atletas: {total_athletes} ({count} adultos + {pairs_count} menores)")

    print("\n--- CREDENCIALES ---")
    print(f"{'DNI':<12} {'Rol':<8} {'Password':<12}")
    print("-" * 35)
    for dni, info in user_creds.items():
        print(f"{dni:<12} {info['role']:<8} {info['pwd']:<12}")


if __name__ == "__main__":
    main()
