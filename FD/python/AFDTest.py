#-*- encoding=utf-8 -*-

from arcsoft import CLibrary, ASVL_COLOR_FORMAT, ASVLOFFSCREEN,c_ubyte_p,FaceInfo
from arcsoft.utils import BufferInfo, ImageLoader
from arcsoft.AFD_FSDKLibrary import *
from ctypes import *
import traceback

APPID = c_char_p(b'XXXXXXXXXX')
FD_SDKKEY = c_char_p(b'YYYYYYYYYY')
FD_WORKBUF_SIZE = 20 * 1024 * 1024
MAX_FACE_NUM = 50
bUseYUVFile = False
bUseBGRToEngine = True

def doFaceDetection(hFDEngine, inputImg):
    faceInfo = []

    pFaceRes = POINTER(AFD_FSDK_FACERES)()
    ret = AFD_FSDK_StillImageFaceDetection(hFDEngine, byref(inputImg), byref(pFaceRes))
    if ret != 0:
        print(u'AFD_FSDK_StillImageFaceDetection 0x{0:x}'.format(ret))
        return faceInfo

    faceRes = pFaceRes.contents
    if faceRes.nFace > 0:
        for i in range(0, faceRes.nFace):
            rect = faceRes.rcFace[i]
            orient = faceRes.lfaceOrient[i]
            faceInfo.append(FaceInfo(rect.left,rect.top,rect.right,rect.bottom,orient))

    return faceInfo


def loadYUVImage(yuv_filePath, yuv_width, yuv_height, yuv_format):
    yuv_rawdata_size = 0

    inputImg = ASVLOFFSCREEN()
    inputImg.u32PixelArrayFormat = yuv_format
    inputImg.i32Width = yuv_width
    inputImg.i32Height = yuv_height
    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3 // 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 2
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 2
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.pi32Pitch[0] = inputImg.i32Width * 3
        yuv_rawdata_size = inputImg.i32Width * inputImg.i32Height * 3
    else:
        print(u'unsupported  yuv format')
        exit(0)

    # load YUV Image Data from File
    f = None
    try:
        f = open(yuv_filePath, u'rb')
        imagedata = f.read(yuv_rawdata_size)
    except Exception as e:
        traceback.print_exc()
        print(e.message)
        exit(0)
    finally:
        if f is not None:
            f.close()

    if ASVL_COLOR_FORMAT.ASVL_PAF_I420 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV12 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_NV21 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_YUYV == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    elif ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8 == inputImg.u32PixelArrayFormat:
        inputImg.ppu8Plane[0] = cast(imagedata, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        print(u'unsupported yuv format')
        exit(0)

    inputImg.gc_ppu8Plane0 = imagedata
    return inputImg

def loadImage(filePath):

    inputImg = ASVLOFFSCREEN()
    if bUseBGRToEngine:
        bufferInfo = ImageLoader.getBGRFromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_RGB24_B8G8R8
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = bufferInfo.width*3
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(0, c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    else:
        bufferInfo = ImageLoader.getI420FromFile(filePath)
        inputImg.u32PixelArrayFormat = ASVL_COLOR_FORMAT.ASVL_PAF_I420
        inputImg.i32Width = bufferInfo.width
        inputImg.i32Height = bufferInfo.height
        inputImg.pi32Pitch[0] = inputImg.i32Width
        inputImg.pi32Pitch[1] = inputImg.i32Width // 2
        inputImg.pi32Pitch[2] = inputImg.i32Width // 2
        inputImg.ppu8Plane[0] = cast(bufferInfo.buffer, c_ubyte_p)
        inputImg.ppu8Plane[1] = cast(addressof(inputImg.ppu8Plane[0].contents) + (inputImg.pi32Pitch[0] * inputImg.i32Height), c_ubyte_p)
        inputImg.ppu8Plane[2] = cast(addressof(inputImg.ppu8Plane[1].contents) + (inputImg.pi32Pitch[1] * inputImg.i32Height // 2), c_ubyte_p)
        inputImg.ppu8Plane[3] = cast(0, c_ubyte_p)
    inputImg.gc_ppu8Plane0 = bufferInfo.buffer

    return inputImg


if __name__ == u'__main__':
    print(u'#####################################################')

    # init Engine
    pFDWorkMem = CLibrary.malloc(c_size_t(FD_WORKBUF_SIZE))

    hFDEngine = c_void_p()
    ret = AFD_FSDK_InitialFaceEngine(APPID, FD_SDKKEY, pFDWorkMem, c_int32(FD_WORKBUF_SIZE), byref(hFDEngine), AFD_FSDK_OPF_0_HIGHER_EXT, 32, MAX_FACE_NUM)
    if ret != 0:
        CLibrary.free(pFDWorkMem)
        print(u'AFD_FSDK_InitialFaceEngine ret 0x{:x}'.format(ret))
        exit(0)

    # print FDEngine version
    versionFD = AFD_FSDK_GetVersion(hFDEngine)
    print(u'{} {} {} {}'.format(versionFD.contents.lCodebase, versionFD.contents.lMajor, versionFD.contents.lMinor, versionFD.contents.lBuild))
    print(c_char_p(versionFD.contents.Version).value.decode(u'utf-8'))
    print(c_char_p(versionFD.contents.BuildDate).value.decode(u'utf-8'))
    print(c_char_p(versionFD.contents.CopyRight).value.decode(u'utf-8'))

    # load Image Data
    if bUseYUVFile:
        filePath = u'001_640x480_I420.YUV'
        yuv_width = 640
        yuv_height = 480
        yuv_format = ASVL_COLOR_FORMAT.ASVL_PAF_I420

        inputImg = loadYUVImage(filePath, yuv_width, yuv_height, yuv_format)
    else:
        filePath = u'003.jpg'

        inputImg = loadImage(filePath)

    # do Face Detect
    faceInfos = doFaceDetection(hFDEngine, inputImg)
    for i in range(0, len(faceInfos)):
        rect = faceInfos[i]
        print(u'{} ({} {} {} {}) orient {}'.format(i, rect.left, rect.top, rect.right, rect.bottom, rect.orient))

    # release Engine
    AFD_FSDK_UninitialFaceEngine(hFDEngine)

    CLibrary.free(pFDWorkMem)

    print(u'#####################################################')
