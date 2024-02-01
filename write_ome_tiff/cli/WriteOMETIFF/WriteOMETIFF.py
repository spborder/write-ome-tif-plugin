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
    
    # Printing contents of current directory, maybe the image gets copied over?
    print(f'Contents of current directory: {os.listdir(os.getcwd())}')

    girderApiUrl = args.girderApiUrl
    girderToken = args.girderToken

    gc = girder_client.GirderClient(apiUrl=girderApiUrl)
    gc.setToken(girderToken)

    image_id = gc.get(f'/file/{image_file_id}')['itemId']

    item_info = gc.get(f'/item/{image_id}')
    folder_id = item_info['folderId']
    image_name = item_info['name']
    annotations = gc.get(f'/annotation/item/{image_id}')

    image_metadata = gc.get(f'/item/{image_id}/tiles')

    # Copying image over to the current directory
    #gc.downloadFile(
    #    fileId = image_file_id,
    #    path = f'/{image_name}'
    #)

    #print('Is the image here??')
    #print(os.listdir('/'))

    ome_tiff_maker = OMETIFFMaker(include_image = False)
    ome_tiff_maker.get_image_data(image_metadata,item_info)
    ome_tiff_maker.gen_annotation_masks(annotations)

    image_save_path, xml_save_path = ome_tiff_maker.write_tiff()

    # Writing file back to original folder with updated name
    image_folder_id = gc.get(f'/item/{image_id}')['folderId']
    uploaded_image = gc.uploadFileToFolder(image_folder_id,image_save_path)
    uploaded_xml = gc.uploadFileToFolder(image_folder_id,xml_save_path)

if __name__=='__main__':
    main(CLIArgumentParser().parse_args())

