import requests
from wdltest.config import Config

class EwesClient(object):

    def __init__(self, ewes_auth):
        self.ewes_auth = ewes_auth
    
    def register_engine(self):
        pass

    def deregister_engine(self):
        pass
    
    def __get_url(self):
        return Config.instance().workbench_ewes_url