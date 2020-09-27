# Running PyToch moodel on multiple GPUs
Test code for using multiple GPU via pytorch. Codes are mainly from [https://pytorch.org/tutorials/beginner/blitz/data_parallel_tutorial.html]

You can find the environment setup for mutiple GPUs on this [repo](https://github.com/JiahongChen/Set-up-deep-learning-frameworks-with-GPU-on-Google-Cloud-Platform).

## How to make your code run on multiple GPUs
You only need to warp your model using ```torch.nn.DataParallel``` function:
```
model = nn.DataParallel(model)
```
You may check codes [here](https://github.com/JiahongChen/multiGPU/blob/master/testMultiGPU.py) to test your multiple GPU environment.

Sample code to run deep learning model is provided [in this folder](https://github.com/JiahongChen/multiGPU/tree/master/MCD_multi_GPU), which replicates the paper [Maximum Classifier Discrepancy for Unsupervised Domain Adaptation](https://openaccess.thecvf.com/content_cvpr_2018/papers/Saito_Maximum_Classifier_Discrepancy_CVPR_2018_paper.pdf).

## Error: 'DataParallel' object has no attribute 'xxx'
Instead of using model.xxx, access the model attributes by model.module.xxx.

[ref: https://discuss.pytorch.org/t/how-to-reach-model-attributes-wrapped-by-nn-dataparallel/1373]
