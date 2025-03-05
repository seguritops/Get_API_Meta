class APIError(Exception):
    """Clase base para errores personalizados."""

    def __init__(self, message: str, tipo: str,indentacion:str=''):
        self.message = message
        # self.code = code  # Código de error opcional
        super().__init__(f"{indentacion}[{tipo}] {message}")

# Crear errores personalizados
Error_dict_format = APIError('Debes ingresar un diccionario con las llaves "ruta" y "nombre_token" en formato texto no nulo','Error Formato')
Error_get_token = APIError('Error al obtener el token. Por favor revisa la configuración de la variable de entorno o diccionario de acceso a ella','Error')
Error_ini_API = APIError('Error al inicializar la API de Facebook. Por favor revisa que el token sea válido para comenzar','Error')
Error_get_accounts = APIError('Error al obtener las cuentas de publicidad. Por favor revisa que el token sea válido para consultar los datos','Error')
Error_get_id_account = APIError('Error al obtener el ID de la cuenta de publicidad. Por favor revisa que el índice ingresado sea válido','Error Index')
Error_dict_vacio = APIError('Error al mapear las estadísticas de un anuncio. Por favor revisa que el diccionario no esté vacío','Error')
Error_API_request = APIError('Error al realizar la petición a la API de Meta. Por favor revisa que los parametros y metricas sean validos','Error consulta')
# Warnings
Warn_sin_data = APIError('La data resultante de la conulta no contiene información.','⚠️ Warning','     ')
