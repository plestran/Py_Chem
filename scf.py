# Self-Consistent Field Main Script
# Torin Stetina
# June 5th 2017

import time
import numpy as np
from numpy import genfromtxt
from scipy.linalg import eig, eigh
import scipy.io

# Internal imports
from mo_transform import ao2mo
from mp2 import mp2
from response import*
#import sys
##sys.path.insert(0, '/path/to/application/app/folder')


###############################
##     F U N C T I O N S     ##
###############################

def getIntegrals(molecule):
  # Vnn = Nuclear repulsion energy value
  # Vne = Electron-Nuclear attraction matrix
  # T   = Kinetic energy matrix
  # S   = Overlap matrix
  # ERI = Electron-Electron repulsion tensor
  direc = 'test_systems/' + molecule

  Vnn = genfromtxt('./' + direc + '/Vnn.dat',dtype=None)
  Vne = genfromtxt('./' + direc + '/Vne.dat',dtype=None)
  T   = genfromtxt('./' + direc + '/T.dat',dtype=None)
  S   = genfromtxt('./' + direc + '/S.dat',dtype=None)
  ERI = scipy.io.loadmat( direc + '/ERI.mat', squeeze_me=False) 
  return Vnn, Vne, T, S, ERI['ERI']


def deltaP(P,P_old):  
  # Calculate change in density matrix  
  return max(abs(P.flatten()-P_old.flatten()))


###############################
##       M   A   I   N       ##
###############################

start_time = time.time()

#### TEST SYSTEMS #### 

## Test Molecules
#mol, Nelec, name, basis = 'H2_STO3G', 2, 'H2', 'STO-3G'
#mol, Nelec, name, basis = 'HeHplus_STO3G', 2, 'HeH+', 'STO-3G'
#mol, Nelec, name, basis = 'CO_STO3G', 14, 'CO', 'STO-3G' 
mol, Nelec, name, basis = 'H2O_STO3G', 10, 'Water', 'STO-3G'
#mol, Nelec, name, basis = 'Methanol_STO3G', 18, 'Methanol', 'STO-3G'

######################



# Define number of MOs
nMOs = Nelec //2  # RHF

# Get integrals from files
Vnn, Vne, T, S, ERI = getIntegrals(mol)

# Number of basis functions dim
dim = len(S)

# Build Core Hamiltonian
h = T + Vne

# Set up initial Fock with core guess, and density at 0
F = h
P = np.zeros((dim,dim))
C = np.zeros((dim,dim))

# Form transformation matrix
s, Y = eigh(S)
s = np.diag(s**(-0.5))
X = np.dot(Y, np.dot(s, Y.T))

# Form transformation matrix
s, Y = eigh(S)
s = np.diag(s**(-0.5))
X = np.dot(Y, np.dot(s, Y.T))

# Initialize variables
delta = 1.0
conver = 1.0e-10
count = 0

# Start main SCF loop
while delta > conver and count < 256:
  count += 1
  E0 = 0
  Vee = np.zeros((dim,dim))
  for m in range(0,dim):
    for n in range(0,dim):
      for k in range(0,dim):
        for l in range(0,dim):
          Vee[m,n] += P[k,l] * (ERI[m,n,l,k]- 0.5*ERI[m,k,l,n])
      E0 += 0.5 * P[m,n] * (2*h[m,n] + Vee[m,n])  
  E0 += Vnn

  # Update Fock
  F = h + Vee
 
  # Orthonormalize Fock
  F_p = np.dot(X.T,np.dot(F, X))
  eps, C_p = eigh(F_p)
  C = np.dot(X, C_p)
  
  # Normalize C
  norm = np.sqrt(np.diag(np.dot(np.dot(np.transpose(C),S),C) ))
  for i in range(0,dim):
    C[:,i] = C[:,i]/norm[i]
  
  # Update Density Matrix
  P_old = P   
  P = 2.0 * np.dot(C[:,0:nMOs],np.transpose(C[:,0:nMOs]))
  
  # Compute change in density matrix
  delta = deltaP(P, P_old)
  

elapsed_time = time.time() - start_time

### Print results ###
print ''
print '~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ '
print '                   R e s u l t s            \n'
print 'Molecule: ' + name 
print 'Basis: ' + basis
print 'E(SCF) = ' + str(E0) + ' a.u.'
print 'SCF iterations: ' + str(count)
print 'Elapsed time: ' + str(elapsed_time) + ' sec'
print ''
print 'Fock Matrix = \n' + np.array_str(F)
print 'Density Matrix = \n' + np.array_str(P)
print 'Orbital Energies = \n' + str(eps) + '\n'
print '~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ '
print ''

# Convert AO to MO orbital basis
#print '-------------------------'
eriMO = ao2mo(ERI, C)
#mp2(eriMO, eps, Nelec)
#print responseAB(eriMO, eps, Nelec)
TDHF(eriMO, eps, Nelec, False)
#print '-------------------------'










