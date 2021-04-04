# Stolen from: https://github.com/nikhilroxtomar/Multi-Layer-Perceptron-in-Python/blob/master/xor.py

import numpy as np
import logging

def sigmoid(x):
	return 1.0/(1.0 + np.exp(-x))

def sigmoid_der(x):
	return x*(1.0 - x)

class NN:
    def __init__(self, inputs, outputs, it=1000000, sensitivity=0.001):
        self.l=len(inputs)
        self.li=len(inputs[0])

        self.wi=np.random.random((self.li, self.l))
        self.wh=np.random.random((self.l, 1))

        self.train(inputs, outputs, it, sensitivity)

    def train(self, inputs, outputs, it=1000000, sensitivity=0.001):
        for i in range(it):
            l0=inputs
            l1=sigmoid(np.dot(l0, self.wi))
            l2=sigmoid(np.dot(l1, self.wh))

            l2_err=outputs - l2
            l2_delta = np.multiply(l2_err, sigmoid_der(l2))

            l1_err=np.dot(l2_delta, self.wh.T)
            l1_delta=np.multiply(l1_err, sigmoid_der(l1))

            self.wh+=np.dot(l1.T, l2_delta)
            self.wi+=np.dot(l0.T, l1_delta)

            if (i > 10) and (np.amax(l2_err) < sensitivity) and (np.amax(l1_err) < sensitivity):
                logging.info("Early training exit "+str(np.amax(l2_err))+" and "+str(np.amax(l1_err))+" at "+str(i))
                break

    def getNumPoints(self):
        return self.li

    def predict(self, inp):
        s1=sigmoid(np.dot(inp, self.wi))
        s2=sigmoid(np.dot(s1, self.wh))
        return s2

    def printNN(self):
        print ("l=",self.l)
        print ("li=",self.li)
        print ("wi=",self.wi)
        print ("wh=",self.wh)

#inputs=np.array([[0,0], [0,1], [1,0], [1,1] ])
#outputs=np.array([ [0], [1],[1],[0] ])
#
#n=NN(inputs)
#print(n.predict(inputs))
#n.train(inputs, outputs, 10000)
#print(n.predict(inputs))