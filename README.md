# multiGPU
Test code for using multiple GPU via pytorch. Codes are mainly from [https://pytorch.org/tutorials/beginner/blitz/data_parallel_tutorial.html]

## How to make your code run on multiple GPUs
You only need to warp your model using ```torch.nn.DataParallel``` function:
```
model = nn.DataParallel(model)
```
You may check codes on [https://github.com/JiahongChen/MCD_DA/blob/master/visda_classification]

## Error: 'DataParallel' object has no attribute 'xxx'
Instead of using model.xxx, access the model attributes by model.module.xxx.

[ref: https://discuss.pytorch.org/t/how-to-reach-model-attributes-wrapped-by-nn-dataparallel/1373]
