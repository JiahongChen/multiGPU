from __future__ import print_function
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable
import numpy as np
from utils import *
from taskcv_loader import CVDataLoader
from basenet import *
import torch.nn.functional as F
import os

# Training settings
parser = argparse.ArgumentParser(description='Visda Classification')
parser.add_argument('--batch-size', type=int, default=32, metavar='N',
                    help='input batch size for training (default: 32)')
parser.add_argument('--test-batch-size', type=int, default=32, metavar='N',
                    help='input batch size for testing (default: 32)')
parser.add_argument('--epochs', type=int, default=10, metavar='N',
                    help='number of epochs to train (default: 10)')
parser.add_argument('--lr', type=float, default=0.001, metavar='LR',
                    help='learning rate (default: 0.001)')
parser.add_argument('--momentum', type=float, default=0.9, metavar='M',
                    help='SGD momentum (default: 0.9)')
parser.add_argument('--optimizer', type=str, default='momentum', metavar='OP',
                    help='the name of optimizer')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
parser.add_argument('--log-interval', type=int, default=50, metavar='N',
                    help='how many batches to wait before logging training status')
parser.add_argument('--num_k', type=int, default=4, metavar='K',
                    help='how many steps to repeat the generator update')
parser.add_argument('--num-layer', type=int, default=2, metavar='K',
                    help='how many layers for classifier')
parser.add_argument('--name', type=str, default='board', metavar='B',
                    help='board dir')
parser.add_argument('--save', type=str, default='./save/', metavar='B',
                    help='board dir')
parser.add_argument('--train_path', type=str, default='./data/2017/train/', metavar='B',
                    help='directory of source datasets')
parser.add_argument('--val_path', type=str, default='./data/2017/validation/', metavar='B',
                    help='directory of target datasets')
parser.add_argument('--dataset', type=str, default='2017', metavar='B',
                    help='directory of target datasets')
parser.add_argument('--resnet', type=str, default='101', metavar='B',
                    help='which resnet 18,50,101,152,200')
parser.add_argument('--model', type=str, default='alexnet', metavar='B',
                    help='type of the feature model used for encoder: [resnet, alexnet]')
parser.add_argument('--multiGPU', type=bool, default=False,
                    help='enable train on multiple GPU or not, default is False')

args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()
if args.dataset == '2018':
    print('=====Using 2018 visda dataset=====')
    train_path = './data/2018/train/'
    val_path = './data/2018/validation/'
elif args.dataset == '2017':
    print('=====Using 2017 visda dataset=====')
    train_path = './data/2017/train/'
    val_path = './data/2017/validation/'
elif args.dataset == '2019':
    print('=====Using 2019 visda dataset=====')
    train_path = './data/2019/real/'
    val_path = './data/2019/sketch/'
num_k = args.num_k
num_layer = args.num_layer
batch_size = args.batch_size
print(batch_size)
save_path = args.save
if not os.path.isdir(save_path):
    os.mkdir(save_path)
save_path += 'mcd_'+str(args.num_k)
featureModel = args.model
# torch.set_default_tensor_type(torch.HalfTensor)
data_transforms = {
    train_path: transforms.Compose([
        transforms.Scale(256),
        transforms.RandomHorizontalFlip(),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    val_path: transforms.Compose([
        transforms.Scale(256),
        transforms.RandomHorizontalFlip(),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}
dsets = {x: datasets.ImageFolder(os.path.join(x), data_transforms[x]) for x in [train_path,val_path]}
dset_sizes = {x: len(dsets[x]) for x in [train_path, val_path]}
dset_classes = dsets[train_path].classes
print ('classes'+str(dset_classes))
use_gpu = torch.cuda.is_available()
torch.manual_seed(args.seed)
if args.cuda:
    torch.cuda.manual_seed(args.seed)
train_loader = CVDataLoader()
train_loader.initialize(dsets[train_path],dsets[val_path],batch_size)
dataset = train_loader.load_data()
test_loader = CVDataLoader()
opt= args
test_loader.initialize(dsets[train_path],dsets[val_path],batch_size,shuffle=True)
dataset_test = test_loader.load_data()
option = 'resnet'+args.resnet
if featureModel =='resnet':
    print('===========Using ResNet model as encoder===========')
    G = ResBase(option)
    F1 = ResClassifier(num_layer=num_layer)
    F2 = ResClassifier(num_layer=num_layer)
    if torch.cuda.device_count() > 1 and args.multiGPU:
        print('===========Using Multiple GPU===========')
        G = nn.DataParallel(G)
        F1 = nn.DataParallel(F1)
        F2 = nn.DataParallel(F2)

elif featureModel =='alexnet':
    print('===========Using AlexNet pre-train model as encoder===========')
    G = AlexNet()
    F1 = AlexClassifier()
    F2 = AlexClassifier()
elif featureModel =='alexnet2':
    print('===========Using AlexNet self-implemented model as encoder===========')
    G = AlexNet2()
    F1 = AlexClassifier()
    F2 = AlexClassifier()
F1.apply(weights_init)
F2.apply(weights_init)
lr = args.lr
if args.cuda:
    print('=====Using CUDA=====')
    G.cuda()
    F1.cuda()
    F2.cuda()
    torch.set_default_tensor_type(torch.HalfTensor)
    torch.set_default_dtype(torch.float16)

if args.optimizer == 'momentum':
    if args.multiGPU:
        optimizer_g = optim.SGD(list(G.module.features.parameters()), lr=args.lr,weight_decay=0.0005)
        optimizer_f = optim.SGD(list(F1.module.parameters())+list(F2.parameters()),momentum=0.9,lr=args.lr,weight_decay=0.0005)
    else:
        optimizer_g = optim.SGD(list(G.features.parameters()), lr=args.lr,weight_decay=0.0005)
        optimizer_f = optim.SGD(list(F1.parameters())+list(F2.parameters()),momentum=0.9,lr=args.lr,weight_decay=0.0005)
elif args.optimizer == 'adam':
    optimizer_g = optim.Adam(G.features.parameters(), lr=args.lr,weight_decay=0.0005)
    optimizer_f = optim.Adam(list(F1.parameters())+list(F2.parameters()), lr=args.lr,weight_decay=0.0005)
else:
    optimizer_g = optim.Adadelta(G.features.parameters(),lr=args.lr,weight_decay=0.0005)
    optimizer_f = optim.Adadelta(list(F1.parameters())+list(F2.parameters()),lr=args.lr,weight_decay=0.0005)    

# enum_dataset = list(enumerate(dataset))
def train(num_epoch):
    criterion = nn.CrossEntropyLoss().cuda()
    correct1Array= []
    correct2Array = []
    size = -1
    for ep in range(num_epoch):
        G.train()
        F1.train()
        F2.train()
        print(len(dataset.data_loader_A.dataset))
        for batch_idx, data in enumerate(dataset): # number of batches: 207785/64 =3246
#       for (batch_idx, data) in enum_dataset: # number of batches: 207785/64 =3246
            if batch_idx * batch_size > 10000:#change back to 30000
                break
            # print(type(data))
            # print(data['S'].size())
            if args.cuda:
                data1 = data['S']
                target1 = data['S_label']
                data2  = data['T']
                target2 = data['T_label']
                data1, target1 = data1.cuda(), target1.cuda()
                data2, target2 = data2.cuda(), target2.cuda()
            # when pretraining network source only
            eta = 1.0
            data = Variable(torch.cat((data1,data2),0))
#           print("Outside: input size", data.size())
            currentData = batch_idx * len(data)/2
            totalData = len(dataset.data_loader_A.dataset)
            if currentData > 200000:#totalData:
                break
            target1 = Variable(target1)
            # Step A train all networks to minimize loss on source
            optimizer_g.zero_grad()
            optimizer_f.zero_grad()
            output = G(data)
            output1 = F1(output)
            output2 = F2(output)

            output_s1 = output1[:batch_size,:]
            output_s2 = output2[:batch_size,:]
            output_t1 = output1[batch_size:,:]
            output_t2 = output2[batch_size:,:]
            output_t1 = F.softmax(output_t1)
            output_t2 = F.softmax(output_t2)

            entropy_loss = - torch.mean(torch.log(torch.mean(output_t1,0)+1e-6))
            entropy_loss -= torch.mean(torch.log(torch.mean(output_t2,0)+1e-6))

            loss1 = criterion(output_s1, target1)
            loss2 = criterion(output_s2, target1)
            all_loss = loss1 + loss2 + 0.01 * entropy_loss
            all_loss.backward()
            optimizer_g.step()
            optimizer_f.step()

            #Step B train classifier to maximize discrepancy
            optimizer_g.zero_grad()
            optimizer_f.zero_grad()

            output = G(data)
            output1 = F1(output)
            output2 = F2(output)
            output_s1 = output1[:batch_size,:]
            output_s2 = output2[:batch_size,:]
            output_t1 = output1[batch_size:,:]
            output_t2 = output2[batch_size:,:]
            output_t1 = F.softmax(output_t1)
            output_t2 = F.softmax(output_t2)
            loss1 = criterion(output_s1, target1)
            loss2 = criterion(output_s2, target1)
            entropy_loss = - torch.mean(torch.log(torch.mean(output_t1,0)+1e-6))
            entropy_loss -= torch.mean(torch.log(torch.mean(output_t2,0)+1e-6))
            loss_dis = torch.mean(torch.abs(output_t1-output_t2))
            F_loss = loss1 + loss2 - eta*loss_dis  + 0.01 * entropy_loss
            F_loss.backward()
            optimizer_f.step()
            # Step C train genrator to minimize discrepancy
            for i in range(num_k):
                optimizer_g.zero_grad()
                output = G(data)
                output1 = F1(output)
                output2 = F2(output)

                output_s1 = output1[:batch_size,:]
                output_s2 = output2[:batch_size,:]
                output_t1 = output1[batch_size:,:]
                output_t2 = output2[batch_size:,:]

                loss1 = criterion(output_s1, target1)
                loss2 = criterion(output_s2, target1)
                output_t1 = F.softmax(output_t1)
                output_t2 = F.softmax(output_t2)
                loss_dis = torch.mean(torch.abs(output_t1-output_t2))
                entropy_loss = -torch.mean(torch.log(torch.mean(output_t1,0)+1e-6))
                entropy_loss -= torch.mean(torch.log(torch.mean(output_t2,0)+1e-6))

                loss_dis.backward()
                optimizer_g.step()
            if batch_idx % args.log_interval == 0: # number of print out: 3264/50 = 64

                # print('Train Ep: {} [{}/{} ({:.2f}%)]\tLoss1: {:.6f}\tLoss2: {:.6f}\t Dis: {:.6f} Entropy: {:.6f}'.format(
                #     ep, currentData, totalData,
                #     currentData / totalData, loss1.item(),loss2.item(),loss_dis.item(),entropy_loss.item()))
                print('Train Ep: {} [{}/{} ({:.0f}%)]\tLoss1: {:.6f}\tLoss2: {:.6f}\t Dis: {:.6f} Entropy: {:.6f}'.format(
                    ep, batch_idx * len(data), 70000,
                    100. * batch_idx * len(data) / 70000, loss1.item(),loss2.item(),loss_dis.item(),entropy_loss.item()))
            if batch_idx == 1 and ep >0:
                correct1, correct2, s = test(ep)
                correct1Array.append(correct1)
                correct2Array.append(correct2)
                size = s
                G.train() # what does this train mean?
                F1.train()
                F2.train()
    np.savetxt('correct1Array'+str(size)+'.csv', correct1Array, delimiter = ",")
    np.savetxt('correct2Array'+str(size)+'.csv', correct2Array, delimiter = ",")


def test(epoch):
    G.eval()
    F1.eval()
    F2.eval()
    test_loss = 0
    correct = 0
    correct2 = 0
    size = 0

    for batch_idx, data in enumerate(dataset_test):
        if batch_idx*batch_size > 5000:
            break
        if args.cuda:
            data2  = data['T']
            target2 = data['T_label']

            data2, target2 = data2.cuda(), target2.cuda()
        data1, target1 = Variable(data2, volatile=True), Variable(target2)
        output = G(data1)
        output1 = F1(output)
        output2 = F2(output)
        test_loss += F.nll_loss(output1, target1).item()
        pred = output1.data.max(1)[1] # get the index of the max log-probability
        correct += pred.eq(target1.data).cpu().sum()
        pred = output2.data.max(1)[1] # get the index of the max log-probability
        k = target1.data.size()[0]
        correct2 += pred.eq(target1.data).cpu().sum()

        size += k
    test_loss = test_loss
    test_loss /= len(test_loader) # loss function already averages over batch size
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%) ({:.0f}%)\n'.format(
        test_loss, correct, size,
        100. * correct / size,100.*correct2/size))
    #if 100. * correct / size > 67 or 100. * correct2 / size > 67:
    value = max(100. * correct / size,100. * correct2 / size)
    if value > 60:
        torch.save(F1.state_dict(), save_path+'_'+args.resnet+'_'+str(value)+'_'+'F1.pth')
        torch.save(F2.state_dict(), save_path+'_'+args.resnet+'_'+str(value)+'_'+'F2.pth')
        torch.save(G.state_dict(), save_path+'_'+args.resnet+'_'+str(value)+'_'+'G.pth')
    return correct, correct2, size


#for epoch in range(1, args.epochs + 1):
train(args.epochs+1)
