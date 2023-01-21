import sys
import pygame
import music21 as ms21
import numpy as np
import cv2
import os
sys.setrecursionlimit(1000000)

#path = os.path.dirname(__file__)
#path = os.path.dirname(os.path.abspath(__file__))
#path = os.path.dirname(os.path.realpath(sys.executable))
path = os.path.dirname(os.path.realpath(sys.argv[0]))
print(path)
pitchs = []
durations = []

music_path = os.path.join(path,'music/')
#fileList = "{}/music/".format(path)
fileList = os.listdir(music_path)
#fileList = os.listdir(path+'/music')
def get_file_choice():
	mxlList = []
	for f in fileList:
		if(".mxl" in f ):
			mxlList.append(f)
	print("\nType the number of a mxl file press enter:\n")
	for i in range(len(mxlList)):
		print(i+1,":",mxlList[i])

	choice = int(input(">"))
	print()
	choice_index = int(choice)
	return mxlList[choice_index-1]

# 解析速度
mxl_file = get_file_choice()
music = os.path.join(music_path, mxl_file)
#file = "{}/music/".format(path) + mxl_file
filename = mxl_file[:-4]
s=ms21.converter.parse(music)
sFlat = s.flatten()
# 获取tempo
bpm = sFlat.metronomeMarkBoundaries()[0][2].number
#bpm change
# bpm = 40
print("tempo: " + str(bpm) + "bpm")
choose = input("The current tempo is "+str(bpm)+"bpm, do you want to change the tempo? Y/N  ")
if(choose == 'Y' or choose == 'y'):
    bpm = int(input("Please enter your expected tempo (must be an interger)  "))
    print("the curren bpm={}".format(bpm))
print("\n Notice:Click the button'X' in the upper right corner to close the window \n Waiting...playSong is ready to run \n ")
# input("\n\nNotice:Click the button'X' in the upper right corner to close the window \n [Press any key to continue...]")

# 解析乐谱获取音高和持续时间
second = 60 / bpm # 换算
for note in s.flat.notesAndRests:
    # 休止符Rest
    if isinstance(note, ms21.note.Rest):
        pitchs.append('r') 
        durations.append(round(note.duration.quarterLength*second,3))
    # 音符Note
    elif isinstance(note,ms21.note.Note):
        pitchs.append(note.pitch.nameWithOctave)
        durations.append(round(note.duration.quarterLength*second,3))

# 背景图处理
bg_path = os.path.join(path,'background/spring.jpg')
background = cv2.imread(bg_path)
#background = cv2.imread("{}/background/spring.jpg".format(path))
# 背景为jpg格式，为与指法图的png图像融合，为其增加Alpha通道
b_channel, g_channel, r_channel = cv2.split(background)
# 创建Alpha通道
alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255 
# 融合通道
bg_new = cv2.merge((b_channel, g_channel, r_channel, alpha_channel)) 
# 修改尺寸
bg_new = cv2.resize(bg_new,(900,500))
bg_x = bg_new.shape[1]
bg_y = bg_new.shape[0]
# print("背景处理成功")
# 生成指法图
for i in pitchs:
    # 指法图与背景图融合
	# 保留path的/
    img_path = os.path.join(path,'fingering_chart/',"{}.png".format(i))
	#img_path = os.path.join('fingering_chart/',"{}.png".format(i))
    #img_path = "{}{}".format(abspath,img_path)
    # print(img_path)
    # cv2不需要读入绝对路径，但是os.path.join需要
    img = cv2.imread(img_path,cv2.IMREAD_UNCHANGED)
    #img = cv2.imread("{}/fingering_chart/".format(path)+i+'.png',cv2.IMREAD_UNCHANGED)
    # 叠加每张png到jpg上
    png_x = img.shape[1]
    png_y = img.shape[0]
    # (x1,y1),(x2,y2)为待叠加位置的对角线
    x1 = int(0 + (bg_x - png_x) / 2)
    y1 = int(0 + (bg_y - png_y) / 2)
    x2 = x1 + png_x
    y2 = y1 + png_y
    
    # 浅拷贝。直接赋值bg_new2 = bg_new会使得初始背景图也被修改
    bg_new2 = bg_new.copy()
    
    # 获取要覆盖图像的alpha值，将像素值除以255，使值保持在0-1之间
    alpha_png = img[:,:,3] / 255.0
    alpha_jpg = 1 - alpha_png
    for c in range(0,3):
        bg_new2[y1:y2,x1:x2,c] = ((alpha_jpg*bg_new[y1:y2,x1:x2,c]) + (alpha_png*img[0:png_y,0:png_x,c]))
    # jpg格式是三通道，只取前三个通道，方便视频生成
    bg_new3 = bg_new2[:,:,0:3] # 左闭右开！
    
    # 存储
    success, encoded_image = cv2.imencode(".jpg", bg_new3)
    bg_bytes = encoded_image.tostring()
    string = os.path.join(path,'fingering/',filename)
    #string ="{}/fingering/".format(path)+filename
    if not os.path.isdir(string):
        os.mkdir(string)
    fingering = os.path.join('fingering/',filename,"{}.jpg".format(i))
    #fingering = "{}/fingering/".format(path)+filename+'/'+i+'.jpg'
    with open(fingering, 'wb') as finger:
        finger.write(bg_bytes)

# 初始化
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode([bg_x, bg_y])
#icon_path = os.path.join(path,'icon.png')
#icon = pygame.image.load(path+'/icon.png').convert_alpha()
icon = pygame.image.load('icon.png').convert_alpha()
pygame.display.set_icon(icon)
pygame.display.set_caption('竖笛音乐盒')
pygame.time.delay(1000)

# 播放指法图和音频
j = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if pygame.mixer.music.get_busy() == False:
            # 读取指法和音频
            for i in pitchs:
                # 单击右上角X关闭窗口
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                fingering = os.path.join(path,"fingering/{}/".format(filename),"{}.jpg".format(i))
                #print(fingering)
                #fingering = "{}/fingering/".format(path)+filename+'/'+i+'.jpg'
                bg_path = pygame.image.load(fingering)
                music_path = os.path.join(path,"mp3_recorder/","{}.mp3".format(i))
                #music_path = "{}/mp3_recorder/".format(path)+i+".mp3"
                print("playing "+i)
                screen.blit(bg_path, (0, 0))
                pygame.display.update()
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play() 
                duration = int(durations[j] * 1000) 
                pygame.time.delay(duration) # 持续相应时长
                j+=1
            pygame.time.delay(1000)
        pygame.quit()


