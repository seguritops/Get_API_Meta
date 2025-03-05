from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.user import User
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.ad import Ad
from facebook_business.exceptions import FacebookRequestError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from datetime import date
import pandas as pd
import requests
import time
import os
# Error Handler
from Error import *
# URLs
from URLs import DEBUG_TOKEN_URL,EXCHANGE_TOKEN_URL

####################################################
## API META
####################################################
class API_meta:
    def __init__(self,config_estats_publicidad:dict,fecha_captura:datetime | date | str = date.today()):
        self.hoy = fecha_captura
        self.ruta_config_estats_publicidad = config_estats_publicidad['ruta']
        self.hoja_config_estats_publicidad = config_estats_publicidad['hoja']
        self.campaigns = {}
        self.ads = {}
        self.data = {}
        self.segmentaciones_estats = [
            ["publisher_platform",'platform_position'],
            ["gender",'age'],
            ["country"]
        ]
        self.iniMetaAPI()

    ########################
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

    def getNombreCampaign(self,acct_id:str,campaign_id:str) -> str:
        """
        Esta función obtiene el nombre de una cuenta de publicidad
        """
        try:
            # Obtener nombre de la cuenta de publicidad
            for campaign in self.campaigns[acct_id]:
                campaign = dict(campaign)
                if campaign['id'] == campaign_id:
                    return campaign['name']
        except Exception as e:
            print(e)

    def getNombreAd(self,campaign_id:str,ad_id:str) -> str:
        """
        Esta función obtiene el nombre de una cuenta de publicidad
        """
        try:
            # Obtener nombre de la cuenta de publicidad
            for ad in self.ads[campaign_id]:
                ad = dict(ad)
                if ad['id'] == ad_id:
                    return ad['name']
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

    ########################
    # metodos
    def validacionToken(self) -> None:
        """
        Esta función valida el token actual guardado.
        Si el token actual ya no es válido, se solicita uno nuevo.
        Al obetener el nuevo token, se guarda en las variables de entorno para
        ser consumido posteriormente y ser un dato persistente.
        """
        if not self.validarToken(): # Validar token
            print('🔄 Solicitando nuevo Token')
            self.token = self.getNuevoToken() # Obtener nuevo token
            self.actEnvVariable(self.key_token,self.token) # Actualizar token en variable de entorno
            self.depurar_token(self.token) # Depurar token

    def saveCuentaLevelInDict(self) -> None:
        """
        Esta función itera sobre las cuentas alojadas en Config_Estats_Publicidad y
        las aloja en un diccionario de la clase par tener la data centralizada
        """
        for id_cuenta, campaigns in self.keys_config_stats.items():
            print(f"📌 Procesando cuenta: {id_cuenta} - {self.getNombreCuenta(str(id_cuenta))}")
            self.getAdCampaigns(id_cuenta)
            if str(id_cuenta) not in self.data.items(): self.data[str(id_cuenta)] = {}
            self.saveCampaignLevelInDict(str(id_cuenta),campaigns)

    def saveCampaignLevelInDict(self,acct_id:str,campaigns:dict) -> None:
        """
        Esta función itera sobre las campañas y
        las aloja en un diccionario de la clase par tener la data centralizada

        :param acct_id (str): ID de la cuenta
        :param camp_id (str): ID de la campaña
        """
        for id_camp, ads in campaigns.items():
            print(f"  🔹 Campaña: {id_camp} - {self.getNombreCampaign(str(acct_id),str(id_camp))}")
            self.getAds(id_camp)
            if str(id_camp) not in self.data[str(acct_id)].items(): self.data[str(acct_id)][str(id_camp)] = {}
            self.saveAdLevelInDict(str(acct_id),str(id_camp),ads)

    def saveAdLevelInDict(self,acct_id:str,camp_id:str,ads:list[str]) -> None:
        """
        Esta función itera sobre los anuncios y
        los aloja en un diccionario de la clase par tener la data centralizada

        :param acct_id (str): ID de la cuenta
        :param camp_id (str): ID de la campaña
        :param ad_id (str): ID del anuncio
        """
        for id_ad in ads:
            print(f"    ▶️ Anuncio: {id_ad} - {self.getNombreAd(str(camp_id),str(id_ad))}")
            if str(id_ad) not in self.data[str(acct_id)][str(camp_id)].items(): self.data[str(acct_id)][str(camp_id)][str(id_ad)] = {}
            self.saveAdDataInDict(str(acct_id),str(camp_id),str(id_ad))
                
    def saveAdDataInDict(self,acct_id:str,camp_id:str,ad_id:str) -> None:
        """
        Esta función itera en 3 opciones (configurables) de breakdowns,
        obtiene la data mediante una consulta (Ad.get_insights()) y
        lo aloja en un diccionario de la clase par tener la data centralizada

        :param acct_id (str): ID de la cuenta
        :param camp_id (str): ID de la campaña
        :param ad_id (str): ID del anuncio
        """
        index = 0
        for segmentacion in self.segmentaciones_estats:
            params = {
                "level": "ad",
                "breakdowns": segmentacion
            }
            df = self.getAdEstats(
                str(acct_id),
                str(camp_id),
                self.findAdInAds(str(camp_id),str(ad_id)),
                params=params
            )
            self.data[str(acct_id)][str(camp_id)][str(ad_id)][str(index)] = df
            index += 1

    ########################
    # CONTROLADORES
    def runAPI(self) -> None:
        """
        Esta función ejecuta la API de Meta
        """
        try:
            ######################
            # VALIODACION TOKEN
            ######################
            self.validacionToken()
            ######################
            # OBTENER DATA
            ######################
            print('🔄 Buscando cuentas...')
            self.getAdAccounts()
            self.keys_config_stats = self.getConfigEstatsPublicidad()
            self.saveCuentaLevelInDict()
            return self.data
        except Exception as e:
            print(e)
    
    ########################
    # TOKEN
    def getToken(self,show=False) -> str:
        """
        Esta función obtiene el token de Meta desde la variable de entorno
        """
        try:
            self.token = self.getAppPass()[0]
            # Validar formato del diccionario de acceso a la variable de entorno
            if type(self.token) != str:
                raise Error_dict_format
            # Validar que el token no sea nulo
            if self.token is None:
                raise Error_get_token
            if show: print('➜ Token obtenido con éxito')
            return self.token
        except Exception as e:
            print(e)

    def validarToken(self) -> None:
        """Verifica si el token de acceso es válido."""
        ACCESS_TOKEN_META,APP_ID,APP_SECRET = self.getAppPass()
        params = {
            "input_token": self.token,
            "access_token": f"{APP_ID}|{APP_SECRET}"
        }
        response = requests.get(DEBUG_TOKEN_URL, params=params)
        data = response.json()

        if "data" in data and data["data"].get("is_valid"):
            expires_at = data["data"].get("expires_at")
            if expires_at:
                tiempo_restante = expires_at - int(time.time())
                print("✅ Token válido. Expira en:", self.formato_expiracion(tiempo_restante))
                print("🔹"+"-" * 40)
                return True
        else:
            print("⚠️ Token inválido o expirado.")
            return False
    
    def getNuevoToken(self) -> str:
        """Obtiene un nuevo token de acceso intercambiando el token actual."""
        ACCESS_TOKEN,APP_ID,APP_SECRET = self.getAppPass()
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": APP_ID,
            "client_secret": APP_SECRET,
            "fb_exchange_token": ACCESS_TOKEN
        }
        response = requests.get(EXCHANGE_TOKEN_URL, params=params)
        data = response.json()

        if "access_token" in data:
            nuevo_token = data["access_token"]
            print("✅ Nuevo token obtenido.")
            return nuevo_token
        else:
            print("❌ Error al obtener un nuevo token:", data)
            return None

    def depurar_token(self,token):
        """Intenta depurar el token para extender su validez."""
        depuration_url = f"https://graph.facebook.com/v22.0/me?access_token={self.token}"
        response = requests.get(depuration_url)
        data = response.json()

        if "id" in data:
            print("✅ Token depurado correctamente.")
            return token
        else:
            print("❌ Error al depurar el token:", data)
            return None

    ########################
    # ACCESO RECURSOS API
    def iniMetaAPI(self) -> None:
        """
        Esta función inicializa la API de Meta con el token de acceso
        """
        print('\n')
        print(f"🚀 INICIO API META")
        print('\n')
        try:
            # Inicializar la API de Facebook
            FacebookAdsApi.init(access_token=self.getToken(True))
            print('➜ API de Facebook inicializada con éxito')
            print("🔹"+"-" * 40)
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
            print('➜ Cuentas de publicidad obtenidas con éxito')
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
            self.campaigns[str(account_id)] = list(ad_account.get_campaigns(
                fields=["id", "name", "status", "effective_status", "objective", "start_time", "stop_time"])
            )
            # print(self.campaigns[str(account_id)])
            print('✅ Campañas obtenidas con éxito')
            if mostrar_campaigns: self.printCampaigns(str(account_id))
            return self.campaigns[str(account_id)]
        except Exception as e:
            print(e)

    def getAds(self,campaign_id:str,mostrar:bool=False) -> list:
        """
        Esta función obtiene los anuncios de una campaña
        """
        try:
            # Obtener anuncios de una campaña
            campaign = Campaign(fbid=campaign_id)
            self.ads[str(campaign_id)] = list(campaign.get_ads(
                fields=["id", "name", "status", "effective_status"])
            )
            # print(f'🔄 Buscando anuncios para la campaña {self.getNombreCampaign(campaign_id)}...')
            # print('\n')
            if mostrar: self.printAds(str(campaign_id))
            return self.ads[str(campaign_id)]
        except Exception as e:
            print(e)

    def getAdEstats(self,
                    id_account:str,
                    id_campaign:str,
                    ad:Ad,
                    fields:list=[
                        "reach",                          
                        "impressions",                 
                        "inline_link_clicks",      
                        "cpc",                        
                        "actions",
                        "spend"
                    ],
                    params:dict={
                        "level": "ad",
                        "breakdowns": ["gender",'age']
                        # "breakdowns": ["country"]
                        # "breakdowns": ["publisher_platform",'platform_position']
        }) -> pd.DataFrame:
        """
        Esta función obtiene las estadísticas de un anuncio
        """
        params["time_range"] = {"since": str(self.hoy), "until": str(self.hoy)}
        try:
            respuesta = ad.get_insights(fields=fields, params=params)
            id_ad = ad['id']
            nombre_ad = ad['name']
            datos_ad = {
                'id_acct':id_account,
                'id_camp':id_campaign,
                'id':id_ad,
                'name':nombre_ad
            }
            # print(f'Este es el ID del AD: {id_ad}')
            # print(f'Este es el NOMBRE del AD: {nombre_ad}')
            data = self.estatToDataframe(respuesta,datos_ad)
            return data
        except Exception as e:
            print('\n')
            print("Código de error:", e.http_status())
            print("Mensaje de error:", e.api_error_message())

    ########################
    # metodos auxiliares
    def printAccounts(self,show_i:bool=False) -> None:
        """
        Esta función imprime las cuentas de publicidad
        """
        print('➜ Cuentas obtenidas desde Meta...')
        contador = 0
        for account in self.adAccounts:
            print(f"[{contador}] 📌 ID Cuenta: {account['account_id']}, Nombre: {account['name']}")
            contador += 1
        if show_i:
            print('\n')
            print("ℹ️ Utiliza el [id] de una de las cuentas de arriba dentro de la función getIdAccount() para obtener el ID de la cuenta de publicidad")
        print("🔹"+"-" * 40)

    def printCampaigns(self,acct_id:str,show_i:bool=False) -> None:
        """
        Esta función imprime las campañas de una cuenta de publicidad
        """
        print('ESTOOOOY EN PRINT CAMPAIGNS')
        contador = 0
        for campaign in self.campaigns[acct_id]:
            print(f"[{contador}] 🎯 ID Campaña: {campaign['id']}, Nombre: {campaign['name']}, Estado: {campaign['status']}, Estado Efectivo: {campaign['effective_status']}, Objetivo: {campaign['objective']}")
            contador += 1
        if show_i:
            print('\n')
            print("ℹ️ Utiliza el [id] de una de las campañas de arriba dentro de la función getAds() para obtener los datos de la campaña")
        print("-" * 40)

    def printAds(self,camp_id:str) -> None:
        """
        Esta función imprime las campañas de una cuenta de publicidad
        """
        print(f'✅ Anuncios obtenidos con éxito...')
        contador = 0
        for ad in self.ads[str(camp_id)]:
            print(f"[{contador}] ✏️  ID Anuncio: {ad['id']}, Nombre: {ad['name']}, Estado: {ad['status']}, Estado Efectivo: {ad['effective_status']}")
            contador += 1
        print("🔹"+"-" * 40)

    def getFechaAyer(self) -> str:
        """
        Esta función obtiene la fecha de ayer
        """
        ayer = datetime.now() - timedelta(days=1)
        return ayer.strftime('%Y-%m-%d')
    
    def mapEstatElement(self,estat:dict) -> list:
        """
        Esta función mapea las estadísticas de un anuncio
        Solo recibe un elemento del resultado completo
        """
        estats = dict(estat)
        # print(dict(estats))
        try:
            estat_keys = list(estats.keys())
            # print(met_keys)
            if len(estat_keys) == 0: raise Error_dict_vacio
            # return pd.DataFrame(dict(estat))
            met_dict = {}
            not_str = {}
            for met in estats:
                if type(estats[met]) == str:
                    met_dict[met] = estats[met]
                else:
                    not_str[met] = estats[met]
                    data = not_str[met]
                    for metric in data:
                        key = metric[list(metric.keys())[0]]
                        value = metric[list(metric.keys())[1]]
                        met_dict[key] = value
            return met_dict
        except Exception as e:
            print(e)

    def mapEstat(self,estats:list) -> list:
        """
        Esta función mapea las estadísticas de un anuncio
        Recibe el resultado completo
        """
        try:
            # Validar que el diccionario no esté vacío
            if len(estats) == 0: raise Error_dict_vacio
            # Mapear estadísticas de anuncios
            data = []
            for estat in estats:
                data.append(self.mapEstatElement(estat))
            return data
        except Exception as e:
            print(e)

    def estatToDataframe(self,estats:list,datos_ad:list) -> pd.DataFrame | None:
        """
        Esta función convierte las estadísticas de un anuncio en un DataFrame
        """
        try:
            # Validar que la data no esté vacía
            if len(estats) == 0: raise Warn_sin_data
            data = self.mapEstat(estats)
            # Convertir estadísticas a DataFrame
            met_keys = list(data[0].keys())
            datos_ini = {variable: [] for variable in met_keys}
            df = pd.DataFrame(datos_ini)
            for row in data:
                df.loc[len(df)] = row
            df['id_account'] = datos_ad['id_acct']
            df['id_campaign'] = datos_ad['id_camp']
            df['id_ad'] = datos_ad['id']
            df['nombre_ad'] = datos_ad['name']
            return df
        except Exception as e:
            print(e)

    def getAppPass(self) -> list:
        """
        Esta función obtiene los datos de la aplicación
        """
        try:
            load_dotenv()
            ACCESS_TOKEN_META = os.getenv('ACCESS_TOKEN_META')
            APP_ID = os.getenv('APP_ID')
            APP_SECRET = os.getenv('APP_SECRET')
            return [ACCESS_TOKEN_META,APP_ID,APP_SECRET]
        except Exception as e:
            print(e)

    def formato_expiracion(self,tpo_rest:int) -> str:
        """Convierte los segundos restantes en una unidad más legible."""
        if type(tpo_rest) != int:
            raise TypeError("El tiempo restante debe ser un número entero.")
        if tpo_rest < 60:
            return f"{tpo_rest} segundos"
        elif tpo_rest < 3600:
            return f"{tpo_rest // 60} minutos"
        elif tpo_rest < 86400:
            return f"{tpo_rest // 3600} horas"
        else:
            return f"{tpo_rest // 86400} días"
    
    def actEnvVariable(self,txt_key, txt_nuevo, archivo=".env"):
        """Actualiza o agrega una variable en el archivo .env."""
        with open(archivo, "r") as f:
            lineas = f.readlines()

        with open(archivo, "w") as f:
            encontrado = False
            for linea in lineas:
                if linea.startswith(txt_key + "="):
                    f.write(f"{txt_key}={txt_nuevo}\n")
                    encontrado = True
                else:
                    f.write(linea)
            if not encontrado:
                f.write(f"{txt_key}={txt_nuevo}\n")  # Agregar si no existe

    def getConfigEstatsPublicidad(self) -> dict:
        # Leer el Excel en un DataFrame
        df = pd.read_excel(self.ruta_config_estats_publicidad, sheet_name=self.hoja_config_estats_publicidad)
        # Inicializamos el objeto que contendrá la estructura
        data_structure = {}
        # Recorremos cada fila del DataFrame
        for _, row in df.iterrows():
            # Extraemos la información de cada columna
            id_cuenta  = row['ID_Cuenta']
            id_camp = row['ID_Campaña']
            id_ad       = row['ID_Anuncio']
            
            # Si la cuenta aún no está en el diccionario, se crea la entrada
            if id_cuenta not in data_structure:
                data_structure[id_cuenta] = {}

            # Si la campaña aún no está en la cuenta, se crea la entrada
            if id_camp not in data_structure[id_cuenta]:
                data_structure[id_cuenta][id_camp] = []

            # Se añade el anuncio a la lista de anuncios dentro de la campaña
            if id_ad not in data_structure[id_cuenta][id_camp]:
                data_structure[id_cuenta][id_camp].append(id_ad)
        
        return data_structure

    def findAdInAds(self, id_camp:str, id_ad:str) -> Ad:
        """
        Busca un anuncio en un diccionario estructurado por campañas.

        :param id_camp: ID de la campaña a buscar (str)
        :param id_ad: ID del anuncio a buscar dentro de la campaña (str)
        :return: (Ad) Diccionario con los datos del anuncio o None si no se encuentra
        """
        # Buscar si la campaña existe
        if id_camp in self.ads:
            ads_list = self.ads[str(id_camp)]  # Obtener la lista de anuncios en esa campaña

            # Buscar el anuncio dentro de la lista de la campaña
            for ad in ads_list:
                if ad.get("id") == id_ad:
                    return ad
                    # {
                    #     "id": ad["id"],
                    #     "name": ad["name"],
                    #     "effective_status": ad["effective_status"],
                    #     "status": ad["status"]
                    # }

        return None

# Test

# load_dotenv()
# APP_ID = os.getenv('APP_ID')
# APP_SECRET = os.getenv('APP_SECRET')

# print(APP_ID)
# print(APP_SECRET)

cep = {
    'ruta':'C:\\Python_APIs\\Meta\\Config_Estats_Publicidad - copia.xlsx',
    'hoja':'Estats_Publicidad_Meta'
}
meta = API_meta(cep)
# meta = API_meta(cep,fecha_captura="2025-03-03")
data = meta.runAPI()

# print(data.items())


# meta.getAdAccounts(True)
# id_cta_pub = meta.getIdAccount(1)
# campaña = meta.getAdCampaigns(id_cta_pub,True)
# ads = meta.getAds(campaña[0]['id'],True)
# metricas = ['reach','spend','impressions','cpc']
# parametros = {
#     'level': 'ad',
#     "breakdowns": ["age",'gender']
# }
# print(df)

# data.to_csv('data_test.csv',index=False)


# FacebookAdsApi.init(access_token=dict_env['ACCESS_TOKEN_META']) 

# me = User(fbid="me")
# user_fields = ["account_id", "id", "name"]
# my_accounts = list(me.get_ad_accounts(fields=user_fields))

# for account in my_accounts:
#     print(f"Account ID: {account['account_id']}, Name: {account['name']}")