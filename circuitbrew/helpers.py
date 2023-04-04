
import logging
from functools import wraps

class LogBlock:
    blocks = {}
    def __init__(self, name):
        if name not in LogBlock.blocks:
            msg = f'Starting {name}'
            LogBlock.blocks[name] = 'in progress'
        else:
            msg = f'Ending {name}'
            del LogBlock.blocks[name]
        logger = logging.getLogger(__name__)
        msg_len = len(msg)+16
        logger.info('\n'+'-'*msg_len)
        logger.info(f'\t{msg}')
        logger.info('-'*msg_len)
    

def log_block(block_name):
    def printer():
        logger.info('\n------------')
        logger.info(f'\tStarting {block_name}')
        yield
        logger.info(f'\tEnding {block_name}')

    
class WithId:
    count = 0
    def __init__(self):
        self.count = WithId.count
        WithId.count += 1

def is_listable(self, obj):
    from typing import Iterable, Sequence, MutableSequence, Mapping, Text
    if(isinstance(obj, type)): 
        return isListable(obj.__new__(obj))
    return isinstance(obj, MutableSequence)
def iter_flattened_boogie(self, myiter, filter=lambda x: x is not None):
    # """Iterator to flatten arbitrary nested lists"""
    # if self.is_listable(myiter):
    #     for subitem in myiter:
    #         yield from self.iter_flattened(subitem, filter)
    # else:
    #     if filter(myiter):
    #         yield myiter
    #     else:
    #         return
    # return
    try:
        # IF this throws an exception, it's not an iterable
        iterator = iter(myiter)
    except TypeError:
        # myiter is not an iterable, so just yield it if it matches the filter
        if filter(myiter):
            yield myiter
        else:
            return
    else:
        # myiter is iterable, so let's recurse on it
        #for subitem in iterator:
        for subitem in myiter:
            yield from self.iter_flattened(subitem, filter)
class attach:
    def __init__(self, port_type, **kwargs):
        # TODO: check here to make sure parameters were entered
        print(f'decorating with {port_type}')
        self.port_type = port_type
        self.kwargs = kwargs

    def __call__ (self, cls):
        # Define a wrapper function to capture the actual instantiation and __init__ params
        @wraps(cls)
        def wrapper_f(*args, **kwargs):
            #print(f'type of cls is {type(cls)}')
            port = self.port_type(**self.kwargs)

            o = cls(*args, **kwargs)
            print(cls, args, kwargs)
            print(f"Decorating class {cls.__name__} with {self.port_type.__name__}")
            o.attach_port(port)
            #o.attach_sensor(peripheral)
            return o
        return wrapper_f

class attach_new:
    def __init__(self, port_type, **kwargs):
        # TODO: check here to make sure parameters were entered
        print(f'decorating with {port_type}')
        self.port_type = port_type
        self.kwargs = kwargs

    def __call__ (self, cls):
        # Define a wrapper function to capture the actual instantiation and __init__ params
        @wraps(cls)
        def wrapper_f(*args, **kwargs):
            #print(f'type of cls is {type(cls)}')
            port = self.port_type(**self.kwargs)

            o = cls(*args, **kwargs)
            print(cls, args, kwargs)
            print(f"Decorating class {cls.__name__} with {self.port_type.__name__}")
            o.attach_port(port)
            #o.attach_sensor(peripheral)
            return o
        return wrapper_f