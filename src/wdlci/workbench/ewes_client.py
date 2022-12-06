import requests
from wdlci.config import Config

class EwesClient(object):

    def __init__(self, ewes_auth):
        self.ewes_auth = ewes_auth
    
    def __get_url(self):
        return Config.instance().workbench_ewes_url