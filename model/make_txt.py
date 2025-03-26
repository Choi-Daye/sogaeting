import os
import sys

# final .txt file
sys.stdout = open('datasets/cow_train.txt', 'w')

# read image path
path = "datasets/cow_images/positive"
file_lst = os.listdir(path)

# read .jpg file
for file1 in file_lst:
    # print(file1)
    filepath = os.listdir(path + '/' + file1)
    # print(filepath)

    for file2 in filepath:
        filepath2 = os.listdir(path + '/' + file1 + '/' + file2)

        for file3 in filepath2 :
            print(path + '/' + file1 + '/' + file2 + '/' + file3)

sys.stdout.close()