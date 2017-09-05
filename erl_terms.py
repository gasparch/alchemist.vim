import struct
#def encode(py_struct):

FORMAT_VERSION = '\x83' #struct.pack("b", 131)

NEW_FLOAT_EXT = 70      # [Float64:IEEE float]
BIT_BINARY_EXT = 77     # [UInt32:Len, UInt8:Bits, Len:Data]
SMALL_INTEGER_EXT = struct.pack("b", 97)  # [UInt8:Int]
INTEGER_EXT = struct.pack("b", 98)        # [Int32:Int]
FLOAT_EXT = 99          # [31:Float String] Float in string format (formatted "%.20e", sscanf "%lf"). Superseded by NEW_FLOAT_EXT
ATOM_EXT = struct.pack("b", 100)          # 100 [UInt16:Len, Len:AtomName] max Len is 255
REFERENCE_EXT = 101     # 101 [atom:Node, UInt32:ID, UInt8:Creation]
PORT_EXT = 102          # [atom:Node, UInt32:ID, UInt8:Creation]
PID_EXT = 103           # [atom:Node, UInt32:ID, UInt32:Serial, UInt8:Creation]
SMALL_TUPLE_EXT = 104   # [UInt8:Arity, N:Elements]
LARGE_TUPLE_EXT = 105   # [UInt32:Arity, N:Elements]
NIL_EXT = struct.pack("b", 106)           # empty list
STRING_EXT = 107        # [UInt32:Len, Len:Characters]
LIST_EXT = struct.pack("b", 108)          # [UInt32:Len, Elements, Tail]
BINARY_EXT = struct.pack("b", 109)        # [UInt32:Len, Len:Data]
SMALL_BIG_EXT = 110     # [UInt8:n, UInt8:Sign, n:nums]
LARGE_BIG_EXT = 111     # [UInt32:n, UInt8:Sign, n:nums]
NEW_FUN_EXT = 112       # [UInt32:Size, UInt8:Arity, 16*Uint6-MD5:Uniq, UInt32:Index, UInt32:NumFree, atom:Module, int:OldIndex, int:OldUniq, pid:Pid, NunFree*ext:FreeVars]
EXPORT_EXT = 113        # [atom:Module, atom:Function, smallint:Arity]
NEW_REFERENCE_EXT = 114 # [UInt16:Len, atom:Node, UInt8:Creation, Len*UInt32:ID]
SMALL_ATOM_EXT = 115    # [UInt8:Len, Len:AtomName]
MAP_EXT = struct.pack("b", 116)
FUN_EXT = 117           # [UInt4:NumFree, pid:Pid, atom:Module, int:Index, int:Uniq, NumFree*ext:FreeVars]
COMPRESSED = 80         # [UInt4:UncompressedSize, N:ZlibCompressedData]

def decode(binary):
    """
        >>> decode('\\x83' + SMALL_INTEGER_EXT + '\x01')
        1
        >>> decode('\\x83\\x74\\x00\\x00\\x00\\x01\\x64\\x00\\x05\\x65\\x72\\x72\\x6F\\x72\\x64\\x00\\x03\\x6E\\x69\\x6c')
        {'error': None}
        >>> decode(encode(-256))
        -256
        >>> decode(encode(False))
        False
        >>> decode(encode(True))
        True
        >>> decode(encode(None))
        >>> decode(encode("Hello"))
        'Hello'
        >>> decode(encode([]))
        []
        >>> decode(encode([1]))
        [1]
        >>> decode(encode(['a']))
        ['a']
        >>> decode(encode({'error': None, 'payload': {'active_param': 1, 'pipe_before': False}, 'signatures': [{'docs': 'docs', 'name': 'name', 'params': ['list']}, {'docs': 'snd doc', 'params': ['list']}], 'request_id': 1 }))
        {'error': None, 'signatures': [{'docs': 'docs', 'params': ['list'], 'name': 'name'}, {'docs': 'snd doc', 'params': ['list']}], 'payload': {'active_param': 1, 'pipe_before': False}, 'request_id': 1}
    """
    if binary[0] != FORMAT_VERSION:
        raise NotImplementedError("Unable to serialize version %s" % binary[0])
    binary = binary[1:]

    (obj_size, fn) = __decode_func(binary)
    return fn(binary[0: obj_size])

def __decode_func(binary):
    if binary[0] == SMALL_INTEGER_EXT:
        return (2, __decode_int)
    elif binary[0] == INTEGER_EXT:
        return (5, __decode_int)
    elif binary[0] == BINARY_EXT:
        (size, ) = struct.unpack(">L", binary[1:5])
        return (1 + 4 + size, __decode_string)
    elif binary[0] == ATOM_EXT:
        (size, ) = struct.unpack(">H", binary[1:3])
        return (1 + 2 + size, __decode_atom)
    elif binary[0] == NIL_EXT:
        return (1, __decode_list)
    elif binary[0] == LIST_EXT:
        (list_size, ) = struct.unpack(">L", binary[1:5])
        tmp_binary = binary[5:]
        byte_size = 0
        for i in xrange(list_size):
            (obj_size, fn) = __decode_func(tmp_binary)
            byte_size = byte_size + obj_size
            tmp_binary = tmp_binary[obj_size:]
        return (1 + 4 + byte_size + 1, __decode_list)
    elif binary[0] == MAP_EXT:
        (map_size, ) = struct.unpack(">L", binary[1:5])
        tmp_binary = binary[5:]
        byte_size = 0
        for i in xrange(map_size):
            (obj_size, fn) = __decode_func(tmp_binary)
            byte_size = byte_size + obj_size
            tmp_binary = tmp_binary[obj_size:]


            (obj_size, fn) = __decode_func(tmp_binary)
            byte_size = byte_size + obj_size
            tmp_binary = tmp_binary[obj_size:]
        return (1 + 4 + byte_size , __decode_map)
    else:
        raise NotImplementedError("Unable to unserialize %r" % binary[0])

def __decode_map(binary):
    """
        >>> __decode_map(__encode_map({'foo': 1}))
        {'foo': 1}
        >>> __decode_map(__encode_map({'foo': 'bar'}))
        {'foo': 'bar'}
        >>> __decode_map(__encode_map({'foo': {'bar': 4938}}))
        {'foo': {'bar': 4938}}
        >>> __decode_map(__encode_map({'error': None, 'payload': {'active_param': 1, 'pipe_before': False}, 'signatures': [{'docs': 'docs', 'name': 'name', 'params': ['list']}, {'docs': 'snd doc', 'params': ['list']}], 'request_id': 1 }))
        {'error': None, 'signatures': [{'docs': 'docs', 'params': ['list'], 'name': 'name'}, {'docs': 'snd doc', 'params': ['list']}], 'payload': {'active_param': 1, 'pipe_before': False}, 'request_id': 1}
    """
    (size,) = struct.unpack(">L", binary[1:5])
    result = {}
    binary = binary[5:]
    for i in xrange(size):

        (key_obj_size, key_fn) = __decode_func(binary)
        key = key_fn(binary[0: key_obj_size])
        binary = binary[key_obj_size:]

        (value_obj_size, value_fn) = __decode_func(binary)
        value = value_fn(binary[0: value_obj_size])

        binary = binary[value_obj_size:]

        result.update({key: value})

    return result


def __decode_list(binary):
    """
        >>> __decode_list(__encode_list([]))
        []
        >>> __decode_list(__encode_list(['a']))
        ['a']
        >>> __decode_list(__encode_list([1]))
        [1]
        >>> __decode_list(__encode_list([1, 'a']))
        [1, 'a']
        >>> __decode_list(__encode_list([True, None, 1, 'a']))
        [True, None, 1, 'a']
    """
    if binary == NIL_EXT: return []
    (size, ) = struct.unpack(">L", binary[1:5])
    result = []
    binary = binary[5:]
    for i in xrange(size):
        (obj_size, fn) = __decode_func(binary)
        result.append(fn(binary[0: obj_size]))
        binary = binary[obj_size:]

    return result

def __decode_string(binary):
    """
        >>> __decode_string(__encode_string("h"))
        'h'
    """
    return binary[5:]

def __decode_atom(binary):
    """
        >>> __decode_atom(__encode_atom("nil"))
        >>> __decode_atom(__encode_atom("true"))
        True
        >>> __decode_atom(__encode_atom("false"))
        False
        >>> __decode_atom(__encode_atom("my_key"))
        'my_key'
    """
    atom = binary[3:]
    if atom == 'true':
        return True
    elif atom == 'false':
        return False
    elif atom == 'nil':
        return None
    return atom

def __decode_int(binary):
    """
        >>> __decode_int(__encode_int(1))
        1
        >>> __decode_int(__encode_int(256))
        256
    """
    if binary[0] == 'a' :
        (num,) = struct.unpack("B", binary[1])
        return num
    (num,) = struct.unpack(">l", binary[1:])
    return num

def encode(struct):
    """
        >>> encode(False)
        '\\x83d\\x00\\x05false'
        >>> encode([])
        '\\x83j'
    """
    return FORMAT_VERSION + __encoder_func(struct)(struct)

def __encode_list(obj):
    """
        >>> __encode_list([])
        'j'
        >>> __encode_list(['a'])
        'l\\x00\\x00\\x00\\x01m\\x00\\x00\\x00\\x01aj'
        >>> __encode_list([1])
        'l\\x00\\x00\\x00\\x01a\\x01j'
    """
    if len(obj) == 0:
        return NIL_EXT
    b = struct.pack(">L", len(obj))
    for i in obj:
        b = '%s%s' %(b, __encoder_func(i)(i))
    return LIST_EXT + b + NIL_EXT

def __encode_map(obj):
    """
        >>> __encode_map({'foo': 1})
        't\\x00\\x00\\x00\\x01m\\x00\\x00\\x00\\x03fooa\\x01'
        >>> __encode_map({'foo': 'bar'})
        't\\x00\\x00\\x00\\x01m\\x00\\x00\\x00\\x03foom\\x00\\x00\\x00\\x03bar'
        >>> __encode_map({'foo': {'bar': 4938}})
        't\\x00\\x00\\x00\\x01m\\x00\\x00\\x00\\x03foot\\x00\\x00\\x00\\x01m\\x00\\x00\\x00\\x03barb\\x00\\x00\\x13J'
    """
    b = struct.pack(">L", len(obj))
    for k,v in obj.iteritems():
        b = '%s%s%s' % (b, __encoder_func(k)(k), __encoder_func(v)(v))
    return MAP_EXT + b

def __encoder_func(obj):
    if isinstance(obj, str):
        return __encode_string
    elif isinstance(obj, bool):
        return __encode_boolean
    elif isinstance(obj, int):
        return __encode_int
    elif isinstance(obj, dict):
        return __encode_map
    elif isinstance(obj, list):
        return __encode_list
    elif obj is None:
        return __encode_none
    else:
        raise NotImplementedError("Unable to serialize %r" % obj)

def __encode_string(obj):
    """
        >>> __encode_string("h")
        'm\\x00\\x00\\x00\\x01h'
        >>> __encode_string("hello world!")
        'm\\x00\\x00\\x00\\x0chello world!'
    """
    return BINARY_EXT + struct.pack(">L", len(obj)) + obj

def __encode_none(obj):
    """
        >>> __encode_none(None)
        'd\\x00\\x03nil'
    """
    return __encode_atom("nil")

def __encode_boolean(obj):
    """
        >>> __encode_boolean(True)
        'd\\x00\\x04true'
        >>> __encode_boolean(False)
        'd\\x00\\x05false'
    """
    if obj == True:
        return __encode_atom("true")
    elif obj == False:
        return __encode_atom("false")
    else:
        raise "Maybe later"

def __encode_atom(obj):
    return ATOM_EXT + struct.pack(">H", len(obj)) + (b"%s" % obj)

def __encode_int(obj):
    """
        >>> __encode_int(1)
        'a\\x01'
        >>> __encode_int(256)
        'b\\x00\\x00\\x01\\x00'
    """
    if 0 <= obj <= 255:
        return SMALL_INTEGER_EXT +  struct.pack("B", obj)
    elif -2147483648 <= obj <= 2147483647:
        return INTEGER_EXT + struct.pack(">l", obj)
    else:
        raise "Maybe later"
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    #f = open('/tmp/erl_bin.txt', 'rb')
    #data = f.read()
    #print(len(data))
    #print(decode(data))
