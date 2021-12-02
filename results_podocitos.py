# -*- coding: utf-8 -*-
"""results_podocitos.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QDJ-eubMN-vNxWztZbCGNjcXiCUHMpOU

#Utils
"""

from google.colab import drive
drive.mount('/content/gdrive')

# Commented out IPython magic to ensure Python compatibility.
#@title Rodar célula
import cv2
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
from IPython.display import Image, display
import random
import seaborn as sns
import shutil


LABEL_DIR = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test/labels/"
DETECTION_SRC = '/content/yolov5/runs/detect/'
CONFIGS_LIST =["sr", "mr", "lr", "xr",
               "swr", "mwr", "lwr", "xwr",
               "sdr", "mdr", "ldr", "xdr",
               "swdr", "mwdr", "lwdr", "xwdr",
               ]
PATH_CVAL = "/content/gdrive/MyDrive/Podocitos/CVal/"


def draw_annotation(img_path, label_path):
  img = cv2.imread(img_path)
  dh, dw, _ = img.shape

  fl = open(label_path, 'r')
  data = fl.readlines()
  fl.close()

  for dt in data:

      # Split string to float
      _, x, y, w, h = map(float, dt.split(' '))

      # Taken from https://github.com/pjreddie/darknet/blob/810d7f797bdb2f021dbe65d2524c2ff6b8ab5c8b/src/image.c#L283-L291
      # via https://stackoverflow.com/questions/44544471/how-to-get-the-coordinates-of-the-bounding-box-in-yolo-object-detection#comment102178409_44592380
      l = int((x - w / 2) * dw)
      r = int((x + w / 2) * dw)
      t = int((y - h / 2) * dh)
      b = int((y + h / 2) * dh)
      
      if l < 0:
          l = 0
      if r > dw - 1:
          r = dw - 1
      if t < 0:
          t = 0
      if b > dh - 1:
          b = dh - 1

      cv2.rectangle(img, (l, t), (r, b), (0, 100, 0), 1)
  
  img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
  return img


def cria_df(PATH):
  
  if PATH[-3:] == 'txt':
    data = pd.read_csv(PATH, delimiter=r"\s+", header=None)
    
    data.columns = ["Epoch", "MEM", "box", "obj", 
                    "cls", "tot", "targets", "img_sz",
                    "P", "R", "mAP", "mAP2", "vbox", 
                    "vobj", "val_C"]
    
    data = data.drop(['Epoch', 'MEM', 'cls', 'tot', 'targets', 
                      'img_sz','val_C'], axis=1)  
  
  elif PATH[-3:] == 'csv':
    data = pd.read_csv(PATH)
    data = data.drop(['               epoch', 
                  '      train/cls_loss',
                  '        val/cls_loss'], axis=1)

    data.rename(columns={'      train/box_loss' : 'box',
                        '      train/obj_loss' : 'obj',
                        '   metrics/precision' : 'P', 
                        '      metrics/recall' : 'R',
                        '     metrics/mAP_0.5' : 'mAP', 
                        'metrics/mAP_0.5:0.95' :'mAP2',
                        '        val/box_loss' :'vbox',
                        '        val/obj_loss' :'vobj'
                        }, inplace=True)
  
  data["F1"] = 2*data["P"]*data["R"]/(data["P"] + data["R"])
  data["Fit"] = 0.9*data["mAP2"] + 0.1*data["mAP"]
  return data


def cria_df_splits(v1, v2):
  data = pd.DataFrame()

  for i in range(5):
    src = PATH_CVAL + v1 + v2 + str(i+1) + '/results.txt'
    if not os.path.exists(src):
      src = src[:-3] + 'csv'

    try:
      split = cria_df(src)
    except:
      continue
    
    try:
      idx=split["Fit"].idxmax()
      series = pd.Series(split.iloc[idx, :].values, index=split.columns)
    except:
      print("Error in split" + str(i+1) + " of version " + v1 + v2)
      continue
    data = data.append(series, ignore_index=True)
  return data


def plot_loss(df, ylim=False):
  fig = plt.figure(figsize=(21,9)) 
  train_loss = df['box'] + df['obj']
  test_loss = df['vbox'] + df['vobj']
  plt.plot(train_loss, marker='o', markersize=5)
  plt.plot(test_loss, marker='o', markersize=5)
  fig.suptitle('Curva de Loss', fontsize=30)
  if ylim:
    top = 1.2*max(train_loss.max(), test_loss.max())
    plt.ylim(top=top)
  plt.grid(axis='y', ls='--')
  plt.xlabel('Época', fontsize=20)
  plt.ylabel('Loss', fontsize=20)
  plt.legend(["Treino", 
              "Teste"],
              fontsize=20,
              loc = 1)
  plt.show()


def plot_map(df1, df2, legends, ylim=False):
  fig = plt.figure(figsize=(21,9)) 
  df1["mAP"].plot(marker='o', markersize=5)
  df2["mAP"].plot(marker='o', markersize=5)
  fig.suptitle('Curva de AP', fontsize=30)
  if ylim:
    ylim=df1["mAP"].max()*1.2
    plt.ylim(top=ylim)
  plt.grid(axis='y', ls='--')
  plt.xlabel('Época', fontsize=20)
  plt.ylabel('AP', fontsize=20)
  plt.legend([legends[0], 
              legends[1]],
              fontsize=20,
              loc = 1)
  plt.show()


def plot_side_by_side(PATH, title):

  NUM_ROWS = 1
  IMGs_IN_ROW = 2
  f, ax = plt.subplots(NUM_ROWS, IMGs_IN_ROW, figsize=(16,8))

  img1 = plt.imread(PATH + "/F1_curve.png")
  img2 = plt.imread(PATH + "/PR_curve.png")

  ax[0].imshow(img1)
  ax[1].imshow(img2)

  ax[0].set_title('F1 x Confiança', fontsize=20)
  ax[1].set_title('Precisão x Recall', fontsize=20)
  ax[0].axis('off')
  ax[1].axis('off')

  f.suptitle(title, fontsize=30)
  f.subplots_adjust(wspace=0)
  plt.tight_layout()
  plt.show()


def show_results(isDataAug=True):
  src = "/content/gdrive/MyDrive/Podocitos/Retreino/"

  if not isDataAug:
    configs_dict = {
      "sr": "Versão S sem pré-treino",
      "mr": "Versão M sem pré-treino",
      "lr": "Versão L sem pré-treino",
      "xr": "Versão X sem pré-treino",
      "swr": "Versão S com pré-treino",
      "mwr": "Versão M com pré-treino",
      "lwr": "Versão L com pré-treino",
      "xwr": "Versão X com pré-treino"
    }
  else:
    configs_dict = {
      "sdr": "Versão S sem pré-treino",
      "mdr": "Versão M sem pré-treino",
      "ldr": "Versão L sem pré-treino",
      "xdr": "Versão X sem pré-treino",
      "swdr": "Versão S com pré-treino",
      "mwdr": "Versão M com pré-treino",
      "lwdr": "Versão L com pré-treino",
      "xwdr": "Versão X com pré-treino"
    }
      
  for key in configs_dict.keys():
    plot_side_by_side(src + "v5" + key, configs_dict[key])
    print("\n")


def compare_detections(target, title):
  img_list = []

  for version in target:
    for imageName in glob.glob(DETECTION_SRC + version + '/*.jpg'): #assuming JPG
        #finds labelname corresponding to image
        filename = imageName.split("/")[-1].split(".jpg")[0]
        label_path = LABEL_DIR + filename + ".txt"
        img_list.append(draw_annotation(imageName, label_path))
        #display(Image(filename=imageName))

  NUM_ROWS = 2
  IMGs_IN_ROW = 2
  f, ax = plt.subplots(NUM_ROWS, IMGs_IN_ROW)

  ax[0][0].imshow(img_list[0])
  ax[0][1].imshow(img_list[1])
  ax[1][0].imshow(img_list[2])
  ax[1][1].imshow(img_list[3])

  ax[0][0].set_title('YOLOv5 S', fontsize=20)
  ax[0][1].set_title('YOLOv5 M', fontsize=20)
  ax[1][0].set_title('YOLOv5 L', fontsize=20)
  ax[1][1].set_title('YOLOv5 X', fontsize=20)

  for row in ax:
    for im in row:
      im.set_xticks([])
      im.set_yticks([])

  f.set_figheight(16)
  f.set_figwidth(16)
  f.suptitle(title, fontsize=30)
  plt.tight_layout(rect=[0, 0, 0.92, 0.95])
  f.subplots_adjust(wspace=0)
  plt.show()


def compara_redes(detections, title, set_title=False):
  img_list=[]

  for detection in detections:
    if os.path.isfile(detection):
      imageName=detection
    else:
      imageName = glob.glob(detection + '/*.jpg')[0] #assuming JPG
      #finds labelname corresponding to image
    filename = imageName.split("/")[-1].split(".jpg")[0]
    label_path = LABEL_DIR + filename + ".txt"
    img_list.append(draw_annotation(imageName, label_path))
    #display(Image(filename=imageName))

  NUM_ROWS = 1
  IMGs_IN_ROW = 2
  f, ax = plt.subplots(NUM_ROWS, IMGs_IN_ROW, figsize=(16, 8))

  ax[0].imshow(img_list[0])
  ax[1].imshow(img_list[1])

  if set_title:
    ax[0].set_title(set_title[0], fontsize=20)
    ax[1].set_title(set_title[1], fontsize=20)

  for im in ax:
    im.set_xticks([])
    im.set_yticks([])

  f.suptitle(title, fontsize=30)
  f.subplots_adjust(wspace=0)
  plt.show()


def best_worst(vs_names):
  for vs_name in vs_names:
    if os.path.exists("map.txt"):
      os.remove("map.txt")
      
    if os.path.exists("test_images"):
      shutil.rmtree("test_images")
    
    !touch map.txt
    src = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test"
    weight_path = "/content/gdrive/MyDrive/Podocitos/Retreino/" + vs_name + "/weights/best.pt"
    if not os.path.exists(weight_path):
      print("Error. File 'best.pt' not found in .../", weight_path.split('Retreino/')[1])
      continue


    if not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/worst_detections"):
      os.mkdir("/content/gdrive/MyDrive/Podocitos/tmp/worst_detections")

    if not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/best_detections"):
      os.mkdir("/content/gdrive/MyDrive/Podocitos/tmp/best_detections")

    if (not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/best_detections/" + vs_name+".jpg") 
    or not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/worst_detections/" + vs_name+".jpg")):
      
      for image in sorted(os.listdir(src + "/images")):
        os.mkdir("test_images")
        os.mkdir("test_images/images")
        os.mkdir("test_images/labels")
        filename = image.split("/")[-1].split(".jpg")[0]
        imagename = src + "/images/" + filename + ".jpg"
        labelname = src + "/labels/" + filename + ".txt"

        shutil.copy(imagename, "test_images/images")
        shutil.copy(labelname, "test_images/labels")
        !python test.py --weights $weight_path --data /content/data.yaml --img 416 
#         %rm -rf test_images

      f = open("map.txt", "r")
      results = [float(x.strip()) for x in f] 
      max_idx = results.index(max(results))
      min_idx = results.index(min(results))
      test_images = sorted(os.listdir(src + "/images"))
      best_img = src + "/images/" + test_images[max_idx]
      worst_img = src + "/images/" + test_images[min_idx]
      f.close()

      if not os.path.exists("best_maps.txt"):
        !touch best_maps.txt
      
      f=open("best_maps.txt", "a")
      f.write(str(vs_name)+ ": " + "(" + str(max_idx) + "," + str(max(results)) + ")\n")
      f.close()

      version = [vs_name+"b", vs_name+"w"]
      img_list=[]
      name_best = version[0]
      name_worst = version[1]   

      if not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/best_detections/" + vs_name +".jpg"):
        !python detect.py --weights $weight_path --img 416 --source $best_img --name $name_best
      else:
        print("Configuration ", name_best, " already stored")
      
      if not os.path.exists("/content/gdrive/MyDrive/Podocitos/tmp/worst_detections/" + vs_name+".jpg"):
        !python detect.py --weights $weight_path --img 416 --source $worst_img --name $name_worst
      else:
        print("Configuration ", name_worst, " already stored") 
        continue

      LABEL_DIR = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test/labels/"
      for v in version:
        for imageName in glob.glob('/content/yolov5/runs/detect/' + v + '/*.jpg'): #assuming JPG
          #finds labelname corresponding to image
          filename = imageName.split("/")[-1].split(".jpg")[0]
          label_path = LABEL_DIR + filename + ".txt"
          img_list.append(draw_annotation(imageName, label_path))
          #display(Image(filename=imageName))

      cv2.imwrite("/content/gdrive/MyDrive/Podocitos/tmp/best_detections/" + vs_name + ".jpg", img_list[0])
      cv2.imwrite("/content/gdrive/MyDrive/Podocitos/tmp/worst_detections/" + vs_name + ".jpg", img_list[1])
    
    else:
      print("Configurations ", vs_name, " already stored")

"""#Estatísticas da Validação Cruzada



"""

#@title Cria df com resultados dos splits
df_s = cria_df_splits("v5s", "") 
df_m = cria_df_splits("v5m", "")
df_l = cria_df_splits("v5l", "")
df_x = cria_df_splits("v5x", "")
df_sw = cria_df_splits("v5s", "w") 
df_mw = cria_df_splits("v5m", "w")
df_lw = cria_df_splits("v5l", "w")
df_xw = cria_df_splits("v5x", "w")
df_sd = cria_df_splits("v5s", "d") 
df_md = cria_df_splits("v5m", "d")
df_ld = cria_df_splits("v5l", "d")
df_xd = cria_df_splits("v5x", "d")
df_swd = cria_df_splits("v5s", "wd") 
df_mwd = cria_df_splits("v5m", "wd")
df_lwd = cria_df_splits("v5l", "wd")
df_xwd = cria_df_splits("v5x", "wd")

"""##Gráficos de Dispersão

###Stripplot
"""

plt.figure(figsize=(8,6))
ax = sns.stripplot(data=[df_s["mAP"], df_m["mAP"], df_l["mAP"], df_x["mAP"]], size=8, jitter=0)
ax.set_xticklabels(["S", "M", "L", "X"])
ax.set_ylabel("AP", fontsize=12)
ax.set_xlabel("Arquitetura", fontsize=12)
ax.set_title("Resultados da validação cruzada", fontsize=18)
plt.show()

plt.figure(figsize=(8,6))
ax = sns.stripplot(data=[df_sw["mAP"], df_mw["mAP"], df_lw["mAP"], df_xw["mAP"]], size=8, jitter=0)
ax.set_xticklabels(["S", "M", "L", "X"])
ax.set_ylabel("AP", fontsize=12)
ax.set_xlabel("Arquitetura", fontsize=12)
ax.set_title("Resultados da validação cruzada", fontsize=18)
plt.show()

plt.figure(figsize=(8,6))
ax = sns.stripplot(data=[df_sd["mAP"], df_md["mAP"], df_ld["mAP"], df_xd["mAP"]], size=8, jitter=0)
ax.set_xticklabels(["S", "M", "L", "X"])
ax.set_ylabel("AP", fontsize=12)
ax.set_xlabel("Arquitetura", fontsize=12)
ax.set_title("Resultados da validação cruzada", fontsize=18)
plt.show()

plt.figure(figsize=(8,6))
ax = sns.stripplot(data=[df_swd["mAP"], df_mwd["mAP"], df_lwd["mAP"], df_xwd["mAP"]], size=8, jitter=0)
ax.set_xticklabels(["S", "M", "L", "X"])
ax.set_ylabel("AP", fontsize=12)
ax.set_xlabel("Arquitetura", fontsize=12)
ax.set_title("Resultados da validação cruzada", fontsize=18)
plt.show()

"""###Catplot"""

tips = sns.load_dataset("tips")
tips

import numpy as np
from matplotlib import rcParams

# figure size in inches
plt.rcParams["axes.labelsize"] = 20
plt.rcParams["xtick.labelsize"] = 15
plt.rcParams["ytick.labelsize"] = 15
plt.rcParams["legend.fontsize"] = 15
plt.rcParams["legend.title_fontsize"] = 15
plt.rcParams["figure.facecolor"] = 'lightgrey'

splits_mAP = pd.concat([df_s["mAP"], df_m["mAP"], df_l["mAP"], df_x["mAP"],
                        df_sw["mAP"], df_mw["mAP"], df_lw["mAP"], df_xw["mAP"]])
name = [["YOLOV5S"]*5, ["YOLOV5M"] * 5, ["YOLOV5L"] * 5, ["YOLOV5X"] * 5] * 2
name = np.reshape(name,len(name) * 5)
version = np.reshape([["Sem Pré-Treino"]*20, ["Com Pré-Treino"]*20], 40)

cross_val_splits = pd.DataFrame(data = {'AP': splits_mAP,
                          'Arquitetura':name,
                          'Grupo':version})


rp = sns.catplot(x="Arquitetura", y="AP", hue="Grupo", data=cross_val_splits, jitter=0, height=6, aspect=1.5, s=10)
rp.fig.subplots_adjust(top=0.9) # adjust the Figure in rp
rp.fig.suptitle('Resultados de Validação Cruzada', fontsize=30)

plt.show()

import numpy as np
from matplotlib import rcParams

# figure size in inches
plt.rcParams["axes.labelsize"] = 20
plt.rcParams["xtick.labelsize"] = 15
plt.rcParams["ytick.labelsize"] = 15
plt.rcParams["legend.fontsize"] = 15
plt.rcParams["legend.title_fontsize"] = 15
plt.rcParams["figure.facecolor"] = 'lightgrey'

splits_mAP = pd.concat([df_sd["mAP"], df_md["mAP"], df_ld["mAP"], df_xd["mAP"],
                        df_swd["mAP"], df_mwd["mAP"], df_lwd["mAP"], df_xwd["mAP"]])
name = [["YOLOV5S"]*5, ["YOLOV5M"] * 5, ["YOLOV5L"] * 5, ["YOLOV5X"] * 5] * 2
name = np.reshape(name,len(name) * 5)
version = np.reshape([["Sem Pré-Treino"]*20, ["Com Pré-Treino"]*20], 40)

cross_val_splits = pd.DataFrame(data = {'AP': splits_mAP,
                          'Arquitetura':name,
                          'Grupo':version})


rp = sns.catplot(x="Arquitetura", y="AP", hue="Grupo", data=cross_val_splits, height=6, aspect=1.5, s=10)
rp.fig.subplots_adjust(top=0.9) # adjust the Figure in rp
rp.fig.suptitle('Resultados de Validação Cruzada', fontsize=30)

plt.show()

"""##Tabela de Médias"""

splits =[df_s, df_m, df_l, df_x,
         df_sw, df_mw, df_lw, df_xw,
         df_sd, df_md, df_ld, df_xd,
         df_swd, df_mwd, df_lwd, df_xwd]


splits_mean = pd.DataFrame()
for split in splits:
  splits_mean = splits_mean.append(split.mean(), ignore_index=True)

print(splits_mean[["P", "R", "mAP", "F1", "Fit"]].to_string(index=False))
print(splits_mean["mAP"][0:8].idxmax(), splits_mean["mAP"][8:16].idxmax())

print(df_sw["mAP"].idxmin(), df_mw["mAP"].idxmin(), df_lw["mAP"].idxmin(), df_xw["mAP"].idxmin())

min = df_xwd["mAP"].min()
y=[x for x in df_xd["mAP"] if x>min]
len(y)

print(splits_mean["mAP"][10], splits_mean["mAP"][14])

"""#Avaliação Final

##Tabela com métricas
"""

df_final = pd.DataFrame()
indexes = []

for config in CONFIGS_LIST:
  try:
    results_path = '/content/gdrive/MyDrive/Podocitos/Retreino/v5' + config + '/results.txt'
    if not os.path.exists(results_path):
      results_path = results_path[:-3] + 'csv'
    aux = cria_df(results_path)
    
  except:
    print(config)
    continue
  idx = aux["Fit"].idxmax()
  indexes.append(idx)
  series = pd.Series(aux.iloc[idx, :].values, index=aux.columns)
  df_final = df_final.append(series, ignore_index=True)

axis = [
        "YOLOV5S SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5M SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5L SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5X SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5S COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5M COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5L COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5X COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5S SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5M SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5L SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5X SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5S COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5M COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5L COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5X COM PRÉ-TREINO - AUMENTADO"
]

df_final["Index"] = indexes
print(df_final[["P", "R", "mAP", "F1", "Index","Fit"]].to_string(index=False))
# print(df_final[["P", "R", "F1", "mAP"]].set_axis(axis))

"""##Loss, mAP e gráficos diversos"""

df_list = []

for config in CONFIGS_LIST:
  try:
    results_path = '/content/gdrive/MyDrive/Podocitos/Retreino/v5' + config + '/results.txt'
    if not os.path.exists(results_path):
      results_path = results_path[:-3] + 'csv'
    aux = cria_df(results_path)
    df_list.append(aux)
  except:
    continue

"""###Cenário 1

####Loss
"""

idx1_min = df_final["Fit"][0:8].idxmin()
idx1_max = df_final["Fit"][0:8].idxmax()
train_loss = df_list[idx1_max]["box"] + df_list[idx1_max]["obj"]
test_loss = df_list[idx1_max]["vbox"] + df_list[idx1_max]["vobj"]
loss_sub = train_loss - test_loss
print('Loss teste maior que treino: ', loss_sub[loss_sub<0], '\n')
print('Menor diferença absoluta ', loss_sub[loss_sub>0].min(), ' na época', loss_sub[loss_sub>0].idxmin())
print('Ponto de mínimo de treino: ', train_loss.idxmin(), ' Ponto de mínimo de teste: ', test_loss.idxmin())

train_loss = df_list[idx1_min]["box"] + df_list[idx1_min]["obj"]
test_loss = df_list[idx1_min]["vbox"] + df_list[idx1_min]["vobj"]
loss_sub = train_loss - test_loss
print('Loss teste maior que treino: ', loss_sub[loss_sub<0])
print('Menor diferença absoluta ', loss_sub[loss_sub>0].min(), ' na época', loss_sub[loss_sub>0].idxmin())
print('Ponto de mínimo de treino: ', train_loss.idxmin(), ' Ponto de mínimo de teste: ', test_loss.idxmin())

plot_loss(df_list[idx1_max])

plot_loss(df_list[idx1_min])

"""####Curva de mAP"""

print('Índice Máximo: ',(idx1_max, CONFIGS_LIST[idx1_max]), '\nÍndice Mínimo: ', (idx1_min, CONFIGS_LIST[idx1_min]))

print(df_list[idx1_max]["mAP"].max(), df_list[idx1_max]["mAP"].idxmax())

print(df_list[idx1_min]["mAP"].max(), df_list[idx1_min]["mAP"].idxmax())

import numpy as np

melhor_pior_map = df_list[idx1_max]["mAP"]/(df_list[idx1_min]["mAP"])
melhor_pior_map.replace([np.inf, -np.inf], np.nan, inplace=True)
(melhor_pior_map.max(), melhor_pior_map.idxmax())

plot_map(df_list[idx1_max], df_list[idx1_min], ylim=True,
         legends=["YOLOv5M pré-treinada", "YOLOv5S sem pré-treino"])

"""####Gráficos"""

show_results(isDataAug=False)

"""###Cenário 2

####Loss
"""

idx2_min = df_final["Fit"][8:16].idxmin()
idx2_max = df_final["Fit"][8:16].idxmax()
train_loss = df_list[idx2_max]["box"] + df_list[idx2_max]["obj"]
test_loss = df_list[idx2_max]["vbox"] + df_list[idx2_max]["vobj"]
loss_sub = train_loss - test_loss
print('Loss teste maior que treino: ', loss_sub[loss_sub<0].count(), '\n')
print('Menor diferença absoluta ', loss_sub[loss_sub>0].min(), ' na época', loss_sub[loss_sub>0].idxmin())
print('Ponto de mínimo de treino: ', train_loss.idxmin(), ' Ponto de mínimo de teste: ', test_loss.idxmin())

train_loss = df_list[idx2_min]["box"] + df_list[idx2_min]["obj"]
test_loss = df_list[idx2_min]["vbox"] + df_list[idx2_min]["vobj"]
loss_sub = train_loss - test_loss
print('Loss teste maior que treino: ', loss_sub[loss_sub<0].count())
print('Menor diferença absoluta ', loss_sub[loss_sub>0].min(), ' na época', loss_sub[loss_sub>0].idxmin())
print('Ponto de mínimo de treino: ', train_loss.idxmin(), ' Ponto de mínimo de teste: ', test_loss.idxmin())

plot_loss(df_list[idx2_max], ylim=True)

plot_loss(df_list[idx2_min], ylim=True)

"""####Curva de mAP"""

print('Índice Máximo: ',(idx2_max, CONFIGS_LIST[idx2_max]), '\nÍndice Mínimo: ', (idx2_min, CONFIGS_LIST[idx2_min]))

print(df_list[idx2_max]["mAP"].max(), df_list[idx2_max]["mAP"].idxmax())

print(df_list[idx2_min]["mAP"].max(), df_list[idx2_min]["mAP"].idxmax())

import numpy as np

melhor_pior_map = df_list[idx2_max]["mAP"]/(df_list[idx2_min]["mAP"])
melhor_pior_map.replace([np.inf, -np.inf], np.nan, inplace=True)
(melhor_pior_map.max(), melhor_pior_map.idxmax())

plot_map(df_list[idx2_max], df_list[idx2_min], ylim=True,
         legends=["YOLOv5L pré-treinada", "YOLOv5S pré-treinada"])

"""####Gráficos"""

show_results(isDataAug=True)

"""#Comparação entre as marcações da rede e as anotações

##Preparações iniciais
"""

# Commented out IPython magic to ensure Python compatibility.
# clone YOLOv5 repository
# %%capture
!git clone https://github.com/ultralytics/yolov5  # clone repo
# %cd yolov5
!git reset --hard 886f1c03d839575afecb059accf74296fad395b6

# install dependencies as necessary
!pip install -qr requirements.txt  # install dependencies (ignore errors)
import torch

from IPython.display import Image, clear_output  # to display images
from utils.google_utils import gdrive_download  # to download models/datasets

# clear_output()
print('Setup complete. Using torch %s %s' % (torch.__version__, torch.cuda.get_device_properties(0) if torch.cuda.is_available() else 'CPU'))

from IPython.core.magic import register_line_cell_magic

@register_line_cell_magic
def writetemplate(line, cell):
    with open(line, 'w') as f:
        f.write(cell.format(**globals()))

# Commented out IPython magic to ensure Python compatibility.
# %%writetemplate /content/data.yaml
# 
# val: /content/yolov5/test_images
# 
# nc: 1
# names: ['1']

# Commented out IPython magic to ensure Python compatibility.
# %cp /content/gdrive/MyDrive/test.py /content/yolov5
# %cp /content/gdrive/MyDrive/detect.py /content/yolov5

# Commented out IPython magic to ensure Python compatibility.
# %cd
# %cd /content/yolov5
# %rm -rf test_images

"""##Grid de Imagens"""

# Commented out IPython magic to ensure Python compatibility.
# %rm -rf /content/yolov5/runs

# Commented out IPython magic to ensure Python compatibility.
weights_src = "/content/gdrive/MyDrive/Podocitos/Retreino/"
path_to_files = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test/images"
file_path = os.path.join(path_to_files, random.choice(os.listdir(path_to_files)))


for dir in os.listdir(weights_src):
  config = dir.split("v5")[1]
  weight_path = weights_src + dir + "/weights/best.pt"
  if os.path.exists(weight_path):
#     %cd /content/yolov5/ 
    !python detect.py --weights $weight_path --img 416 --source $file_path --name $config --conf-thres 0.5

list_c1a = ["sr", "mr", "lr", "xr"]
list_c1b = ["swr", "mwr", "lwr", "xwr"]
list_c2a = ["lr", "lwr", "ldr", "lwdr"]
list_c2b = ["xr", "xwr", "xdr", "xwdr"]

compare_detections(list_c1a, title="Detecções de redes sem pré-treino")

compare_detections(list_c1b, title="Detecções de redes com pré-treino")

compare_detections(list_c2a, title="Detecções de redes sem pré-treino")

compare_detections(list_c2b, title="Detecções de redes com pré-treino")

"""##Cenário 1

####Imagem padrão
"""

print(idx1_max, CONFIGS_LIST[idx1_max])
print(idx1_min, CONFIGS_LIST[idx1_min])

# Commented out IPython magic to ensure Python compatibility.
best_weight = "/content/gdrive/MyDrive/Podocitos/Retreino/v5" + CONFIGS_LIST[idx1_max] + "/weights/best.pt"
worst_weight = "/content/gdrive/MyDrive/Podocitos/Retreino/v5" + CONFIGS_LIST[idx1_min] + "/weights/best.pt"
filename = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test/images/n61_jpg.rf.a817c47873529dee6853763172e5c328.jpg"

# %cd /content/yolov5/ 
!python detect.py --weights $best_weight --img 416 --source $filename --name c1a
!python detect.py --weights $worst_weight --img 416 --source $filename --name c1b

compara_redes([DETECTION_SRC+"c1a", DETECTION_SRC+"c1b"], 
              "Detecção em Imagem Padrão",
              set_title=["Melhor rede", "Pior Rede"])

"""####Comparação entre a melhor e a pior imagem"""

# Commented out IPython magic to ensure Python compatibility.
items = ["v5" + item for item in CONFIGS_LIST]
# %cd /content/yolov5
best_worst(items)

best_path = "/content/yolov5/runs/detect/v5" + CONFIGS_LIST[idx1_max] + "b"
worst_path = "/content/yolov5/runs/detect/v5" + CONFIGS_LIST[idx1_max] + "w"
compara_redes([best_path, worst_path], "Detecções da melhor rede",
              set_title=["Imagem de melhor resultado", "Imagem de pior resultado"])

"""##Cenário 2

####Imagem padrão
"""

print(idx2_max, CONFIGS_LIST[idx2_max])
print(idx2_min, CONFIGS_LIST[idx2_min])

# Commented out IPython magic to ensure Python compatibility.
best_weight = "/content/gdrive/MyDrive/Podocitos/Retreino/v5" + CONFIGS_LIST[idx1_max] + "/weights/best.pt"
worst_weight = "/content/gdrive/MyDrive/Podocitos/Retreino/v5" + CONFIGS_LIST[idx1_min] + "/weights/best.pt"
filename = "/content/gdrive/MyDrive/Podocitos/Datasets/original/test/images/n61_jpg.rf.a817c47873529dee6853763172e5c328.jpg"

# %cd /content/yolov5/ 
!python detect.py --weights $best_weight --img 416 --source $filename --name c2a
!python detect.py --weights $worst_weight --img 416 --source $filename --name c2b

compara_redes([DETECTION_SRC+"c2a", DETECTION_SRC+"c2b"], 
              "Detecção em Imagem Padrão",
              set_title=["Melhor rede", "Pior Rede"])

"""####Comparação entre a melhor e a pior imagem"""

# Commented out IPython magic to ensure Python compatibility.
items = ["v5" + item for item in CONFIGS_LIST]
# %cd /content/yolov5
best_worst(items)

best_path = "/content/yolov5/runs/detect/v5" + CONFIGS_LIST[idx2_max] + "b"
worst_path = "/content/yolov5/runs/detect/v5" + CONFIGS_LIST[idx2_max] + "w"
compara_redes([best_path, worst_path], "Detecções da melhor rede",
              set_title=["Imagem de melhor resultado", "Imagem de pior resultado"])

"""#Rascunho"""

df_final = pd.DataFrame()
indexes = []

for config in CONFIGS_LIST:
  try:
    results_path = '/content/gdrive/MyDrive/Podocitos/Retreino/v5' + config + '/results.txt'
    if not os.path.exists(results_path):
      results_path = results_path[:-3] + 'csv'
    aux = cria_df(results_path)
    
  except:
    print(config)
    continue
  idx1 = aux["Fit"].idxmax()
  idx = aux["mAP"].idxmax()
  if idx == idx1:
    print('ingual')
  indexes.append(idx)
  series = pd.Series(aux.iloc[idx, :].values, index=aux.columns)
  df_final = df_final.append(series, ignore_index=True)

axis = [
        "YOLOV5S SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5M SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5L SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5X SEM PRÉ-TREINO - ORIGINAL",
        "YOLOV5S COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5M COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5L COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5X COM PRÉ-TREINO - ORIGINAL",
        "YOLOV5S SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5M SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5L SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5X SEM PRÉ-TREINO - AUMENTADO",
        "YOLOV5S COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5M COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5L COM PRÉ-TREINO - AUMENTADO",
        "YOLOV5X COM PRÉ-TREINO - AUMENTADO"
]

df_final["Index"] = indexes
print(df_final["mAP"].sort_values().set_axis(axis))
# print(df_final[["P", "R", "F1", "mAP"]].set_axis(axis))

# Commented out IPython magic to ensure Python compatibility.
src="/content/gdrive/MyDrive/Podocitos/Datasets/original/test"
weight_path="/content/gdrive/MyDrive/Podocitos/Retreino/v5lwdr/weights/best.pt"

for image in sorted(os.listdir(src + "/images")):
#   %rm -rf test_images
  os.mkdir("test_images")
  os.mkdir("test_images/images")
  os.mkdir("test_images/labels")
  filename = image.split("/")[-1].split(".jpg")[0]
  imagename = src + "/images/" + filename + ".jpg"
  labelname = src + "/labels/" + filename + ".txt"

  shutil.copy(imagename, "test_images/images")
  shutil.copy(labelname, "test_images/labels")

  !python test.py --weights $weight_path --data /content/data.yaml --img 416 
  !python detect.py --weights $weight_path --img 416 --source $imagename

for imageName in glob.glob('/content/yolov5/runs/detect/' + '/*/*.jpg'): #assuming JPG
  #finds labelname corresponding to image
  filename = imageName.split("/")[-1].split(".jpg")[0]
  label_path = LABEL_DIR + filename + ".txt"
  img=draw_annotation(imageName, label_path)
  plt.figure(figsize=(9, 9))
  plt.axis('off')
  print(imageName.split('exp')[1])
  plt.imshow(img)
  plt.show()

# Commented out IPython magic to ensure Python compatibility.
src="/content/gdrive/MyDrive/Podocitos/Datasets/original/test"
filename="FIOCRUZ20190122--1079-_jpg.rf.dfeddcd29a82fb481d35286e3b79a7db"

# %rm -rf ./test_images
os.mkdir("test_images")
os.mkdir("test_images/images")
os.mkdir("test_images/labels")
imagename = src + "/images/" + filename + ".jpg"
labelname = src + "/labels/" + filename + ".txt"
shutil.copy(imagename, "test_images/images")
shutil.copy(labelname, "test_images/labels")

!python test.py --weights $weight_path --data /content/data.yaml --img 416 
!python detect.py --weights $weight_path --img 416 --source $imagename --name gbg3 --conf-thres 0.23

imageName = glob.glob("/content/yolov5/runs/detect/gbg3/*.jpg")[0]
filename = imageName.split("/")[-1].split(".jpg")[0]
label_path = LABEL_DIR + filename + ".txt"
img=draw_annotation(imageName, label_path)
plt.figure(figsize=(9, 9))
plt.axis('off')
plt.imshow(img)
plt.show()

#nucleo
!python detect.py --weights '/content/gdrive/MyDrive/Nucleos/Retreino/v5xwdr/weights/best.pt' --img 416 --source '/content/imagem/n22_jpg.rf.e5bc688fe954ab26efd4d7607d065a13.jpg'

imageName = ''glob.glob("/content/yolov5/runs/detect/exp/*.jpg")[0]''
filename = imageName.split("/")[-1].split(".jpg")[0]
label_path = '/content/labelnucleo/n22_jpg.rf.e5bc688fe954ab26efd4d7607d065a13.txt'
img=draw_annotation(imageName, label_path)
plt.figure(figsize=(9, 9))
plt.axis('off')
plt.imshow(img)
plt.show()

#pod
!python detect.py --weights '/content/gdrive/MyDrive/Podocitos/Retreino/v5lwdr/weights/best.pt' --img 416 --source '/content/imagem/n22_jpg.rf.e5bc688fe954ab26efd4d7607d065a13.jpg'

imageName = '/content/imagem/n22_jpg.rf.e5bc688fe954ab26efd4d7607d065a13.jpg'
filename = imageName.split("/")[-1].split(".jpg")[0]
label_path = '/content/labelpod/n22_jpg.rf.67543d7c62dfbeee773144f98b8e49bd.txt'
img=draw_annotation(imageName, label_path)
plt.figure(figsize=(9, 9))
plt.axis('off')
plt.imshow(img)
plt.show()