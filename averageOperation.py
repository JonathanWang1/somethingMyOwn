'''
Created on Mar 20, 2016

@author: root
'''
import numpy as np 
from scipy.ndimage import generic_filter 
from numpy import dtype

class averageOperation():
    # the function to test the custom filter 
    def do(self,s,  aArray, cArray): 
        # center of filter (in both directions) 
        c = s / 2
        
        # extend aArray and cArray
        aaArray = np.pad(aArray, ((c, c), (c, c), (c, c)),'edge')
        ccArray = np.pad(cArray, ((c, c), (c, c), (c, c)),'constant', constant_values=(False))
        
        c = float(c)

    
        # define  average filter 
        filt = np.ones((s,s,s), dtype = float)
        filt = filt / (s*s*s)
        print filt
        
        dArray = aaArray[:,:,:];
        Ashape = aaArray.shape
        
        c = int(c)
        
        for i in range(c, Ashape[0] - c):
            for j in range(c, Ashape[1] - c):
                for k in range(c, Ashape[2] - c):
                    if ccArray[i][j][k] == False:
                        continue
                    tempA = aaArray[(i - c):(i + c + 1), (j - c):(j + c + 1), (k - c):(k + c + 1)]
                    tempC = ccArray[(i - c):(i + c + 1), (j - c):(j + c + 1), (k - c):(k + c + 1)]
                    mask = np.where(tempC) 
                    
                    dArray[i][j][k] = np.sum(tempA[mask]*filt[mask])/np.sum(filt[mask])
        return dArray[c:-c, c:-c, c:-c]

     
if __name__ == '__main__':    
    aArray = np.array([[[1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5]],
                      [[1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5]],
                      [[1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5]],
                      [[1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5]],
                      [[1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5],
                      [1,2,3,4,5]]],
                       dtype = float) 
    cArray = np.array([[[True, True, False, True, True],
                       [True, True, False, True, True],
                       [True, True, True, True, True],
                       [True, True, False, True, True],
                       [True, True, False, True, True]],
                      [[True, True, False, True, True],
                       [True, True, False, True, True],
                       [True, True, True, True, True],
                       [True, True, False, True, True],
                       [True, True, False, True, True]],
                      [[True, True, False, True, True],
                       [True, True, False, True, True],
                       [True, True, True, True, True],
                       [True, True, False, True, True],
                       [True, True, False, True, True]],
                      [[True, True, False, True, True],
                       [True, True, False, True, True],
                       [True, True, True, True, True],
                       [True, True, False, True, True],
                       [True, True, False, True, True]],
                      [[True, True, False, True, True],
                       [True, True, False, True, True],
                       [True, True, True, True, True],
                       [True, True, False, True, True],
                       [True, True, False, True, True]]], dtype = bool)
    g = averageOperation()
    abc = g.do(5, aArray, cArray)
        
    print abc
     