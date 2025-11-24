from kavenegar import *
from core.settings import kavenegar_API
from random import randint
from .models import MyUser
import datetime

def send_otp(mobile, otp):
    mobile = [mobile,]
    try:
        api = KavenegarAPI(kavenegar_API)
        params = {
            'sender': '', 
            'receptor': '0098'+mobile[0],
            'template': 'verify', 
            # 'token': 'Your OTP is {}'.format(otp),
            'token': f'{otp}'
        } 
        response = api.verify_lookup(params)
        # print(response)
    except APIException as e: 
        # print(f"APIException: {e}")
        return {'error': str(e)}
    except HTTPException as e: 
        # print(f"HTTPException: {e}")
        return {'error': str(e)}
    print(f"otp: {otp}")

def get_random_otp():
    return randint(1000, 9999)

def check_otp_expiration(mobile):
    try:
        user = MyUser.objects.get(mobile=mobile)
        now = datetime.datetime.now()
        otp_time = user.otp_create_date

        diff_time = now - otp_time
        # print(f' OTP TIME: {diff_time}')

        if diff_time.seconds > 30:
            return False
        return True

    except MyUser.DoesNotExist:
        return False
    


 