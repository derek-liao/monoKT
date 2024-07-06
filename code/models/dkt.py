import os

import numpy as np
import torch
import torch.nn as nn


from torch.nn import Module, Embedding, LSTM, Linear, Dropout
from torch.nn.functional import one_hot

class DKT(Module):
    def __init__(self, num_skills, embedding_size=64, dropout=0.1):
        super().__init__()
        self.num_skills = num_skills
        self.emb_size = embedding_size
        self.hidden_size = embedding_size
        self.interaction_emb = Embedding(self.num_skills * 2, self.emb_size)

        # self.lstm_layer = RNN(self.emb_size, self.hidden_size, batch_first=True)
        self.lstm_layer = LSTM(self.emb_size, self.hidden_size, batch_first=True)
        self.dropout_layer = Dropout(dropout)
        self.out_layer = Linear(self.hidden_size, self.num_skills)
        self.loss_fn = nn.BCELoss(reduction="mean")
        

    def forward(self, feed_dict):
        q = feed_dict['skills']
        r = feed_dict['responses']
        masked_r = r * (r > -1).long()
        q_input = q[:, :-1]
        r_input = masked_r[:, :-1]
        q_shft = q[:, 1:]
        r_shft = r[:, 1:]
        x = q_input + self.num_skills * r_input
        xemb = self.interaction_emb(x)
        h, _ = self.lstm_layer(xemb)
        h = self.dropout_layer(h)
        y = self.out_layer(h)
        y = torch.sigmoid(y)
        y = (y * one_hot(q_shft.long(), self.num_skills)).sum(-1)
        
        out_dict = {
            "pred": y,
            "true": r_shft.float(),
        }
        return out_dict

    def loss(self, feed_dict, out_dict):
        pred = out_dict["pred"].flatten()
        true = out_dict["true"].flatten()
        mask = true > -1
        loss = self.loss_fn(pred[mask], true[mask])
        return loss, len(pred[mask]), true[mask].sum().item()