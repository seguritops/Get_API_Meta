from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User
from facebook_business.adobjects.adaccount import AdAccount
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

class APIError(Exception):
    """Clase base para errores personalizados."""

    def __init__(self, message: str, tipo: str):
        self.message = message
        # self.code = code  # Código de error opcional
        super().__init__(f"[{tipo}] {message}")

# Crear errores personalizados
Error_dict_format = APIError('Debes ingresar un diccionario con las llaves "ruta" y "nombre_token" en formato texto no nulo','Error Formato')
Error_get_token = APIError('Error al obtener el token. Por favor revisa la configuración de la variable de entorno o diccionario de acceso a ella','Error')
Error_ini_API = APIError('Error al inicializar la API de Facebook. Por favor revisa que el token sea válido para comenzar','Error')
Error_get_accounts = APIError('Error al obtener las cuentas de publicidad. Por favor revisa que el token sea válido para consultar los datos','Error')
Error_get_id_account = APIError('Error al obtener el ID de la cuenta de publicidad. Por favor revisa que el índice ingresado sea válido','Error Index')

class API_meta:
    def __init__(self,dict_env):
        self.dict_env = dict_env
        self.iniFbAPI()

    # geters  
    def getIdAccount(self,indice:int) -> str:
        """
        Esta función obtiene el ID de una cuenta de publicidad
        """
        try:
            # Validar que el índice sea válido
            if indice < 0 or indice >= len(self.adAccounts):
                raise Error_get_id_account
            return self.adAccounts[indice]['account_id']
        except Exception as e:
            print(e)

    def getNombreCuenta(self,account_id:str) -> str:
        """
        Esta función obtiene el nombre de una cuenta de publicidad
        """
        try:
            # Obtener nombre de la cuenta de publicidad
            for account in self.adAccounts:
                if account['account_id'] == account_id:
                    return account['name']
        except Exception as e:
            print(e)

    # seters

    # metodos
    def getToken(self) -> str:
        """
        Esta función obtiene el token de Meta desde la variable de entorno
        """
        try:
            # Validar formato del diccionario de acceso a la variable de entorno
            if type(self.dict_env['ruta']) != str or type(self.dict_env['nombre_token']) != str:
                raise Error_dict_format
            if len(self.dict_env['ruta']) == 0 or len(self.dict_env['nombre_token']) == 0:
                raise Error_dict_format
            # Cargar variable de entorno
            load_dotenv(dotenv_path=self.dict_env['ruta'])
            # Obtener el token
            self.token = os.getenv(self.dict_env['nombre_token'])
            # Validar que el token no sea nulo
            if self.token is None:
                raise Error_get_token
            print('@ Token cargado con éxito')
            return self.token
        except Exception as e:
            print(e)
            
    def iniFbAPI(self) -> None:
        """
        Esta función inicializa la API de Facebook con el token de acceso
        """
        try:
            # Inicializar la API de Facebook
            FacebookAdsApi.init(access_token=self.getToken())
            print('@ API de Facebook inicializada con éxito')
            print("-" * 40)
        except Exception as Error_ini_API:
            print(Error_ini_API)

    def getAdAccounts(self,mostrar_cuentas:bool=False) -> list:
        """
        Esta función obtiene las cuentas de publicidad de Meta
        """
        try:
            # Obtener cuentas de publicidad
            me = User(fbid="me")
            self.adAccounts = list(me.get_ad_accounts(
                fields=["account_id", "id", "name"])
            )
            print('@ Cuentas de publicidad obtenidas con éxito')
            print('\n')
            if mostrar_cuentas: self.printAccounts()
            return self.adAccounts
        except Exception as Error_get_accounts:
            print(Error_get_accounts)

    def getAdCampaigns(self,account_id:str,mostrar_campaigns:bool=False) -> list:
        """
        Esta función obtiene las campañas de una cuenta de publicidad
        """
        try:
            # Obtener campañas de una cuenta de publicidad
            ad_account = AdAccount(f"act_{account_id}")
            self.campaigns = list(ad_account.get_campaigns(
                fields=["id", "name", "status", "effective_status", "objective"])
            )
            print('@ Campañas obtenidas con éxito')
            print('\n')
            if mostrar_campaigns: self.printCampaigns(account_id)
            return self.campaigns
        except Exception as e:
            print(e)

    # metodos auxiliares
    def printAccounts(self) -> None:
        """
        Esta función imprime las cuentas de publicidad
        """
        print('# Cuentas obtenidas desde Meta')
        contador = 0
        for account in self.adAccounts:
            print(f"> [{contador}] Account ID: {account['account_id']}, Name: {account['name']}")
            contador += 1
        print('\n')
        print("@ Utiliza el [id] de una de las cuentas de arriba dentro de la función getIdAccount() para obtener el ID de la cuenta de publicidad")
        print("-" * 40)

    def printCampaigns(self,account_id:str) -> None:
        """
        Esta función imprime las campañas de una cuenta de publicidad
        """
        print(f'# Campañas obtenidas desde Meta para la cuenta: {self.getNombreCuenta(account_id)}')
        contador = 0
        for campaign in self.campaigns:
            print(f"> [{contador}] Campaign ID: {campaign['id']}, Name: {campaign['name']}, Status: {campaign['status']}, Effective Status: {campaign['effective_status']}, Objective: {campaign['objective']}")
            contador += 1
        print('\n')
        print("@ Utiliza el [id] de una de las campañas de arriba dentro de la función getAdCampaigns() para obtener los datos de la campaña")
        print("-" * 40)

    def getFechaAyer(self) -> str:
        """
        Esta función obtiene la fecha de ayer
        """
        ayer = datetime.now() - timedelta(days=1)
        return ayer.strftime('%Y-%m-%d')
    

# Test
dict_env = {'ruta':'./config.env','nombre_token':'ACCESS_TOKEN_META'}
meta = API_meta(dict_env)
meta.getAdAccounts(True)
id_cta_pub = meta.getIdAccount(1)
meta.getAdCampaigns(id_cta_pub,True)


