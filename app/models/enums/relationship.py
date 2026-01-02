import enum


class Relationship(enum.Enum):
    """Tipo de relacion entre un atleta menor de edad y su representante."""

    FATHER = "Father"
    MOTHER = "Mother"
    LEGAL_GUARDIAN = "Legal Guardian"
