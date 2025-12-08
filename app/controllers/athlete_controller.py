from app.dao.athlete_dao import AthleteDAO


class AthleteController:
    """
    Controlador de deportistas
    """
    
    def __init__(self):
        self.athlete_dao = AthleteDAO()