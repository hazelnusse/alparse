import filecmp
import alparse as alp
import os

def test_test1_al():
    alp.alparse("test1_al", "test1_al")
    assert filecmp.cmp('test1_al.txt', 'test1_al_desired.txt')
    #os.remove('test1_al.txt')
