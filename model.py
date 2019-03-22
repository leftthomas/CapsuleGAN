import torch
from capsule_layer import CapsuleLinear
from torch import nn
from torch_geometric.nn import GCNConv
from torch_geometric.utils import remove_self_loops

from utils import global_sort_pool


class Model(nn.Module):
    def __init__(self, num_features, num_classes, num_iterations=3):
        super(Model, self).__init__()

        self.gcn1 = GCNConv(num_features, 32)
        self.gcn2 = GCNConv(32, 32)
        self.gcn3 = GCNConv(32, 32)
        self.classifier_1 = CapsuleLinear(out_capsules=16, in_length=96, out_length=32, in_capsules=50,
                                          share_weight=False, num_iterations=num_iterations)
        self.classifier_2 = CapsuleLinear(out_capsules=num_classes, in_length=32, out_length=16, in_capsules=16,
                                          share_weight=False, num_iterations=num_iterations)

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch
        edge_index, _ = remove_self_loops(edge_index)

        x_1 = torch.tanh(self.gcn1(x, edge_index))
        x_2 = torch.tanh(self.gcn2(x_1, edge_index))
        x_3 = torch.tanh(self.gcn3(x_2, edge_index))
        x = torch.cat([x_1, x_2, x_3], dim=-1)
        out = self.classifier_1(global_sort_pool(x, batch, k=50))
        out = self.classifier_2(out)
        classes = out.norm(dim=-1)

        return classes
