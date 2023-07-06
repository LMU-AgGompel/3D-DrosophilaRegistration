#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function(s) to transform 3D images in point clouds and viceversa.

@author: ceolin
"""

import sys
import numpy as np
import open3d as o3d
from skimage import morphology
from scipy import ndimage


def pcd_to_image(pcd, pcd_values, image_shape):
    """
    Parameters
    ----------
    pcd : open3d pcd.
        an open3d point cloud object.
    pcd_values : 1D numpy array
        brightness of the point cloud points.
    image_shape : list
        shape of the final 3D numpy array.

    Returns
    -------
    image : 3 dimensional numpy array
        grayscale 3D image.

    This function converts a point cloud to a 3D image. If more than one point
    falls in the same voxel their britghness is averaged. Holes in the final
    image are filled with the median values of neighbouring voxels.
    """
    pcd_array = np.asarray(pcd.points).T.astype(int)
    image = np.zeros(image_shape)
    points_count = np.zeros(image_shape)
    assert len(pcd_values) == pcd_array.shape[-1],\
        " ERROR: the number of points in the pcd object doesn't match the number of britghness values."

    index_error_flag = False

    for i in range(pcd_array.shape[-1]):
        pos = tuple(pcd_array[..., i])
        try:
            image[pos] += pcd_values[i]
            points_count[pos] += 1
        except IndexError:
            index_error_flag = True

    if index_error_flag:
        print("Warning: The point cloud does not fit the image shape. Part of the object will be cropped.",  file=sys.stderr)

    # average the birghtness in voxels containing multiple points:
    image[points_count > 1] = image[points_count > 1] / \
        points_count[points_count > 1]

    # fill holes with the median of neighbouring voxels:
    mask = morphology.closing(image > 0, morphology.ball(2))
    image_median = ndimage.median_filter(image, size=3)
    image[points_count == 0] = image_median[points_count == 0]
    image = image*mask
    return image


def image_to_pcd(image_3d, upscale=None):
    """
    Convert a 3D image into a point cloud and an array of brightness values of each point.

    Parameters
    ----------
    image_3d : numpy.ndarray
        The input (sparse) 3D image.

    upscale : float or None, optional
        Upscaling factor for the image. If provided, the image will be zoomed by the given factor.
        Default is None.

    Returns
    -------
    pcd : open3d.geometry.PointCloud
        An open3d point cloud object.

    pcd_values : numpy.ndarray
        1D array containing the brightness values of the point cloud points.

    Notes
    -----
    If `upscale` is provided, the `image_3d` will be zoomed by the specified factor before converting
    it into a point cloud. The zoomed image will be used to generate the point cloud and brightness
    values.

    If `upscale` is not provided, the original `image_3d` will be used directly to generate the point
    cloud and brightness values.

    The point cloud coordinates are computed from the non-zero elements of `image_3d` using the
    `np.nonzero` function. The resulting point cloud is stored in an `open3d.geometry.PointCloud`
    object.
    """

    if upscale:
        upscaled_image = ndimage.zoom(image_3d, upscale)
        indexes = np.nonzero(upscaled_image > 0)
        pcd_points = np.array(indexes).T/upscale
        pcd_values = upscaled_image[indexes]
    else:
        indexes = np.nonzero(image_3d > 0)
        pcd_points = np.array(indexes).T
        pcd_values = image_3d[indexes]

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pcd_points)

    return pcd, pcd_values
