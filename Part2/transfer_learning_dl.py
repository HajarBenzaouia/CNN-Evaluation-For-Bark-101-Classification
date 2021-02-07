# -*- coding: utf-8 -*-
"""Transfer_Learning_DL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11u71zYzl3tAmNYBzdcq1XmGgeHIDNWmj
"""

import matplotlib

matplotlib.use("Agg")
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Model
from keras.layers import Reshape,GlobalAveragePooling2D, BatchNormalization,Input, Dense, Dropout, Activation, Conv2D, MaxPooling2D, concatenate, AveragePooling2D
from keras.utils import plot_model
import os
from keras.models import Model
from keras.optimizers import SGD
from imutils import paths
from keras.applications import MobileNet
import matplotlib.pyplot as plt
import numpy as np
import os
from keras import backend as K
import keras

# fonction qui dessine les graphes de l'historique d'entrainement
def plot_training_loss_data_generator(H, N, plotPath):   
  plt.style.use("ggplot")
  plt.figure()
  plt.plot(np.arange(0, N), H.history["loss"], label="train_loss")
  plt.plot(np.arange(0, N), H.history["val_loss"], label="val_loss")
  plt.plot(np.argmax(H.history["loss"]), np.min(H.history["loss"]), marker="x",color="r", label="meilleur train_loss")
  plt.title("Training loss")
  plt.xlabel("Epoch #")
  plt.ylabel("loss")
  plt.legend(loc="lower left")
  plt.savefig(plotPath)
  plt.show()

def plot_training_accu_data_generator(H, N, plotPath):   
  plt.style.use("ggplot")
  plt.figure()
  plt.plot(np.arange(0, N), H.history["accuracy"], label="train_acc")
  plt.plot(np.arange(0, N), H.history["val_accuracy"], label="val_acc")
  plt.plot(np.argmax(H.history["val_accuracy"]), np.max(H.history["val_accuracy"]), marker="x",color="g", label="meilleur accuracy")
  plt.title("Training Accuracy")
  plt.xlabel("Epoch #")
  plt.ylabel("Accuracy")
  plt.legend(loc="lower left")
  plt.savefig(plotPath)
  plt.show()




# variable globales
BASE_PATH = "DataSet_Bark101"
# definir des nom des repertoires train, et test
TRAIN = "Bark101_train"
TEST = "Bark101_test"
# labels des classes
CLASSES = range(0, 101)
#convert int to str
CLASSES = [str(i) for i in CLASSES]
# taille du  batch
BATCH_SIZE = 8

# chemins vers les repertoires train, val et test
trainPath = os.path.sep.join([BASE_PATH, TRAIN])
testPath = os.path.sep.join([BASE_PATH, TEST])

# nbr total des image dans chacun des repo train test
totalTrain = len(list(paths.list_images(trainPath))) 
print(totalTrain)
totalTest = len(list(paths.list_images(testPath)))
print(totalTest)


# instancier un objet ImageDataGenerator pou l'augmentation des donnees train
trainAug = ImageDataGenerator(
    rescale=1.0/255.0,
    horizontal_flip=True,
    fill_mode="nearest")

# instancier un objet ImageDataGenerator pour l'augmentation des donnees test
testAug = ImageDataGenerator(rescale=1.0/255.0)

# definir la moyenne des images ImageNet par plan RGB pour normaliser les images de la base Bark
mean = np.array([123.68, 116.779, 103.939], dtype="float32")
trainAug.mean = mean
testAug.mean = mean

# initialiser le generateur de train
trainGen = trainAug.flow_from_directory(
    trainPath,
    class_mode="categorical",
    target_size=(224, 224),
    color_mode="rgb",
    shuffle=True,
    batch_size=BATCH_SIZE)


# initialiser le generateur de test
testGen = testAug.flow_from_directory(
    testPath,
    class_mode="categorical",
    target_size=(224, 224),
    color_mode="rgb",
    shuffle=False,
    batch_size=BATCH_SIZE)


baseModel = MobileNet(weights="imagenet", include_top=False, input_tensor=Input(shape=(224, 224, 3)))
baseModel_with_FC = MobileNet(weights="imagenet", include_top=True, input_tensor=Input(shape=(224, 224, 3)))
#afficher le model Mobile net avec FC et sans FC

baseModel.summary()
baseModel_with_FC.summary()

# construire une nouvelle couche FC  avec le nombre de classe de la nouvelle base: Bark
# ceci forme le partie superieure du modele
# ajouter notre FC
headModel = baseModel.output
headModel = GlobalAveragePooling2D()(headModel)
headModel = Reshape((1, 1, 1024))(headModel)
headModel = Dropout(0.5)(headModel)
headModel = Conv2D(len(CLASSES), kernel_size=1)(headModel)
headModel = Reshape((len(CLASSES),))(headModel)
headModel = Activation("softmax")(headModel)


# joindre les deux parties pour former le nouveau modele à entrainer
# voir l'image "MobileNet_FC.png"
model = Model(inputs=baseModel.input, outputs=headModel) #new model

#afficher le model Mobile net avec notre propre FC 
keras.utils.plot_model(model, to_file="MobileNet_FC.png", show_shapes= True)

# compiler le nouveau modele
print("[INFO] compiling model...")
opt = SGD(lr=0.001, momentum=0.9)
model.compile(loss="categorical_crossentropy", optimizer=opt, metrics=["accuracy"])

# geler (ou bien freeze) toute les couche basale du modèle, càd on ne va pas changer leur poids mais laisser les poids
# appris sur imagenet
for layer in baseModel.layers:
    layer.trainable = False

# visualiser les couches à entrainer
for layer in baseModel.layers:
    print("{}: {}".format(layer, layer.trainable))


# entrainer la couche FC pour 50 epoch (rappel: toutes les autres couches sont gelees donc leurs poids resteront
# inchangés
from keras.callbacks import ModelCheckpoint
filepath="best_model.hdf5"
checkpoint = ModelCheckpoint(filepath, monitor='val_loss', verbose=1,
              save_best_only=True, mode='max')
callbacks = [checkpoint]
print("[INFO] training head...")
H = model.fit_generator(
    trainGen,
    steps_per_epoch=totalTrain // BATCH_SIZE,
    validation_data=testGen,
    validation_steps=totalTest // BATCH_SIZE,
    epochs=100)

#afficher history de training
plot_training_loss_data_generator(H, 100, "loss.png")
plot_training_accu_data_generator(H, 100, "accuracy.png")