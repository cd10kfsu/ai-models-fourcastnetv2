import torch
from torch import nn


class ComplexReLU(nn.Module):
    def __init__(self, negative_slope=0.0, mode="cartesian", bias_shape=None):
        super(ComplexReLU, self).__init__()

        # store parameters
        self.mode = mode
        if self.mode in ["modulus", "halfplane"]:
            if bias_shape is not None:
                self.bias = nn.Parameter(torch.zeros(bias_shape, dtype=torch.float32))
            else:
                self.bias = nn.Parameter(torch.zeros((1), dtype=torch.float32))
        else:
            bias = torch.zeros((1), dtype=torch.float32)
            self.register_buffer("bias", bias)

        self.negative_slope = negative_slope
        self.act = nn.LeakyReLU(negative_slope=negative_slope)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        if self.mode == "cartesian":
            zr = torch.view_as_real(z)
            za = self.act(zr)
            out = torch.view_as_complex(za)
        elif self.mode == "modulus":
            zabs = torch.sqrt(torch.square(z.real) + torch.square(z.imag))
            out = self.act(zabs + self.bias) * torch.exp(1.0j * z.angle())
        elif self.mode == "halfplane":
            # bias is an angle parameter in this case
            modified_angle = torch.angle(z) - self.bias
            condition = torch.logical_and(
                (0.0 <= modified_angle), (modified_angle < torch.pi / 2.0)
            )
            out = torch.where(condition, z, self.negative_slope * z)
        elif self.mode == "real":
            zr = torch.view_as_real(z)
            outr = zr.clone()
            outr[..., 0] = self.act(zr[..., 0])
            out = torch.view_as_complex(outr)
        else:
            # identity
            out = z

        return out


class ComplexActivation(nn.Module):
    def __init__(self, activation, mode="cartesian", bias_shape=None):
        super(ComplexActivation, self).__init__()

        # store parameters
        self.mode = mode
        if self.mode == "modulus":
            if bias_shape is not None:
                self.bias = nn.Parameter(torch.zeros(bias_shape, dtype=torch.float32))
            else:
                self.bias = nn.Parameter(torch.zeros((1), dtype=torch.float32))
        else:
            bias = torch.zeros((1), dtype=torch.float32)
            self.register_buffer("bias", bias)

        # real valued activation
        self.act = activation

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        if self.mode == "cartesian":
            zr = torch.view_as_real(z)
            za = self.act(zr)
            out = torch.view_as_complex(za)
        elif self.mode == "modulus":
            zabs = torch.sqrt(torch.square(z.real) + torch.square(z.imag))
            out = self.act(zabs + self.bias) * torch.exp(1.0j * z.angle())
        else:
            # identity
            out = z

        return out
