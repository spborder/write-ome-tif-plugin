"""

Taking plugin arguments and generating output

"""

import os
import sys

import girder_client

from ctk_cli import CLIArgumentParser


sys.path.append('..')
from write_ome_tif import OMETIFFMaker

def main(args):

    image_id = args.input_image.split(os.sep)[-1]
    girderApiUrl = args.girderApiUrl
    girderToken = args.girderToken

    gc = girder_client.GirderClient(apiUrl=girderApiUrl)
    gc.setToken(girderToken)

    annotations = gc.get(f'/annotation/item/{image_id}')

    ome_tiff_maker = OMETIFFMaker(include_image = False)
    ome_tiff_maker.gen_annotation_masks(annotations)
    ome_tiff_maker.read_image(args.input_image)

    ome_tiff_maker.write_tiff()

if __name__=='__main__':
    main(CLIArgumentParser().parse_args())

