import torch.optim as optim
from model import *
import util_pre

class trainer():
    def __init__(self, scaler, in_dim, seq_length, num_nodes, nhid, dropout,
                 lrate, wdecay, device, supports, adj_mx,
                 gcn_bool = True, 
                 addaptadj = True,aptinit = None,):
        self.model = gwnet(device,
                           num_nodes,
                           dropout,
                           supports=supports,
                           gcn_bool=gcn_bool,
                           addaptadj=addaptadj,
                           aptinit=aptinit,
                           in_dim=in_dim,
                           out_dim=seq_length,
                           residual_channels=nhid,
                           dilation_channels=nhid,
                           skip_channels=nhid * 8,
                           end_channels=nhid * 16,
                           adj_mx=adj_mx)
        
        self.device = device
        self.model.to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lrate, weight_decay=wdecay)
        self.loss = util_pre.masked_mae
        self.wloss = util_pre.weighted_mae
        self.scaler = scaler
        self.clip = 5

    def train(self, input, real_val, events):
        self.model.train()
        self.optimizer.zero_grad()
        output,seg_emb = self.model(input, events)
        output = output.transpose(1, 3)
        real = torch.unsqueeze(real_val, dim=1)
        predict = self.scaler.inverse_transform(output)
        loss = self.loss(predict, real, 0.0)
        # loss = self.wloss(predict, real, weight)
        mape = util_pre.masked_mape(predict, real, 0.0).item()
        # mape = util.weighted_mape(predict, real, weight).item()
        rmse = util_pre.masked_rmse(predict, real, 0.0).item()
        loss.backward()

        if self.clip is not None:
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip)
        self.optimizer.step()
       
        
        return loss.item(), mape, rmse

    def eval(self, input, real_val, events):
        self.model.eval()
        output,seg_emb = self.model(input, events)
        output = output.transpose(1, 3)
        real = torch.unsqueeze(real_val, dim=1)
        predict = self.scaler.inverse_transform(output)
        # loss = self.wloss(predict, real, weight)
        # mape = util.weighted_mape(predict, real, weight).item()
        loss = self.loss(predict, real, 0.0)
        mape = util_pre.masked_mape(predict, real, 0.0).item()
        rmse = util_pre.masked_rmse(predict, real, 0.0).item()
        return loss.item(), mape, rmse
