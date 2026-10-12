from common import *
import ctypes,io
from mutagen.oggvorbis import OggVorbis
_dll=None;_func=None
def decrypt(data):
    global _dll,_func
    if data[:4]!=b'FCD\x00' or len(data)<16:raise ValueError('Invalid FCD header')
    offset=int.from_bytes(data[8:12],'big');kind=int.from_bytes(data[12:16],'big')
    if data[offset:offset+4]==b'OggS':result=data[offset:];method='plaintext embedded OGG'
    elif kind==2:
        if _func is None:
            dllpath=W/'tools/fcd/fzmedia-win64vc14-release-dynamic.dll';_dll=ctypes.WinDLL(str(dllpath))
            _func=ctypes.CFUNCTYPE(None,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint)(_dll._handle+0x3BDE0)
        b=bytearray(data);b[12:16]=struct.pack('<I',2);b[6:8]=struct.pack('<H',1)
        pointer=ctypes.addressof(ctypes.c_char.from_buffer(b));_func(pointer,pointer+28,len(b)-28)
        pos=b.find(b'OggS',28)
        if pos<0:raise ValueError('Native decryption returned no OGG')
        result=bytes(b[pos:]);method='FSNr_tools native DLL RVA 0x3BDE0'
    else:raise ValueError(f'Unsupported FCD type {kind}, offset {offset}')
    media=OggVorbis(io.BytesIO(result));return result,{'duration':media.info.length,'sample_rate':media.info.sample_rate,'channels':media.info.channels,'bitrate':media.info.bitrate,'codec':'vorbis','output_format':'OGG','decrypt_method':method}
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('output');args=parser.parse_args()
    data,info=decrypt(pathlib.Path(args.input).read_bytes());pathlib.Path(args.output).write_bytes(data);print(json.dumps(info))
