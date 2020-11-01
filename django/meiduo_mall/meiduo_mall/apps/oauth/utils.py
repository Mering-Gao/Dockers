from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

def generate_access_token_by_openid(openid):
    '''把openid加密为access_token'''

    obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=600)


    dict = {
        'openid':openid
    }

    access_token = obj.dumps(dict).decode()

    return access_token



def check_access_token(access_token):
    '''把access_token解密为openid'''

    obj = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=600)

    try:
        data = obj.loads(access_token)
    except Exception as e:
        return None
    else:
        return data.get('openid')





























