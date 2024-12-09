import argparse
import torch
import numpy as np
from torchvision import transforms
from osgeo import gdal
from PIL import Image

import torch.nn as nn
from torchvision import transforms, models

from utils import s2_to_arr, gray_to_arr

# Define the script arguments
parser = argparse.ArgumentParser(description="Rural road detection via Sentinel-2 imagery.")
parser.add_argument("--image", required=True, help="Input image path.")
parser.add_argument("--model", required=True, help="Trained model weights.")
parser.add_argument("--output", required=True, help="Output path.")
args = parser.parse_args()

# set utils
def gray_to_arr(path):
    '''Open graysclae image and return as np.array'''
    raster = gdal.Open(path)
    arr = raster.GetRasterBand(1).ReadAsArray()
    del raster
    return arr

def s2_to_arr(path, bands=['red', 'green', 'blue']):
    '''
    Open Sentinel-2 imagery and return as np.array with specified bands.
    Bands: red, green, blue, nir, swir1, swir2, edge1, edge2, edge3 and edge4.
    Output array has shape (height, width, n_channels)
    '''
    bands_dict = {'blue': 2, 'green': 3, 'red': 4, 'edge1': 5, 'edge2': 6, 'edge3': 7,\
             'nir': 8, 'edge4': 9, 'swir1': 12, 'swir2': 13}

    raster = gdal.Open(path)

    arr = np.dstack(
        [raster.GetRasterBand(bands_dict[band]).ReadAsArray() for band in bands]
    )

    del raster

    return arr

def get_model_and_load_weights(model_path):
    model = ResNetUNet(n_class=1)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    return model


def convrelu(in_channels, out_channels, kernel, padding):
    return nn.Sequential(
        nn.Conv2d(in_channels, out_channels, kernel, padding=padding),
        nn.ReLU(inplace=True),
    )

def process_in_tiles(image, model):
    height, width, channels = image.shape
    padded_height = ((height + 128 - 1) // 128) * 128
    padded_width = ((width + 128 - 1) // 128) * 128

    padded_image = np.zeros((padded_height, padded_width, channels), dtype=image.dtype)
    padded_image[:height, :width, :] = image

    output_mask = np.zeros((padded_height, padded_width))

    transform = transforms.Compose([
        transforms.ToTensor(),
    ])

    for y in range(0, padded_height, 128):
        for x in range(0, padded_width, 128):
            tile = padded_image[y:y + 128, x:x + 128, :]
            tile_tensor = transform(tile).unsqueeze(0)
            with torch.no_grad():
                mask = model(tile_tensor)
                mask = torch.sigmoid(mask).squeeze().cpu().numpy()

            output_mask[y:y + 128, x:x + 128] = mask

    return output_mask[:height, :width]


# model implementation
class ResNetUNet(nn.Module):
    def __init__(self, n_class):
        super().__init__()

        self.base_model = models.resnet18(pretrained=True)
        self.base_layers = list(self.base_model.children())

        self.layer0 = nn.Sequential(*self.base_layers[:3]) # size=(N, 64, x.H/2, x.W/2)
        self.layer0_1x1 = convrelu(64, 64, 1, 0)
        self.layer1 = nn.Sequential(*self.base_layers[3:5]) # size=(N, 64, x.H/4, x.W/4)
        self.layer1_1x1 = convrelu(64, 64, 1, 0)
        self.layer2 = self.base_layers[5]  # size=(N, 128, x.H/8, x.W/8)
        self.layer2_1x1 = convrelu(128, 128, 1, 0)
        self.layer3 = self.base_layers[6]  # size=(N, 256, x.H/16, x.W/16)
        self.layer3_1x1 = convrelu(256, 256, 1, 0)
        self.layer4 = self.base_layers[7]  # size=(N, 512, x.H/32, x.W/32)
        self.layer4_1x1 = convrelu(512, 512, 1, 0)

        self.upsample = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)

        self.conv_up3 = convrelu(256 + 512, 512, 3, 1)
        self.conv_up2 = convrelu(128 + 512, 256, 3, 1)
        self.conv_up1 = convrelu(64 + 256, 256, 3, 1)
        self.conv_up0 = convrelu(64 + 256, 128, 3, 1)

        self.conv_original_size0 = convrelu(3, 64, 3, 1)
        self.conv_original_size1 = convrelu(64, 64, 3, 1)
        self.conv_original_size2 = convrelu(64 + 128, 64, 3, 1)

        self.conv_last = nn.Conv2d(64, n_class, 1)

    def forward(self, input):
        x_original = self.conv_original_size0(input)
        x_original = self.conv_original_size1(x_original)

        layer0 = self.layer0(input)
        layer1 = self.layer1(layer0)
        layer2 = self.layer2(layer1)
        layer3 = self.layer3(layer2)
        layer4 = self.layer4(layer3)

        layer4 = self.layer4_1x1(layer4)
        x = self.upsample(layer4)
        layer3 = self.layer3_1x1(layer3)
        x = torch.cat([x, layer3], dim=1)
        x = self.conv_up3(x)

        x = self.upsample(x)
        layer2 = self.layer2_1x1(layer2)
        x = torch.cat([x, layer2], dim=1)
        x = self.conv_up2(x)

        x = self.upsample(x)
        layer1 = self.layer1_1x1(layer1)
        x = torch.cat([x, layer1], dim=1)
        x = self.conv_up1(x)

        x = self.upsample(x)
        layer0 = self.layer0_1x1(layer0)
        x = torch.cat([x, layer0], dim=1)
        x = self.conv_up0(x)

        x = self.upsample(x)
        x = torch.cat([x, x_original], dim=1)
        x = self.conv_original_size2(x)

        out = self.conv_last(x)

        return out

# Main function
def main():
    print('Setting device...')
    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Using {device} device")
    
    # load image
    input_image = s2_to_arr(image_pth)

    # load model
    model = get_model_and_load_weights(weights_pth)

    # inference
    binary_mask = process_in_tiles(input_image, model)

    # save inference
    output_image = Image.fromarray(binary_mask, mode="L")
    output_image.save(output_pth)

if __name__ == "__main__":
    main()
