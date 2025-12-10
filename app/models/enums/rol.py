import enum

class Role(enum.Enum):
    """Rol cualitativo para categorizar usuarios."""
    ADMINISTRATOR = "Administrator"
    COACH = "Coach"
    INTERN = "Intern"