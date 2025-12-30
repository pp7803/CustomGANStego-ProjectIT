import torch
from torch import nn


class ReverseDecoder(nn.Module):
    """
    Module ReverseDecoder nhận ảnh stego và cố gắng
    tái tạo lại ảnh cover gốc (Reverse Hiding).
    
    Điều này cho phép:
    - Khôi phục ảnh gốc không mất mát
    - Steganography có thể đảo ngược
    - Bảo mật cao hơn (có thể xóa dấu vết)
    
    Đầu vào: (N, 3, H, W) - Ảnh stego
    Đầu ra: (N, 3, H, W) - Ảnh cover đã khôi phục
    """

    def _conv2d(self, in_channels, out_channels):
        return nn.Conv2d(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=3,
            padding=1
        )

    def _build_models(self):
        """
        Kiến trúc tương tự như BasicDecoder nhưng đầu ra là ảnh RGB (3 kênh)
        Sử dụng kết nối residual để cải thiện luồng gradient
        """
        self.conv1 = nn.Sequential(
            self._conv2d(3, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv2 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv3 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv4 = nn.Sequential(
            self._conv2d(self.hidden_size, self.hidden_size),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm2d(self.hidden_size),
        )
        self.conv5 = nn.Sequential(
            self._conv2d(self.hidden_size, 3),
            nn.Tanh()
        )

        return self.conv1, self.conv2, self.conv3, self.conv4, self.conv5

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self._models = self._build_models()

    def forward(self, stego_image):
        """
        Forward pass với kết nối residual
        
        Args:
            stego_image: Ảnh stego (N, 3, H, W)
            
        Returns:
            recovered_cover: Ảnh cover đã tái tạo (N, 3, H, W)
        """
        x = self._models[0](stego_image)
        x_1 = self._models[1](x)
        x_2 = self._models[2](x_1)
        x_3 = self._models[3](x_2)
        x_4 = self._models[4](x_3)
        
        recovered_cover = stego_image + x_4
        
        recovered_cover = torch.clamp(recovered_cover, -1.0, 1.0)
        
        return recovered_cover
