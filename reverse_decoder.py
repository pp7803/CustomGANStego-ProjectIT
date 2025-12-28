import torch
from torch import nn


class ReverseDecoder(nn.Module):
    """
    The ReverseDecoder module takes a steganographic image and attempts to 
    reconstruct the original cover image (Reverse Hiding).
    
    This enables:
    - Lossless recovery of original image
    - Reversible steganography
    - Higher security (can remove traces)
    
    Input: (N, 3, H, W) - Stego image
    Output: (N, 3, H, W) - Recovered cover image
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
        Architecture similar to BasicDecoder but output is RGB image (3 channels)
        Uses residual connections for better gradient flow
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
            self._conv2d(self.hidden_size, 3),  # Output RGB
            nn.Tanh()  # Output range [-1, 1] to match normalized images
        )

        return self.conv1, self.conv2, self.conv3, self.conv4, self.conv5

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        self._models = self._build_models()

    def forward(self, stego_image):
        """
        Forward pass with residual connection
        
        Args:
            stego_image: Steganographic image (N, 3, H, W)
            
        Returns:
            recovered_cover: Reconstructed cover image (N, 3, H, W)
        """
        x = self._models[0](stego_image)
        x_1 = self._models[1](x)
        x_2 = self._models[2](x_1)
        x_3 = self._models[3](x_2)
        x_4 = self._models[4](x_3)
        
        # Residual connection: stego + delta = cover
        # This helps network learn only the difference
        recovered_cover = stego_image + x_4
        
        # Clamp to valid range [-1, 1]
        recovered_cover = torch.clamp(recovered_cover, -1.0, 1.0)
        
        return recovered_cover
