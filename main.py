import pandas as pd
import json
import os
import cv2
'''
Il programma prende in input il databes HECO e crea un file json che ha le seguenti caratteristiche:
{
    image_file: "nome_file",
    caption: "The image express" + emozione presa dal dataset
    foil: "The image express" + emozione opposta

    Emozioni presenti nel dataset:
        Peace,Anger,Happiness,Excitement,Fear,Sadness,Surprise,Disgust
}
'''
#dati

#Dizionario emozioni opposte
emotion_opposites = {}
rows = 500
#Percorso database
path = "HECO_Labels.csv"
imgPath = "/home/luigi/Scrivania/LVLM/emotionDataset/"


#Mappatura emozioni

def addOpposite(x: str, y: str,emotion_opposites):
    '''
    Registra nel dizionario emotion_opposites, l'emozione x come l'opposto dell' emozione y e viceversa.
    '''
    emotion_opposites[x] = y
    emotion_opposites[y] = x

addOpposite("Peace","Anger",emotion_opposites)
addOpposite("Happiness","Sadness",emotion_opposites)
addOpposite("Excitement","Disgust",emotion_opposites)
addOpposite("Fear","Surprise",emotion_opposites)


#vedi se l'immagine esiste all'interno della cartella
def imageNotFound(img : str):
    imagePath = f'{imgPath}{img}'
    #print(imagePath)
    if os.path.exists(imagePath) : return False
    #print("Percorso non trovato")
    return True

    
class JsonGenerator:
    
    def __init__(self,databasePath : str,imgPath : str,opposites):
    
        '''
            databasePath : percorso del database
            imgPath : percorso della cartella contenente le immagini
            opposites : dictionary contenente coppie di emozioni opposte (happy,anger)
            
        '''
        self.databasePath = databasePath
        self.imgPath = imgPath
        self.opposites = opposites

    #Ad ogni emozione associa una descrizione testuale
    def getDescriptionByEmotion(self,emotion):
        if emotion == "Peace":
            return "A person with relaxed facial features and a soft gaze."
        if emotion == "Anger":
            return "A person with tense muscles and a firm jaw."
        if emotion == "Happiness":
            return "A person with lifted corners of the mouth and bright eyes."
        if emotion == "Excitement":
            return "A person with wide eyes and raised eyebrows."
        if emotion == "Fear":
            return "A person with widened eyes and slightly pulled-back posture."
        if emotion == "Sadness":
            return "A person with lowered eyelids and a downturned mouth."
        if emotion == "Surprise":
            return "A person with raised eyebrows and slightly open mouth."
        if emotion == "Disgust":
            return "A person with a wrinkled nose and tightened lips"
            
    #Resituisce una coppia [caption,foil] strutturata in modo diverso in base all'id passato
    def getCaptionFoil(self,row,id):
        '''
        row : dictionary
        id  : int (0,1,2,3) Permette di scegliere il tipo di (caption,foil) che vogliamo
        desctiption : nel caso dell' id = 2, la descrizione viene utilizzata all'interno della caption
        '''
        category = row["Category"]
        match id:
            case 0:
                caption = f'The image express {category}'
                foil = f'The image express {emotion_opposites[category]}'
                
                return caption,foil
            case 1:
                xmin,ymin,xmax,ymax = int(row["xmin"]),int(row["ymin"]),int(row["xmax"]),int(row["ymax"])
                
                caption = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) expresses {category}'
                foil = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) expresses {emotion_opposites[category]}'
                
                return caption,foil
            case 2:
                
                xmin,ymin,xmax,ymax = int(row["xmin"]),int(row["ymin"]),int(row["xmax"]),int(row["ymax"])
                currentPath = f'{self.imgPath}{row["Image"]}'

                #Lettura dell'immagine
                img = cv2.imread(currentPath)
                #Disegno un rettangolo all'interno dell'immagine di coordinate (xmin,ymin) (xmax,ymax) 
                cv2.rectangle(img, (xmin,ymin),(xmax,ymax), (0, 255, 0), 5)  # verde, spessore 2
                #Mostro l' immagine all'utente
                cv2.imshow("Finestra",img)
                cv2.waitKey(0)
                #Chiedo di descrivere ciò che si vede nel rettangolo
                description = input("Descrivi brevemente l'immagine mostrata \n")
                cv2.destroyAllWindows()

                #Controllo segnale di stop da parte dell'utente
                if description == "0" : return "0","0"
                #Unisco il tutto
                caption = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) with description = " {description} ", expresses {category}'
                foil = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) with description = " {description} ", expresses {emotion_opposites[category]}'
                print(caption, " ",foil," ")
                
                return caption,foil
            case 3:
               xmin,ymin,xmax,ymax = int(row["xmin"]),int(row["ymin"]),int(row["xmax"]),int(row["ymax"])
               descr = self.getDescriptionByEmotion(category)
               caption = f'The image region (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}), with description = {descr} expresses {category}'
               foil = f'The image region (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}), with description = {descr} expresses {emotion_opposites[category]}'
               return caption,foil
               
    #Crea un emotionDataset in formato json a partire da un dataset csv: {xmin,ymin,xmax,ymax(numbers),caption,foil(stringhe)}    
    def SimpleEmotionDataset(self,id : int,numberOfElements = 80):
        '''
            id : struttura della coppia (caption,foil) (0,1,2,3)
        '''

        #Prendo le tuple esistenti
        jsonDataset,start = self.update(id)
        founds = 0
        j = 0
        
        #Estrazione dati dal database
        db = pd.read_csv(self.databasePath)

        for i,row in db.iterrows():

            #Controlli
            if i < start : continue
            if i == numberOfElements : break
            if imageNotFound(row["Image"]) : continue

            print("Campione: ",i,"Emozione classificata: ",row["Category"])

            
            #founds += 1   
            #Costruzione caption e foil
            caption,foil = self.getCaptionFoil(row,id)

            #Segnale di stop
            if caption == "0" : break
            
            #Costruzione campione
            data = {
                "image_file" : row["Image"],
                "caption"    : caption,
                "foil"       : foil 
            }
            #Aggiunta del campione i-esimo al dataset
            jsonDataset[str(i)] = data

        #Trascrizione del dataset su file
        self.save(jsonDataset,id)

    #Evito di sovrascrivere i dati ogni volta
    def update(self,id):
        name = f'simpleEmotions{id}.json'
        #Da che riga devo iniziare?
        start = 0
        #Se il file esiste già allora devo continuare ad aggiungere dati
        if os.path.exists(name):
            with open(name,"r") as f:
                data = json.load(f)
                start = len(data)
                print(start)
                
        #Il file non esiste e quindi non c'è nulla da caricare    
        else :
            data = {}
            
        return data,start
        
    #Salvo il lavoro svolto
    def save(self,jsonDataset,id):
        print("--Salvataggio in corso--")
        name = f'simpleEmotions{id}.json'
        with open(name,"w") as file:
            json.dump(jsonDataset,file,indent=4)
        print("--Salvataggio avvenuto con successo--")



            
emot1 = JsonGenerator(path,imgPath,emotion_opposites)
while True:
    #Opzioni
    print("Benvenuto all' interno del generatore di dataset json")
    print("exit : termina l' esecuzione del programma")
    print("0 : Generazione emotionDataset- The image express [emozione]")
    print("1 : Generazione emotionDataset- The image region defined by the coordinates (xmin, xmax, ymin, ymax) expresses [emotion]")
    print("2 : Generazione emotionDataset- Uguale alla 1 con l'aggiunta di una descrizione, scritta dall'utente.")
    print("3 : Generazione emotionDataset- Uguale alla 2 ad eccezzione del fatto che la descrizione è associata all'emozione")
    #Prendo la scelta dell'utente
    scelta = input()
    
    #Termina l' esecuzione del programma
    if scelta == "exit" : break

    #Creazione del dataset
    scelta = int(scelta)
    emot1.SimpleEmotionDataset(scelta,100)
   



        
        

    








