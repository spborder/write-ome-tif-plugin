"""

Taking plugin arguments and generating output

"""

import os
import sys

import girder_client

from ctk_cli import CLIArgumentParser

sys.path.append('..')
from cli.write_ome_tif import OMETIFFMaker

def main(args):

    image_file_id = args.input_image
    # This is the file id, not the item which has annotations. So have to get the associated item id

    girderApiUrl = args.girderApiUrl
    girderToken = args.girderToken

    gc = girder_client.GirderClient(apiUrl=girderApiUrl)
    gc.setToken(girderToken)

    image_id = gc.get(f'/resource/{image_file_id}?token={girderToken}')['itemId']

    annotations = gc.get(f'/annotation/item/{image_id}')

    ome_tiff_maker = OMETIFFMaker(include_image = False)
    ome_tiff_maker.gen_annotation_masks(annotations)
    ome_tiff_maker.read_image(args.input_image)

    ome_tiff_maker.write_tiff()

if __name__=='__main__':
    main(CLIArgumentParser().parse_args())

