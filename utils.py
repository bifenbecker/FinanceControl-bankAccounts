import base64
import json
import re
from typing import Optional, Union
from datetime import datetime

from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.response import Response

from bills.models import Bill
from operations.models import Operation, OperationToBill, CategoryToUser
from exceptions import ConvertDateException

try:
    from .producer import logger
except:
    print(f"[DEBUG] - {datetime.utcnow()} - [ERROR] - No connection to RABBIT_MQ")

HOST = 'http://docker.for.mac.localhost:10000'


def decode_base64(encoded_payload: Optional[str]) -> Optional[str]:
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    payload_bytes = encoded_payload.encode('ascii')
    error = None
    try:
        base64_bytes = base64.b64decode(payload_bytes)
        error = None
    except Exception as e:
        error = str(e)

    try:
        base64_bytes = base64.b64decode(payload_bytes + b'=' * (-len(payload_bytes) % 4))
        error = None
    except Exception as e:
        error = str(e)


    try:
        base64_bytes = base64.b64decode(payload_bytes + b'==')
        error = None
    except Exception as e:
        error = str(e)

    if not error:
        decoded_payload = base64_bytes.decode('ascii')
        return decoded_payload
    else:
        try:
            logger(error)
        except:
            print("Message was not send")
        return None


def convert_date(date: Union[str, int], pattern: Optional[str] = r'^\d{2}.\d{2}.\d{4}[ \d{2}:\d{2}:\d{2}]*$') -> Optional[datetime]:
    """
    Convert str datetime format DD.MM.YYYY HH:MM:SS
    :param date: string or integer(UNIX) date
    :return: datetime object
    """
    if isinstance(date, str):
        if re.match(pattern, date.strip()):
            date_part = date.split()[0]
            chunks = list(map(int, date_part.split(".")))
            time_part = date.split()[-1]
            if time_part != date_part:
                try:
                    time = list(map(int, time_part.split(":")))
                    return datetime(year=chunks[-1], month=chunks[1], day=chunks[0], hour=time[0], minute=time[1],
                                    second=time[2])
                except Exception as e:
                    raise ConvertDateException(str(e))
            else:
                return datetime(year=chunks[-1], month=chunks[1], day=chunks[0])
        else:
            raise ConvertDateException('No valid pattern - (DD.MM.YYYY HH:MM:SS)')

    elif isinstance(date, int):
        return datetime.utcfromtimestamp(date)
    else:
        raise ConvertDateException('No valid type of date')


def get_payload(func):
    """
    ?????????????????? ???????????????????? payload ???? ????????????????????
    :param func: ?????????? ????????????
    :return: Response
    """

    def wrapper(request, *args, **kwargs):
        try:
            encoded_payload = request.headers.get("x-jwt-payload")
        except Exception as e:
            return f"No x-jwt-payload - {str(e)}", status.HTTP_400_BAD_REQUEST

        decoded_payload = decode_base64(encoded_payload)
        if decoded_payload:
            kwargs.update({'decoded_payload': json.loads(decoded_payload)})
            res, status_code, msg = func(request, *args, **kwargs)
            return res, status_code, msg
        else:
            return f'Error in decoded payload', status.HTTP_400_BAD_REQUEST

    return wrapper


def process_response(func):
    """
    Return data and status code
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        data, response_status_code, logger_msg = func(*args, **kwargs)
        if logger_msg:
            try:
                logger(logger_msg)
            except:
                print("Message was not send")

        if isinstance(data, str):
            data = {'msg': data}
        return Response(
            data=data,
            status=response_status_code if response_status_code else status.HTTP_200_OK
        )

    return wrapper


def get_operation(func):
    """
    Get operation
    :param func:
    :return:
    """

    def wrapper(self, request, *args, **kwargs):
        try:
            operation_uuid = request.data.get('uuid')
        except:
            return {
                       'msg': 'No uuid'
                   }, status.HTTP_400_BAD_REQUEST

        operation = Operation.objects.filter(uuid=operation_uuid).first()

        if operation:
            kwargs.update({'operation': operation})
            res, status_code, msg = func(self=self, request=request, *args, **kwargs)
            return res, status_code, msg
        else:
            return {'msg': 'Incorrect uuid'}, status.HTTP_404_NOT_FOUND

    return wrapper


def get_bill(func):
    """
    Get bank from request data
    :param func:
    :return: Bank
    """

    def wrapper(self, request, *args, **kwargs):
        if 'uuid' in request.data.keys():
            bill_uuid = request.data.pop('uuid')  # todo: check pop in data
        elif 'uuid' in request.headers.keys():
            bill_uuid = request.headers.get('uuid')
        else:
            return {'msg': 'No bill uuid'}, status.HTTP_400_BAD_REQUEST

        try:
            bill = Bill.objects.filter(uuid=bill_uuid).first()
        except ValidationError as e:
            return {'msg': ''.join(e)}, status.HTTP_400_BAD_REQUEST
        except Exception as e:
            return {'msg': str(e)}, status.HTTP_400_BAD_REQUEST

        if bill:
            kwargs.update({'bill': bill})
            res, status_code, msg = func(self=self, request=request, *args, **kwargs)
            return res, status_code, msg
        else:
            return {'msg': 'Incorrect uuid'}, status.HTTP_404_NOT_FOUND

    return wrapper


def get_user_id_from_payload(func):
    """
    Get user id from payload
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        try:
            decoded_payload = kwargs['decoded_payload']
        except:
            return "No decoded payload in args", status.HTTP_400_BAD_REQUEST
        if decoded_payload:
            user_id = decoded_payload['id']
            kwargs.update({'user_id': user_id})
            res, status_code, msg = func(*args, **kwargs)
            return res, status_code, msg
        else:
            return "Payload is None", status.HTTP_400_BAD_REQUEST

    return wrapper


def all_methods_get_payload(cls):
    """
    Each method get payload from headers
    :param cls: Class
    :return: Class
    """

    def wrapper(arg):
        class Cls(cls):
            def __init__(self, *args, **kwargs):
                self._obj = arg(*args, **kwargs)

            def __getattribute__(self, item):
                try:
                    x = super().__getattribute__(item)
                except:
                    pass
                else:
                    return x
                attr = self._obj.__getattribute__(item)
                if isinstance(attr, type(self.__init__)):
                    return process_response(get_payload(attr))
                else:
                    return attr

        return Cls
    return wrapper




