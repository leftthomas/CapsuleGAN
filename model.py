import torch
from torch import nn

config = {
    'VGG16': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 'M', 512, 512, 512, 'M', 512, 512, 512, 'M'],
    'VGG19': [64, 64, 'M', 128, 128, 'M', 256, 256, 256, 256, 'M', 512, 512, 512, 512, 'M', 512, 512, 512, 512, 'M'],
}


def squash(tensor):
    squared_norm = (tensor ** 2).sum(dim=1, keepdim=True)
    scale = squared_norm / (1 + squared_norm)
    return scale * tensor / torch.sqrt(squared_norm)


class SquashLayer(nn.Module):
    def __init__(self, chunks):
        super(SquashLayer, self).__init__()
        self.chunks = chunks

    def forward(self, x):
        x = torch.cat([squash(capsule) for capsule in torch.chunk(x, chunks=self.chunks, dim=1)], dim=1)
        return x


class ResBlock(nn.Module):
    def __init__(self, in_channels, out_channels, is_downsample):
        super(ResBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn = nn.BatchNorm2d(num_features=out_channels)
        self.relu = nn.ReLU(inplace=True)
        if is_downsample:
            self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=2, padding=1)
        else:
            self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.bn(x)
        x = self.relu(x)
        return x


class SquashCapsuleNet(nn.Module):
    def __init__(self, in_channels, num_class):
        super(SquashCapsuleNet, self).__init__()
        # self.conv = nn.Conv2d(in_channels, 64, kernel_size=5, stride=1, padding=2)
        self.rb1 = ResBlock(in_channels, 64, True)
        self.rb2 = ResBlock(64, 128, True)
        self.rb3 = ResBlock(128, 256, False)
        self.rb4 = ResBlock(256, 256, True)
        self.rb5 = ResBlock(256, 512, False)
        self.rb6 = ResBlock(512, 512, True)
        self.rb7 = ResBlock(512, 512, False)
        self.rb8 = ResBlock(512, 512, True)
        self.classifier = nn.Linear(512, num_class)

    def forward(self, x):
        x = self.rb1(x)
        x = self.rb2(x)
        x = self.rb3(x)
        x = self.rb4(x)
        x = self.rb5(x)
        x = self.rb6(x)
        x = self.rb7(x)
        x = self.rb8(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x


# class SquashCapsuleNet(nn.Module):
#     def __init__(self, in_channels, num_class, vgg_name):
#         super(SquashCapsuleNet, self).__init__()
#         self.features = self.make_layers(in_channels, config[vgg_name])
#         self.classifier = nn.Linear(512, num_class)
#
#     def forward(self, x):
#         out = self.features(x)
#         out = out.view(out.size(0), -1)
#         out = self.classifier(out)
#         return out
#
#     @staticmethod
#     def make_layers(in_channels, cfg):
#         layers = []
#         for x in cfg:
#             if x == 'M':
#                 layers += [nn.MaxPool2d(kernel_size=2, stride=2)]
#             else:
#                 layers += [nn.Conv2d(in_channels, x, kernel_size=3, padding=1),
#                            nn.BatchNorm2d(x),
#                            nn.ReLU(inplace=True)]
#                 in_channels = x
#         layers += [nn.AdaptiveAvgPool2d(1)]
#         return nn.Sequential(*layers)


if __name__ == "__main__":
    a = torch.FloatTensor([[0, 1, 2], [3, 4, 5]])
    b = squash(a)
    print(b)
    d = SquashCapsuleNet(in_channels=1, num_class=10)
    print(d)
