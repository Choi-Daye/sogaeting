import os

negative_path = ""
positive_path = ""

nevative_file_lst = os.listdir(negative_path)
positive_file_lst = os.listdir(positive_path)


### "Positively predicted" value among "actual negative" values ###
for neg_file1 in nevative_file_lst:
    filepath = os.path.join(negative_path, neg_file1)

    # Count Number
    negative_positive_cnt += 1


### Among the "actual positive" values, "positively predicted" values ###
for pos_file1 in positive_file_lst:
    filepath = os.path.join(positive_path, pos_file1)

    # Count Number
    positive_positive_cnt += 1


print("오탐 : ", negative_positive_cnt)
print("탐지 : ", positive_positive_cnt)