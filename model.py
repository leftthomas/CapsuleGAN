import torch.nn.functional as F
from torch import nn

from capsulelayer import CapsuleConv2d, CapsuleLinear

config = {
    # each ceil form: out_channels, out_length, (D)[means do CapsuleConv2d at stride=2]
    'MNIST': ['64-8', '64-8D', '128-16', '128-16D'],
    'FashionMNIST': ['64-8', '64-8D', '128-16', '128-16D'],
    'SVHN': ['64-8', '64-8D', '128-16', '128-16D'],
    'CIFAR10': ['64-8', '64-8D', '128-16', '128-16D'],
    'CIFAR100': ['64-8', '64-8D', '128-16', '128-16D'],
    'STL10': ['64-8', '64-8D', '128-16', '128-16D'],
}


class SquashCapsuleNet(nn.Module):
    def __init__(self, in_channels, num_class, data_type):
        super(SquashCapsuleNet, self).__init__()
        self.features = self.make_layers(in_channels, config[data_type])
        self.classifier = CapsuleLinear(in_capsules=6 * 6 * 128 // 16, out_capsules=num_class, in_length=16,
                                        out_length=16)

    def forward(self, x):
        out = self.features(x)

        out = out.view(*out.size()[:2], -1)
        out = out.transpose(-1, -2)
        out = out.contiguous().view(out.size(0), -1, 16)

        out = self.classifier(out)
        classes = (out ** 2).sum(dim=-1) ** 0.5
        classes = F.softmax(classes, dim=-1)
        return classes

    @staticmethod
    def make_layers(in_channels, cfg):
        layers = []
        layers += [nn.Conv2d(in_channels, 64, kernel_size=9), nn.ReLU(inplace=True)]
        in_length = 8
        for x in cfg:
            out_channels, out_length = x.split('-')
            out_channels = int(out_channels)
            if out_length.endswith('D'):
                out_length = int(out_length.replace('D', ''))
                layers += [
                    CapsuleConv2d(in_channels, out_channels, kernel_size=3, in_length=in_length, out_length=out_length,
                                  padding=1, stride=2)]
            else:
                out_length = int(out_length)
                layers += [
                    CapsuleConv2d(in_channels, out_channels, kernel_size=3, in_length=in_length, out_length=out_length,
                                  padding=1)]
            in_channels = out_channels
            in_length = out_length
        return nn.Sequential(*layers)


if __name__ == "__main__":
    d = SquashCapsuleNet(in_channels=1, num_class=10, data_type='MNIST')
    print(d)
