import abc
import typing

class Cleaner(abc.ABC):
    @staticmethod
    def clean() ->  typing.Any:
        pass
        

      
class HTTPCLeaner(Cleaner):
    @staticmethod
    def clean_groups() -> typing.Any:
        pass










