# Running [Maximum Classifier Discrepancy for Domain Adaptation](https://github.com/mil-tokyo/MCD_DA) on multiple GPUs

The code in this repo was modified from [MCD_DA](https://github.com/mil-tokyo/MCD_DA).

Before running the code, you will need to download the [classification track VISDA dataset](https://github.com/VisionLearningGroup/taskcv-2017-public/tree/master/classification) and place it in ```./data/2017/``` folder:
```
mkdir data/
cd ./data/
mkdir 2017/
cd ./2017/
wget http://csr.bu.edu/ftp/visda17/clf/train.tar
tar xvf train.tar

wget http://csr.bu.edu/ftp/visda17/clf/validation.tar
tar xvf validation.tar  
```

Then, the code can be ran by:

```python main.py```

Note that this code was written a long time a ago, and as I do not have a multiple GPU environment at this time, I'm not able to test this code now. Therefore, there might be some minor bugs to run the code, but they should be fixed easily. Please feel free to open an issue or contact me if you found any bugs :)

If you find this work usefull, please cite the original paper:
```
@inproceedings{saito2018maximum,
  title={Maximum classifier discrepancy for unsupervised domain adaptation},
  author={Saito, Kuniaki and Watanabe, Kohei and Ushiku, Yoshitaka and Harada, Tatsuya},
  booktitle={Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition},
  pages={3723--3732},
  year={2018}
}
```
