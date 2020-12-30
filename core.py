# -*- coding: utf-8 -*-

from PIL import ImageFont, ImageDraw, Image
import cv2
import qrcode

import os
import uuid
import shutil

CUR_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.abspath(os.path.dirname(CUR_PATH) + os.path.sep + ".")
WORK_DIR = os.path.join(ROOT_DIR, "workspace")
RESOURCE_DIR = os.path.join(ROOT_DIR, "resource")


def generate_qrcode(url, qrpath="test.png"):
    '''生成二维码'''
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    with open(qrpath, 'wb') as f:
        img.save(f)


def generate_background_img(width, height, path, qrpath):
    ''' 生成底图 二维码 & 文字 '''
    qrtmppath = os.path.join(WORK_DIR, "{}.png".format(str(uuid.uuid4())))
    newImg = Image.new('RGB',(width, height),'black')
    markImg = Image.open(qrpath)
    w, h = markImg.size
    out = markImg.resize((15 * height / 64, (15 * height / 64) * (h / w)), Image.ANTIALIAS)
    out.save(qrtmppath)
    outImg = Image.open(qrtmppath)
    n_w, n_h = outImg.size
    W, H = newImg.size
    newImg.paste(outImg, ((W-n_w)/2, 178 * height / 640))
    newImg.save(path)
    if os.path.exists(qrtmppath):
        os.remove(qrtmppath)

    img = Image.open(path)
    W, H = img.size
    font_size = 18 * H / 640
    font = ImageFont.truetype(os.path.join(RESOURCE_DIR, 'font', 'PingFangSC-Semibold.otf'), font_size, encoding="unic")
    draw = ImageDraw.Draw(img)
    draw.text(((W-font_size*8.3)/2, H * 136 / 640),  u"微信扫一扫 有惊喜", font = font, fill = (255, 255, 255))
    font_size = 16 * H / 640
    font = ImageFont.truetype(os.path.join(RESOURCE_DIR, 'font', 'PingFangRegular.otf'), font_size, encoding="unic")
    draw.text(((W-font_size*9)/2, 364 * H / 640),  u"这里是一个文案1", font = font, fill = (119, 136, 153))
    draw.text(((W-font_size*12)/2, 364 * H / 640 + font_size * 1.2),  u"这里是另一个文案吧应该", font = font, fill = (119, 136, 153))
    img.save(path)


def pasteButtom(src_path, logo_path, out_path):
    ''' 添加底部logo '''
    logo_resize_path = os.path.join(WORK_DIR, str(uuid.uuid4()) + "_logo_resize.png")
    img = Image.open(src_path)
    markImg = Image.open(logo_path)
    markImg.convert('RGB')
    w, h = markImg.size
    W, H = img.size

    new_h = 10 * H / 64
    new_w = new_h * w / h
    print new_w, new_h
    out = markImg.resize((int(new_w), int(new_h)), Image.ANTIALIAS)
    out.save(logo_resize_path)
    outImg = Image.open(logo_resize_path)
    n_w, n_h = outImg.size
    img.paste(outImg, ((W-n_w)/2, 500 * H / 640))
    img.save(out_path)
    if os.path.exists(logo_resize_path):
        os.remove(logo_resize_path)


def generate_images(base_img_path, dstdirpath):
    """ 生成所有视频 """
    for i in range(140):
        if i == 0:
            continue
        img = "/foot_images/image-%05d.jpeg" % i
        pasteImg = RESOURCE_DIR + img
        pasteButtom(base_img_path, pasteImg, dstdirpath + '/after_{}.png'.format(str(i)))
    return


def pic2video(path, file_path):
    img = Image.open(path + "/after_{}.png".format(str(1)))
    size = img.size
    '''
    fps:
    帧率：1秒钟有n张图片写进去[控制一张图片停留5秒钟，那就是帧率为1，重复播放这张图片5次]
    '''
    fps = 25
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    video = cv2.VideoWriter(file_path, fourcc, fps, size)
    for i in range(140):
        if i == 0:
            continue
        item = path + "/after_{}.png".format(str(i))
        img = cv2.imread(item)  #使用opencv读取图像，直接返回numpy.ndarray 对象，通道顺序为BGR ，注意是BGR，通道值默认范围0-255。
        video.write(img)        #把图片写进视频
    video.release() #释放


def add_audio(video_path, audio_path, out_path):
    cmd = "ffmpeg -i {} -i {} -f mp4 -y {}".format(video_path, audio_path, out_path)
    os.system(cmd)



def generate_tail_video(key, width, height):
    """ 生成尾部视频 """
    work_dir = os.path.join(WORK_DIR, "{}_{}_{}".format(str(key), width, height))
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)

    # step1: 生成二维码
    url = "http://diaohaha.github.io?reqkey={}".format(str(key))
    qrcode_path = os.path.join(work_dir, "qrcode.png")
    generate_qrcode(url, qrcode_path)

    # step2: 生成底图 (粘贴二维码, 文字)
    background_img_path = os.path.join(work_dir, "{}_background.png".format(str(uuid.uuid4())))
    generate_background_img(width, height, background_img_path, qrcode_path)

    # step3: 底部动态图合并生成视频帧
    dst_dir_path = os.path.join(work_dir, str(uuid.uuid4()))
    os.mkdir(dst_dir_path)
    generate_images(background_img_path, dst_dir_path)

    # step4: 生成尾版视频 & 添加音频
    video_tmp_path = os.path.join(work_dir, "{}.mp4".format(str(uuid.uuid4())))
    pic2video(dst_dir_path, video_tmp_path)
    video_path = os.path.join(WORK_DIR, "{}.mp4".format(str(uuid.uuid4())))
    audio_resource_path = os.path.join(RESOURCE_DIR, "background.aac")
    add_audio(video_tmp_path, audio_resource_path, video_path)

    # if os.path.exists(work_dir):
    #     shutil.rmtree(work_dir)
    return video_path





if __name__ == "__main__":
    generate_tail_video(123, 1080, 1920)

