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

    #Resituisce una coppia [caption,foil] diversa in base all'id passato
    def getCaptionFoil(self,row,id,description = " "):
        category = row["Category"]
        match id:
            case 0:
                caption = f'The image express {category}'
                foil = f'The image express {emotion_opposites[category]}'
                return caption,foil
            case 1:
                xmin = row["xmin"]
                ymin = row["ymin"]
                xmax = row["xmax"]
                ymax = row["ymax"]
                print("xmin = ",xmin)
                caption = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) expresses {category}'
                foil = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) expresses {emotion_opposites[category]}'
                print(caption, " ",foil," ")
                return caption,foil
            case 2:
                #Caption scritta dall'utente
                xmin = row["xmin"]
                ymin = row["ymin"]
                xmax = row["xmax"]
                ymax = row["ymax"]
                print("xmin = ",xmin)
                caption = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) with description = " {description} ", expresses {category}'
                foil = f'The image region defined by the coordinates (xmin = {xmin}, xmax = {xmax}, ymin = {ymin}, ymax = {ymax}) with description = " {description} ", expresses {emotion_opposites[category]}'
                print(caption, " ",foil," ")
                return caption,foil
                
                

               
        
        
    def checkDuplicate(self,image,duplicate,analizzati):
        if not duplicate : return False
        if image in analizzati : return True
        return False
        
    def SimpleEmotionDataset(self,id,duplicate : bool):
        '''
            Struttura: The image express {emotion}
        '''
        jsonDataset = {}
        #Estrazione dati dal database
        db = pd.read_csv(self.databasePath)

        j = -1
        founds = 0
        analizzati = []
        
        for i,row in db.iterrows():
            if self.checkDuplicate(row["Image"],duplicate,analizzati) : continue
            if imageNotFound(row["Image"]) : continue
            founds += 1
                
            j+=1
            analizzati.append(row["Image"])
            #Costruzione caption e foil
            caption,foil = self.getCaptionFoil(row,id)

            #Costruzione campione
            data = {
                "image_file" : row["Image"],
                "caption"    : caption,
                "foil"       : foil 
            }

            jsonDataset[str(j)] = data

        name = f'simpleEmotions{id}.json'
        with open(name,"a") as file:
            json.dump(jsonDataset,file,indent=4)

        #print("founds = ",founds)


    def update(self):
        name = f'simpleEmotions{2}.json'
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
        

    def save(self,jsonDataset):
        print("--Salvataggio in corso--")
        name = f'simpleEmotions{2}.json'
        with open(name,"w") as file:
            json.dump(jsonDataset,file,indent=4)
        print("--Salvataggio avvenuto con successo--")
            
        
    def HumanEmotionDataset(self):
        '''
            Permette all'utente di creare delle caption riutilizzabili
            L'utente può salvare la sua sessione in qualsiasi momento e decidere cosi di uscire (Basta passare "0")
            Ad ogni passo all'utente viene mostrata un'immagine e gli viene chiesto di descrivere una sottoporzione precisa dell'immagine
        '''
        db = pd.read_csv(self.databasePath)
        
        jsonDataset,rowNumber = self.update()
        #Scorro le righe del database
        for i,row in db.iterrows():
            #Continua da rowNumber(Serve per continuare da dove ci eravamo fermati)
            if i < rowNumber : continue
            print("Campione: ",i)
            
            #Immagine
            xmin,ymin,xmax,ymax = int(row["xmin"]),int(row["ymin"]),int(row["xmax"]),int(row["ymax"])
            currentPath = f'{self.imgPath}{row["Image"]}'
            img = cv2.imread(currentPath)
            cv2.rectangle(img, (xmin,ymin),(xmax,ymax), (0, 255, 0), 5)  # verde, spessore 2
            cv2.imshow("Finestra",img)
            cv2.waitKey(0)
            description = input("Descrivi brevemente l'immagine mostrata \n")
            cv2.destroyAllWindows()
            if description == "0" : break
            
            caption,foil = self.getCaptionFoil(row,2,description)
            
            #Costruzione campione
            data = {
                "image_file" : row["Image"],
                "caption"    : caption,
                "foil"       : foil 
            }

            jsonDataset[str(i)] = data
            
        self.save(jsonDataset)

    
            
            
            
            
        



emot1 = JsonGenerator(path,imgPath,emotion_opposites)
while True:
    print("Benvenuto all' interno del generatore di dataset json")
    print("0 : Generazione emotionDataset- The image express [emozione]")
    print("1 : Generazione emotionDataset- The image region defined by the coordinates (xmin, xmax, ymin, ymax) expresses [emotion]")
    print("2 : Generazione emotionDataset- Uguale alla 1 con l'aggiunta di una descrizione, scritta dall'utente.")
    
    scelta = int(input())

    if(scelta == 2) :
        emot1.HumanEmotionDataset()
    else :
        emot1.SimpleEmotionDataset(scelta,False)



        
        

    








