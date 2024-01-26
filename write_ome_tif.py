"""

Writing ome-tif file from DSA item

HuBMAP's fav format. Have to add each annotation layer as a labeled mask the same size as the WSI (yikes)

source of ome-tiff writing:
https://forum.image.sc/t/writing-contiguous-ome-tiff-with-tifffile/70613/2

"""

import os
import sys

import tifffile
import numpy as np

import girder_client
import large_image

import ome_types as ot

from skimage.draw import polygon


class OMETIFFMaker:
    def __init__(self, include_image: bool):

        self.include_image = include_image
        self.annotation_masks = []
        self.annotation_names = []
        self.n_frames = 0
        self.image = None

    def gen_annotation_masks(self,annotations: list | dict):

        # This is for annotations in Histomics JSON format.
        if type(annotations)==dict:
            annotations = [annotations]

        # Iterating through annotation layers
        for ann_idx,ann in annotations:
            # Creating new mask that is the same size as the WSI (yikes)
            ann_mask = np.zeros((self.image_Y,self.image_X))

            self.annotation_names.append(ann['annotation']['name'])

            # Iterating through elements in current annotation layer
            for el_idx, el in ann['annotation']['elements']:

                if el['type']=='polyline':
                    # Pulling out points (dropping z-axis)
                    coords = [[i[0],i[1]] for i in el['points']]

                    # Points are stored in X, Y, Z order in large-image annotations
                    x_coords = [i[0] for i in coords]
                    y_coords = [i[1] for i in coords]

                    # Getting bounding box of points (minx, miny, maxx, maxy)
                    minx = int(np.min(x_coords))
                    miny = int(np.min(y_coords))
                    maxx = int(np.max(x_coords))
                    maxy = int(np.max(y_coords))

                    el_height = int(maxy-miny)
                    el_width = int(maxx-minx)

                    # Scaled coordinates (making minimal polygons necessary)
                    scaled_coords = [[i[0]-minx,i[1]-miny] for i in coords]

                    # Creating polygon (inputs are rows, columns or y, x so have to reverse order)
                    el_rows, el_cols = polygon(
                        r = [int(i[1]) for i in scaled_coords],
                        c = [int(i[0]) for i in scaled_coords]
                    )

                    # Label mask assigns the element index to the locations of the polygon
                    el_poly_mask = np.zeros((el_height,el_width))
                    el_poly_mask[el_rows,el_cols] += (el_idx+1)

                    # Adding element mask to full layer mask
                    ann_mask[miny:maxy,minx:maxx] += el_poly_mask
                
                else:
                    print(f'Skipping annotation: {ann_idx}')
                    continue
                
            self.annotation_masks.append(ann_mask)
            self.n_frames += 1

        if self.include_image:
            # Assemble all frames
            self.all_frames = np.concatenate((self.image[None,:,:,:],np.array(self.annotation_masks)[None,:,:,None]))
        else:
            self.all_frames = self.annotation_masks

    def read_image(self,image_path:str):

        # Reads image from file path
        self.image_object = large_image.open(image_path)
        self.image_metadata = self.image.getMetadata()
        self.image_X = self.image_metadata['sizeX']
        self.image_Y = self.image_metadata['sizeY']
        self.image_name = image_path.split(os.sep)[-1]
        self.image_path = image_path

        # If reading the image
        if self.include_image:
            self.image = self.image_object.getRegion(
                region = {
                    'left':0,
                    'top':0,
                    'right':self.image_X,
                    'bottom':self.image_Y
                },
                format = large_image.constants.TILE_FORMAT_NUMPY
            )

            self.n_frames += np.shape(self.image)[0]

    def frame_generator(self):

        for frame in self.all_frames:
            yield frame

    def write_tiff(self,save_path = None):

        if save_path is None:

            start_ext = self.image_name.split('.')[-1]
            save_path = self.image_path.replace(self.image_name.replace(start_ext,'.ome.tiff'))
        
        tifffile.imwrite(
            save_path,
            self.frame_generator(),
            shape = (self.n_frames, self.image_Y, self.image_X),
            dtype = np.float64,
            metadata={'axes':'ZYX'}
        )

        # Creating ome.xml file
        tif_file = ot.from_tiff(save_path)
        for idx,channel in enumerate(tif_file.images[0].pixels.channels):
            channel.name = self.annotation_names[idx]

        xml_save_path = save_path.replace('.tiff','.xml')
        xml_data = ot.to_xml(tif_file)
        xml_data = xml_data.replace('<pixels','<Pixels PhysicalSizeXUnit="\u03BCm" PhysicalSizeYUnit="\u03BCm"')

        with open(xml_save_path,'wt+') as fh:
            fh.write(xml_data)
















