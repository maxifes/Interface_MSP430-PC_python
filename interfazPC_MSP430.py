from serial import EIGHTBITS, PARITY_ODD, STOPBITS_ONE
import serial.tools.list_ports
import serial
import time

def int_to_bytes(vector): 
    data = []
    i = 0
    for element in vector:
        data.append(vector[i].to_bytes(1,'big'))
        i = i+1
    return data
    
def translate_IntelHex_Line(vector):
    data  = []
    dataBytes = []
    numBytes = vector[1:3]
    data.append(int(numBytes,16))
    Low_ADDRESS_MSB = vector[3:5]
    data.append(int(Low_ADDRESS_MSB,16))
    Low_ADDRESS_LSB = vector[5:7]
    data.append(int(Low_ADDRESS_LSB,16))
    Record_Type = vector[7:9]
    data.append(int(Record_Type,16))

    for i in range(0,int(numBytes,16)):
        a =  vector[9+(i*2):11+(i*2)]
        data.append(int(a,16))

    checksum = 0
    for i in range(0,len(data)):
        checksum = checksum ^ data[i] 
    data.append(checksum)

    #El arreglo del vector es el siguiente
    #data[0] = numBytes
    #data[1] = LowerADDRESS_MSB 
    #data[2] = LowerADDRESS_LSB
    #data[3] = RecordType  
    #data[4] = Inicio de datos.
    #data[4+numBytes] = Checksum. 

    return data

relativa = "STM32_HAL_DMA.hex"
archivo = open(relativa,"r")
prueba =[]
error = 0


ports = serial.tools.list_ports.comports(); 
serialInst = serial.Serial()
portList = []
for onePort in ports: 
    portList.append(str(onePort))
    print(str(onePort))
val = input("Select port: COM")

for x in range(0,len(portList)):
    if portList[x].startswith("COM"+str(val)):
        portVar = "COM" + str(val)
        print(portVar)

#Configuracion de UART
serialInst.baudrate = 9600
serialInst.bytesize = EIGHTBITS
#serialInst.parity = PARITY_ODD;
serialInst.stopbits = STOPBITS_ONE
#serialInst.timeout = 2.0
serialInst.port = portVar
serialInst.open()

startByte = 15 #0x0F
endByte = 240  #0xF0 
ackByte = 121 #0x79
nackByte = 127 #0x7F

startByte = startByte.to_bytes(1,'big')
endByte = endByte.to_bytes(1,'big')
ackByte = ackByte.to_bytes(1,'big')
nackByte = nackByte.to_bytes(1,'big')

serialInst.write(startByte) #indica que comenzará transmision

while(error != 2):
    vector = archivo.readline()
    data = translate_IntelHex_Line(vector)
    data_in_Bytes = int_to_bytes(data)
    error = 0 #resetea el valor del vector a 0 
    if(data[3] == 0):
        ##while(error != 2): 
        serialInst.write(data_in_Bytes[0]) #Envia Byte ADDRESS MSB 
        time.sleep(0.1)
        serialInst.write(data_in_Bytes[1]) #Envia Byte ADDRESS LSB
        time.sleep(0.1)
        serialInst.write(data_in_Bytes[2]) #Envia numero de Bytes
        time.sleep(0.1)
        serialInst.write(data_in_Bytes[3]) #Envia numero de Bytes
        time.sleep(0.1)
        for i in range(4,4+data[0]):
            serialInst.write(data_in_Bytes[i]) #Envia Bytes de datos.
            time.sleep(0.1)
        serialInst.write(data_in_Bytes[4+data[0]])
        #ack_received = serialInst.read(); ##Espera Byte de ACK 
        #if (ack_received != ackByte): ##Si el byte de ack coincide
        #    break # Sale del while
        #if (ack_received != ackByte):
        #    error = error + 1 #repite el while pero incrementa el error
        print(data)
    elif(data[3] == 1):
        #enviarByte de terminacion al MSP430.
        print("Se ha terminado de cargar el programa")
        break
    elif(data[3] == 2): 
        print("Intruccion extended segment Address")
    elif(data[3] == 3): 
        print("start segment Address")
    elif(data[3] == 4):
        print("exteded linear Address")
    elif(data[3] == 5): 
        print("Start linear Address")
    for i in range(0,5):
        serialInst.write(ackByte)

if (error == 2):
    print("El byte de ACK ha sido incorrecta dos veces consecutivas")

serialInst.close()