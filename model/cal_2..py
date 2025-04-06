### Run cal_1.py first ###

# 272
total = 16
negative_positive_cnt = 11
positive_positive_cnt = 15


# confusion matrix
true_positives = positive_positive_cnt
false_positives = total - positive_positive_cnt
true_negatives = total - negative_positive_cnt
false_negatives = negative_positive_cnt

## How accurately they categorized it
accuracy = (true_positives + true_negatives) / (true_positives + true_negatives + false_positives + false_negatives)
## Predict "True" -> Actually "True"
precision = true_positives / (true_positives + false_positives)
## Actually "True" -> Predict "True"
recall = true_positives / (true_positives + false_negatives)
## 
f1score = 2 * precision * recall / (precision + recall)
## False positive rate
FPR = false_positives / (false_positives + true_negatives)


print(f"accuracy(정확도) : {accuracy}")
print(f"precision(정밀도) : {precision}")
print(f"recall(재현율) : {recall}")
print(f"f1score : {f1score}")
print(f"FPR(오탐율) : {FPR}")
print("")
print(f"탐지율 : {recall*100}")
print(f"오탐율 : {(1-recall)*100}")